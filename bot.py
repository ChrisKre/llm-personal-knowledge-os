"""bot.py — Telegram bot: the primary input channel of the LLM-Personal-Knowledge-OS.

Receives:     text / voice / URL / photo / document / video
Forwards to:  Extractor → raw/events/ → main_workflow.run_ingest()
Sends:        a confirmation to the user

Start:        python bot.py
Requires:     TELEGRAM_BOT_TOKEN in .env
Optional:     ANTHROPIC_API_KEY (without a key → Ollama fallback)
              TELEGRAM_ALLOWED_USER_ID (empty → filter disabled, discovery mode)

User-facing replies are German for now (see ROADMAP: i18n).
"""

from __future__ import annotations

import asyncio
import functools
import logging
import os
from pathlib import Path

import anthropic
from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    filters,
)

# .env must be loaded before agents.config is imported (KOS_VAULT_ROOT).
load_dotenv(Path(__file__).resolve().parent / ".env")

from agents.config import VAULT_ROOT  # noqa: E402
from agents.extractors.extractor import Extractor  # noqa: E402
from main_workflow import run_ingest  # noqa: E402

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)
# httpx logs every request URL at INFO; Telegram URLs contain the bot token.
logging.getLogger("httpx").setLevel(logging.WARNING)

_api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
_client = anthropic.Anthropic(api_key=_api_key) if _api_key else None
_extractor = Extractor(wiki_root=VAULT_ROOT, anthropic_client=_client)
if _client is None:
    logger.info("No ANTHROPIC_API_KEY — Ollama fallback active.")

_allowed_user_raw = os.environ.get("TELEGRAM_ALLOWED_USER_ID", "").strip()
_ALLOWED_USER_ID: int | None = int(_allowed_user_raw) if _allowed_user_raw else None
if _ALLOWED_USER_ID is None:
    logger.warning(
        "TELEGRAM_ALLOWED_USER_ID not set — discovery mode (anyone may write). "
        "Read your user ID from the log, put it in .env, restart the bot."
    )
else:
    logger.info("Auth filter active for user ID %s.", _ALLOWED_USER_ID)


def _require_allowed_user(func):
    """Decorator — blocks handlers for other user IDs and logs the rejection.

    Discovery mode: if TELEGRAM_ALLOWED_USER_ID is empty, every incoming user ID
    is logged and let through; this is only meant for filling in .env initially.
    """
    @functools.wraps(func)
    async def wrapper(update: Update, context, *args, **kwargs):
        user = update.effective_user
        uid = user.id if user else None
        if _ALLOWED_USER_ID is None:
            logger.info("DISCOVERY — incoming user_id=%s (username=%s)", uid, user.username if user else None)
            return await func(update, context, *args, **kwargs)
        if uid != _ALLOWED_USER_ID:
            logger.warning("REJECTED user_id=%s (expected %s)", uid, _ALLOWED_USER_ID)
            return
        return await func(update, context, *args, **kwargs)
    return wrapper

# ---------------------------------------------------------------------------
# Bootstrap ConversationHandler states
# ---------------------------------------------------------------------------

BOOTSTRAP_Q = 0

BOOTSTRAP_QUESTIONS = [
    "1/10 — Was war dein peinlichster Moment in einer sozialen Situation? "
    "Erzähl so konkret wie möglich — wo warst du, wer war dabei?",
    "2/10 — Wann hast du zuletzt gelacht bis der Bauch wehtut? Was war der Auslöser?",
    "3/10 — Was ist das Dümmste das du je aus Versehen gemacht hast — und was ist dann passiert?",
    "4/10 — Wann warst du bei etwas erst komplett skeptisch — und am Ende begeistert oder überrascht?",
    "5/10 — Was war der unerwartetste Moment in deinem Leben in den letzten 2 Jahren?",
    "6/10 — Erzähl mir von einer Situation wo ein Fremder dich überrascht, bewegt oder überrumpelt hat.",
    "7/10 — Wann hat etwas entweder viel besser oder viel schlechter funktioniert als du gedacht hast?",
    "8/10 — Was kannst du, das die meisten Leute überrascht wenn sie es erfahren?",
    "9/10 — Was ist eine Überzeugung oder Meinung von dir die die meisten Menschen nicht teilen?",
    "10/10 — Was war das Erste das du dir selbst beigebracht hast — und wie hast du das gemacht?",
]


# ---------------------------------------------------------------------------
# I1: content confirmation (ENT-040)
# ---------------------------------------------------------------------------

def _format_write_confirmation(writes: list, graph_context: list) -> str:
    """Render the content confirmation after a successful wiki write."""
    first = writes[0]
    content = first.get("content", "")

    title = first["path"].split("/")[-1]
    for line in content.splitlines():
        if line.startswith("# ") and not line.startswith("## "):
            title = line[2:].strip()
            break

    score = None
    for line in content.splitlines():
        if "story_score:" in line:
            try:
                score = int(line.split(":", 1)[1].strip())
            except (ValueError, IndexError):
                pass
            break

    cluster = ""
    if graph_context:
        cluster = getattr(graph_context[0], "title", "") or ""

    lines = [f"✓ {title} gespeichert"]
    if score is not None:
        lines.append(f"  story_score {score} · {len(writes)} verknüpfte Facts")
    else:
        lines.append(f"  {len(writes)} Facts gespeichert")
    if cluster:
        lines.append(f'  "{cluster}" wächst.')

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# I6: friendlier errors (ENT-041)
# ---------------------------------------------------------------------------

