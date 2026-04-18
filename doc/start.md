# Ziel
- LLM Knowledgegraph als Hauptkomponente und Wissenspeicher
- Workflows zur Wissen-Speicherung, -Generierung, -Transformierung
- Wissensabfragung 
- Erweiterbarkeit von zusätzlichen Komponenten um mit dem Knowledgegraph zu interagieren

# Wissengraph
- Insipieriert von :
- LLM
- **Selbstheilend**


# Technologien
- Obsidian als UI (Knowledge Graph)
- (Anki, Telegramtrigger, (?)weitere(?))
- N8N Workflows 
- (?) OpenClaw (?)

# Komponente Sprache 
- LLM-Knowledgegraph soll Wortschatz des Nutzer aufbauen
- Routinen um Karteikarten zu erstellen 
	- Verbindung zu Anki App (N8N-Link vllt)
	- Automatisierter Workflo durch Trigger -> Spanisches Wort | Person/Kulturstichwort | Ort -> Analyse des Triggerworts, (Wort->Übersetzung, Konjugation, Beispielsätze), (Person/Kulturstichwort -> Recherche durch Websuche, LLM, ggf Bild, Artikel, .. -> Zusammenfassung), (Ort .. -> Zusammenfassung)  (?) Aufnahme in den Knowledgegraph(?) 
- Zufällige Nachrichten schicken "{'Inhalt': [Fakten, Rätseln, Geschichten, Kulturellem, Aktuellen], 'Ziel':[Sprache verbessern, Geschichten kennen zulernen und zu merken, Nutzer versteht das Land/die Sprache besser}"
- Recherche darüber hinaus (Empfehlungsystem). Die Eingaben des Nutzers sollen als Eingabe genutzt werden um weitere interessante Themen zu suchen und vorzuschlagen.
 

# Komponente Diary
## Kurzbescheibung
- Lebensgeschichten verinnerlichen um sie besser vorzutragen 
	-	Lustige Geschichten aus eigenen Erfahrungen


## Problem:
- Nutzer weiß in sozialen Interaktionen nicht welche eigenen Geschichten unterhaltsam/interessant sein können
- Nutzer hat Schwierigkeiten eigene Geschichten zu finden und vorzutragen ((!)Pointe finden, Tonfall üben(!)

## Methodik
-  **Persöhnlichen Fakten** sollen ausgearbeitet werden. Diese beinhalten interessante, betonungswürdige, lustige, … Fakten/Geschichten des Nutzers.
	1. Persöhnlichen Fakten soll gefunden werden. Durch Analyse des Knowledgegraphs Nutzer verstehen  
	2. Filter von interessanten Geschehnisse. (Korrelationen zu anderen Themen die passen, um Geschichte anzureichern)
	3. Interessante Pointen aufzeigen. 

- Durch Wiederholung und Erinnerungsmechanismen hat der Nutzer eigene Geschichten griffbereit haben, da diese im Zusammenspiel entdeckt, ausgefeilt, und für den Vortrag geübt wurden. 
- KnowledgeGraph soll anhand der **persönlichen Daten** des Nutzers aus dem LLM-Knowledgegraph Potential entdecken, mit interessanten Fakten erweitern und durch Wiederholung/Betonung auf die Besonderheit dieses **persöhnlichen Faktes** hinweisen.
- Hilft dem Nutzer passende **persöhnlichen Fakten** aus seinem Alltag besser zu erkennen und festzuhalten
- Schlägt dem Nutzer Vorschläge vor die für ihn passend sind basierend auf dem Inhalt seines Graphen 
- Übt mit dem Nutzer 

## Ziel:
	- Nutzer lernt sich besser kennen
	- Nutzer ist selbstbewusster
	- Nutzer ist vorbereitet 

## Fragen: 
- Wie **Persöhnlichen Fakten** sammeln?
- Wie müssen Daten abgelegt werden?
- Wie den Nutzer motivieren sich zu öffnen 
- Wie Nutzer lernen aufmerksamer zu sein im echten Leben um mehr **persöhnliche Fakten** zu erleben

# Architektur
## Knowledgegraph

- Inspieriert von :
- """
[Quoted third-party text removed: Andrej Karpathy's "LLM Wiki" idea file (GitHub gist).]
"""
 - "Karpathy shares 'LLM Knowledge Base' architecture that bypasses RAG with an evolving markdown library maintained by AI" https://venturebeat.com/data/karpathy-shares-llm-knowledge-base-architecture-that-bypasses-rag-with-an
 - "Andrej Karpathy’s LLM Knowledge Bases explained" https://medium.com/data-science-in-your-pocket/andrej-karpathys-llm-knowledge-bases-explained-2d9fd3435707

## Supervisor
- Supervisor verteilt dynamisch Aufgaben an:
    1. Routinen (Knowledge aufräumen, Workflows schedulen/triggern ((?)wie dynamisch gestalten, auf Nutzer/aktuelle Geschehnissen in Nutzers Leben eingehen(?)))
    2. Mehrere Agenten/
        2.1. Eigene Persöhnlichkeit und Ziel für den Nutzer (Sprache, Kultur, ...)
        2.2. Erhalten aufgaben von Supervisor
- Supervisor handelt immer aus Sicht des Nutzers
    1. Bewerte die Ergebnisse der Agenten
    2. **persöhnliche Fakten**
- Jeder(Supervisor/Agent) soll mit dem Nutzer interagieren können -> Wissengestaltung (?Supervisor soll neue Informationen/Daten **Interaktionen** immer bewerten ob relevant für den KnowledgeGraph)
(?) Wie Daten/Kommunikation mit anderen Agenten untereinander und mit dem Nutzer selbst gestalten (?)
     

# Datenspeicherung
- (?)Wie Daten von **Interaktionen** speichern und kommunizieren(?)
- LLM-Knowledegraph
- (?)Datenbank notwendig, welche Services nutzen(?)