"""bot.py — Telegram Bot: primärer Input-Kanal des LLM-Personal-Knowledge-OS.

Empfängt: Text / Voice / URL / Foto / Dokument / Video
Leitet weiter an: Extractor → raw/events/ → main_workflow.run_ingest()
Sendet: Bestätigung an Nutzer

Start: python bot.py
Voraussetzung: TELEGRAM_BOT_TOKEN + ANTHROPIC_API_KEY in .env
"""

from __future__ import annotations

import asyncio
import logging
import os
from pathlib import Path

import anthropic
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    filters,
)

from agents.extractors.extractor import Extractor
from main_workflow import run_ingest

load_dotenv()
logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

WIKI_ROOT = Path(__file__).parent

_client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
_extractor = Extractor(wiki_root=WIKI_ROOT, anthropic_client=_client)

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
# Core helper
# ---------------------------------------------------------------------------

async def _process_and_reply(update: Update, content, user_hint: str = "") -> None:
    """Extract → save raw event → run workflow → reply with result."""
    try:
        extracted = _extractor.extract(content, user_hint=user_hint)
        extracted.save_event(WIKI_ROOT)
        raw_event = extracted.to_raw_event(WIKI_ROOT)

        await update.message.reply_text("⏳ Verarbeite...")

        result = await asyncio.to_thread(run_ingest, raw_event)

        verdict = result.get("supervisor_verdict", "accept")
        writes  = result.get("wiki_writes", [])
        msgs    = result.get("telegram_messages", [])

        if verdict == "reject":
            await update.message.reply_text("❌ Nicht verarbeitet — Supervisor hat abgelehnt.")
        elif writes:
            names = ", ".join(w["path"].split("/")[-1] for w in writes)
            await update.message.reply_text(f"✓ Gespeichert: {names}")
        else:
            await update.message.reply_text("✓ Verarbeitet (keine neuen Wiki-Seiten).")

        for msg in msgs:
            await update.message.reply_text(msg)

    except Exception as exc:
        logger.error("Processing error: %s", exc, exc_info=True)
        await update.message.reply_text(f"⚠️ Fehler: {exc}")


async def _download_file(context, file_id: str, dest: Path) -> None:
    """Download a Telegram file to dest."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    tg_file = await context.bot.get_file(file_id)
    await tg_file.download_to_drive(str(dest))


# ---------------------------------------------------------------------------
# Normal message handlers
# ---------------------------------------------------------------------------

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
    await _process_and_reply(update, text, user_hint=user_hint)


async def handle_voice(update: Update, context) -> None:
    voice = update.message.voice
    dest = WIKI_ROOT / "raw" / "assets" / f"{voice.file_unique_id}.ogg"
    await _download_file(context, voice.file_id, dest)
    await _process_and_reply(update, dest, user_hint=update.message.caption or "")


async def handle_photo(update: Update, context) -> None:
    photo = update.message.photo[-1]   # largest resolution
    dest = WIKI_ROOT / "raw" / "assets" / f"{photo.file_unique_id}.jpg"
    await _download_file(context, photo.file_id, dest)
    await _process_and_reply(update, dest, user_hint=update.message.caption or "")


async def handle_document(update: Update, context) -> None:
    doc  = update.message.document
    name = doc.file_name or f"{doc.file_unique_id}.bin"
    dest = WIKI_ROOT / "raw" / "sources" / name
    await _download_file(context, doc.file_id, dest)
    await _process_and_reply(update, dest, user_hint=update.message.caption or "")


async def handle_video(update: Update, context) -> None:
    video = update.message.video or update.message.video_note
    dest  = WIKI_ROOT / "raw" / "assets" / f"{video.file_unique_id}.mp4"
    await _download_file(context, video.file_id, dest)
    await _process_and_reply(update, dest, user_hint=update.message.caption or "")


# ---------------------------------------------------------------------------
# Bootstrap ConversationHandler
# ---------------------------------------------------------------------------

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
        dest = WIKI_ROOT / "raw" / "assets" / f"{voice.file_unique_id}.ogg"
        await _download_file(context, voice.file_id, dest)
        content = dest
    else:
        content = update.message.text or ""

    user_hint = f"bootstrap — direkt als PersonalFact verarbeiten. Frage {q_idx + 1}/10."
    try:
        extracted = _extractor.extract(content, user_hint=user_hint)
        raw_event = extracted.to_raw_event(WIKI_ROOT)
        raw_event["source_type"] = "bootstrap_interview"
        raw_event["question_index"] = q_idx + 1
        extracted.save_event(WIKI_ROOT)
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
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.VOICE,                   handle_voice))
    app.add_handler(MessageHandler(filters.PHOTO,                   handle_photo))
    app.add_handler(MessageHandler(filters.Document.ALL,            handle_document))
    app.add_handler(MessageHandler(filters.VIDEO | filters.VIDEO_NOTE, handle_video))

    logger.info("Bot gestartet — polling...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