_ERROR_KEYBOARD = InlineKeyboardMarkup([[
    InlineKeyboardButton("🔁 Nochmal versuchen", callback_data="retry"),
    InlineKeyboardButton("📋 Details",           callback_data="error_details"),
    InlineKeyboardButton("🙈 Egal, weiter",      callback_data="error_dismiss"),
]])


async def _reply_error_keyboard(update: Update, context, exc: Exception) -> None:
    """Friendlier error message with an inline keyboard (ENT-041)."""
    context.user_data["last_error"] = str(exc)
    await update.message.reply_text(
        "🤔 Hm — da ist was schiefgelaufen.\n"
        "Dein Input ist nicht verloren (steht in raw/events/).",
        reply_markup=_ERROR_KEYBOARD,
    )


async def handle_error_callback(update: Update, context) -> None:
    """Callback handler for the I6 error inline-keyboard buttons."""
    query = update.callback_query
    await query.answer()

    if query.data == "retry":
        raw_event = context.user_data.get("last_raw_event")
        if not raw_event:
            await query.message.reply_text("⚠️ Kein Event zum Wiederholen gespeichert.")
            return
        if context.user_data.get("retry_in_progress"):
            return  # idempotent: ignore a double tap
        context.user_data["retry_in_progress"] = True
        try:
            result = await asyncio.to_thread(run_ingest, raw_event)
            writes   = result.get("wiki_writes", [])
            graph_ctx = result.get("graph_context", [])
            if writes:
                await query.message.reply_text(_format_write_confirmation(writes, graph_ctx))
            else:
                await query.message.reply_text("✓ Verarbeitet (keine neuen Wiki-Seiten).")
        except Exception as exc:
            logger.error("Retry error: %s", exc, exc_info=True)
            await query.message.reply_text(f"🔁 Nochmal gescheitert: {str(exc)[:200]}")
        finally:
            context.user_data["retry_in_progress"] = False

    elif query.data == "error_details":
        err = context.user_data.get("last_error", "(kein Detail gespeichert)")
        await query.message.reply_text(f"📋 Fehlerdetail:\n{err[:200]}")

    # "error_dismiss": query.answer() was already called, nothing else to do


# ---------------------------------------------------------------------------
# Core helper
# ---------------------------------------------------------------------------

async def _process_and_reply(update: Update, context, content, user_hint: str = "") -> None:
    """Extract → save raw event → run workflow → reply with result."""
    try:
        extracted = _extractor.extract(content, user_hint=user_hint)
        extracted.save_event(VAULT_ROOT)
        raw_event = extracted.to_raw_event(VAULT_ROOT)
        context.user_data["last_raw_event"] = raw_event

        await update.message.reply_text("⏳ Verarbeite...")

        result = await asyncio.to_thread(run_ingest, raw_event)

        verdict   = result.get("supervisor_verdict", "accept")
        writes    = result.get("wiki_writes", [])
        msgs      = result.get("telegram_messages", [])
        graph_ctx = result.get("graph_context", [])

        if verdict == "reject":
            await update.message.reply_text("❌ Nicht verarbeitet — Supervisor hat abgelehnt.")
        elif writes:
            await update.message.reply_text(_format_write_confirmation(writes, graph_ctx))
        else:
            await update.message.reply_text("✓ Verarbeitet (keine neuen Wiki-Seiten).")

        for msg in msgs:
            await update.message.reply_text(msg)

    except Exception as exc:
        logger.error("Processing error: %s", exc, exc_info=True)
        await _reply_error_keyboard(update, context, exc)


