# ActionPilot
Turn messy meeting notes into a validated action-item list (task, owner, deadline, priority). Export to CSV or Markdown.

## Features
- Works with **no API key** (rules-based extractor); optional LLM mode via `ANTHROPIC_API_KEY`
- Every result is labelled **AI-generated (validated)** or **Rules-based** so you always know the source
- LLM output is treated as untrusted: fences stripped, JSON parsed, fields validated/repaired, and automatic fallback to rules on any failure
- Input validation, loading/empty/error states, sample data, CSV export, responsive light/dark UI

## Setup (Windows PowerShell)
```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python app.py          # open http://127.0.0.1:5000
pytest                 # run tests
```
Optional AI: copy `.env.example` values into your shell, e.g. `$env:ANTHROPIC_API_KEY="sk-..."` (never commit keys; `.env` is git-ignored).

## RAG (retrieval-augmented generation)
`retriever.py` indexes the markdown files in `knowledge/` (team roster, past meetings, project notes) as paragraph chunks with TF-IDF + cosine similarity, written in pure Python (no embeddings API, no vector DB).
1. **Grounded prompt:** the top chunks relevant to the notes are retrieved and passed to the LLM as reference-only context (to resolve names/roles).
2. **Evidence per item:** each extracted task shows the retrieved source passage. This step runs in code, not in the LLM, so the citations cannot be hallucinated.
3. **Duplicate detection:** a task matching an *open* item from a past meeting is flagged (items marked done are not).
4. **Owner suggestion:** unassigned tasks get a *suggested* owner from the roster (never silently assigned).
Edit the files in `knowledge/` to change what the system knows.

## Architecture
`templates/index.html` (UI) -> `app.py` (Flask: `/api/extract`, `/api/sample`) -> `extractor.py` (validate input -> retrieve context -> AI or rules -> validate output -> enrich with retrieved evidence). No database; state lives in the browser. The API key is only read server-side.

## Limitations
Retrieval is lexical (TF-IDF), so it misses synonyms; the duplicate threshold (0.25) was hand-tuned on a tiny sample KB and should be evaluated on real data; prompt-injection in KB files is mitigated only by labelling context as data. Rules handle common English phrasing only; relative dates are resolved against today's server date; no persistence, auth, or multi-language support; AI mode sends notes to a third-party API.

## Demo steps
Load sample -> Extract (rules) -> show badge + warning -> export CSV -> paste invalid/empty input -> (optional) set key and rerun to see the AI badge.