async def _download_file(context, file_id: str, dest: Path) -> None:
    """Download a Telegram file to dest."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    tg_file = await context.bot.get_file(file_id)
    await tg_file.download_to_drive(str(dest))


# ---------------------------------------------------------------------------
# Normal message handlers
# ---------------------------------------------------------------------------

@_require_allowed_user
async def handle_text(update: Update, context) -> None:
    text = update.message.text or ""
    user_hint = ""
    # "#tag rest of message" → extract tag as hint
    if text.startswith("#"):
        parts = text.split(None, 1)
        user_hint = parts[0]
        text = parts[1] if len(parts) > 1 else ""
    if not text.strip():
        return
    await _process_and_reply(update, context, text, user_hint=user_hint)


@_require_allowed_user
async def handle_voice(update: Update, context) -> None:
    voice = update.message.voice
    dest = VAULT_ROOT / "raw" / "assets" / f"{voice.file_unique_id}.ogg"
    await _download_file(context, voice.file_id, dest)
    await _process_and_reply(update, context, dest, user_hint=update.message.caption or "")


@_require_allowed_user
async def handle_photo(update: Update, context) -> None:
    photo = update.message.photo[-1]   # largest resolution
    dest = VAULT_ROOT / "raw" / "assets" / f"{photo.file_unique_id}.jpg"
    await _download_file(context, photo.file_id, dest)
    await _process_and_reply(update, context, dest, user_hint=update.message.caption or "")


@_require_allowed_user
async def handle_document(update: Update, context) -> None:
    doc  = update.message.document
    name = doc.file_name or f"{doc.file_unique_id}.bin"
    dest = VAULT_ROOT / "raw" / "sources" / name
    await _download_file(context, doc.file_id, dest)
    await _process_and_reply(update, context, dest, user_hint=update.message.caption or "")


@_require_allowed_user
async def handle_video(update: Update, context) -> None:
    video = update.message.video or update.message.video_note
    dest  = VAULT_ROOT / "raw" / "assets" / f"{video.file_unique_id}.mp4"
    await _download_file(context, video.file_id, dest)
    await _process_and_reply(update, context, dest, user_hint=update.message.caption or "")


# ---------------------------------------------------------------------------
# Bootstrap ConversationHandler
# ---------------------------------------------------------------------------

@_require_allowed_user
async def bootstrap_start(update: Update, context) -> int:
    context.user_data["bootstrap_q"] = 0
    await update.message.reply_text(
        "Willkommen! Ich stelle dir 10 kurze Fragen um dein persönliches Wissens-Profil aufzubauen.\n"
        "Nimm dir Zeit, antworte so konkret wie möglich.\n"
        "Du kannst per Text oder Sprachnachricht antworten.\n\n"
        + BOOTSTRAP_QUESTIONS[0]
    )
    return BOOTSTRAP_Q


async def bootstrap_answer(update: Update, context) -> int:
    q_idx = context.user_data.get("bootstrap_q", 0)

    # Accept text or voice
    if update.message.voice:
        voice = update.message.voice
        dest = VAULT_ROOT / "raw" / "assets" / f"{voice.file_unique_id}.ogg"
        await _download_file(context, voice.file_id, dest)
        content = dest
    else:
        content = update.message.text or ""

    user_hint = f"bootstrap — direkt als PersonalFact verarbeiten. Frage {q_idx + 1}/10."
    try:
        extracted = _extractor.extract(content, user_hint=user_hint)
        raw_event = extracted.to_raw_event(VAULT_ROOT)
        raw_event["source_type"] = "bootstrap_interview"
        raw_event["question_index"] = q_idx + 1
        extracted.save_event(VAULT_ROOT)
        await asyncio.to_thread(run_ingest, raw_event)
    except Exception as exc:
        logger.error("Bootstrap error Q%d: %s", q_idx + 1, exc)

    q_idx += 1
    context.user_data["bootstrap_q"] = q_idx

    if q_idx >= len(BOOTSTRAP_QUESTIONS):
        await update.message.reply_text(
            "✓ Alles gespeichert. Dein Graph hat jetzt einen ersten Kern.\n"
            "Schick mir einfach eine Nachricht — ich bin bereit."
        )
        return ConversationHandler.END

    await update.message.reply_text("Danke! Weiter:\n\n" + BOOTSTRAP_QUESTIONS[q_idx])
    return BOOTSTRAP_Q


async def bootstrap_cancel(update: Update, context) -> int:
    await update.message.reply_text(
        "Bootstrap abgebrochen. Jederzeit mit /bootstrap neu starten."
    )
    return ConversationHandler.END


# ---------------------------------------------------------------------------
# Global error handler
# ---------------------------------------------------------------------------

async def _global_error_handler(update: object, context) -> None:
    """Catch exceptions from the Telegram library (network, API) that would otherwise kill polling."""
    logger.error("uncaught handler error: %s", context.error, exc_info=context.error)
    if isinstance(update, Update) and update.message is not None:
        try:
            await _reply_error_keyboard(update, context, context.error)
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    app   = Application.builder().token(token).build()

    bootstrap_handler = ConversationHandler(
        entry_points=[CommandHandler("bootstrap", bootstrap_start)],
        states={
            BOOTSTRAP_Q: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, bootstrap_answer),
                MessageHandler(filters.VOICE, bootstrap_answer),
            ],
        },
        fallbacks=[CommandHandler("cancel", bootstrap_cancel)],
    )

    app.add_handler(bootstrap_handler)
    app.add_handler(CallbackQueryHandler(handle_error_callback, pattern="^(retry|error_details|error_dismiss)$"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.VOICE,                   handle_voice))
    app.add_handler(MessageHandler(filters.PHOTO,                   handle_photo))
    app.add_handler(MessageHandler(filters.Document.ALL,            handle_document))
    app.add_handler(MessageHandler(filters.VIDEO | filters.VIDEO_NOTE, handle_video))

    app.add_error_handler(_global_error_handler)

    # Whisper warm-up: the ~460 MB download happens only on the very first start;
    # avoids a long silence on the user's first voice note (session 020: 703 s).
    from agents.extractors.audio_extractor import _get_model
    logger.info("Loading Whisper model (once at startup)...")
    _get_model()
    logger.info("Whisper model ready.")

    logger.info("Bot started — polling...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
