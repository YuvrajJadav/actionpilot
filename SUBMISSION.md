# Submission guide (personal notes)

## Files
- `extractor.py` core logic: `validate_input`, `extract_with_rules`, `call_anthropic`, `parse_llm_json`/`normalize_items` (output validation), `extract` (orchestration + fallback)
- `app.py` thin Flask layer; `templates/index.html` single-page UI (DOM built with `textContent`, so no XSS from notes)
- `tests/test_extractor.py` 12 tests; `samples/meeting.txt` demo data

## Design decision: validate-and-fallback instead of trusting the LLM
Alternatives: (a) AI only: fails without key/network, (b) rules only: brittle, (c) AI with a function-calling schema: better, but needs SDK/key. I chose rules as the guaranteed baseline plus AI as an enhancer whose output is validated. The app never breaks and never mislabels the source.

## Real mistake from this build (honest account)
1. My setup command used `mkdir -p a/{b,c}` in `/bin/sh`, which doesn't expand braces. It created a folder literally named `{templates,samples,tests}` and my sample/test files silently failed to write. Detected by the stderr "Directory nonexistent" and `no tests ran`. Fixed by creating the dirs explicitly.
2. The first test run caught a logic bug: `Action: Dana - book the demo room` produced no owner, because the regex only handled "Name will/needs to...". Fixed by adding a `Name - task` pattern for labelled lines. The test was written from the spec before the code was fixed.
**Controlled failure for the video (optional, also honest):** in `parse_llm_json`, comment out the line that strips ``` fences, run `pytest`, show `test_llm_output_in_markdown_fences_is_parsed` fail, restore, show green.

## Limitations / next day
Schema-constrained LLM output (tool use), an evaluation set of real notes to measure rules vs AI accuracy, time zones, owner-name matching from the attendee list, Slack/Jira export.

## Interview Q&A
- *Why Flask?* Smallest thing that serves a page plus a JSON API; no build step on Windows.
- *How do you handle hallucinated output?* Strict parsing, field-level validation (ISO dates, enum priority, length caps), drop invalid items, fall back if none survive.
- *Security?* Key stays server-side in env; UI uses `textContent`; input length capped at 20k chars.
- *Why not a database?* Nothing needs persistence; adding one adds failure modes.
- *How would you measure AI quality?* Labelled notes, compare precision/recall on owner+deadline against the rules baseline.
- *Did the tests exercise the real AI?* No. They use an injected fake LLM. The live API call is untested here; try it yourself with your key.

## Checklist
- [ ] Fresh clone -> venv -> `pip install -r requirements.txt` -> `pytest` green -> `python app.py`
- [ ] Walk the flow: sample, extract, export, empty input, long input, AI on/off
- [ ] `git init; git add .; git commit`; confirm `.env` is NOT tracked (`git status`); create GitHub repo; push
- [ ] README renders; repo set to Public (or access granted); open it in an incognito window
- [ ] Record with screen recorder; upload; test the video link logged out

## 5-minute script
- 0:00-0:30 Problem: meetings end with decisions buried in notes; manual follow-up gets dropped.
- 0:30-2:30 Live demo: load sample, extract, point at badge and warning, export CSV, trigger the empty-input error; if you have a key, rerun and show the AI badge.
- 2:30-3:30 Architecture (UI -> Flask -> extractor) and the validate-and-fallback decision.
- 3:30-4:30 The real mistakes above (brace expansion + `Dana` test failure), or the fence-stripping controlled failure.
- 4:30-5:00 Summary and limitations (English-only rules, AI path untested live by me).

## RAG addendum
- **Design decision:** retrieval enrichment runs in code *after* the LLM, not inside it. Alternatives: let the LLM cite sources (can hallucinate them), or use embeddings + vector DB (more setup, offline-unfriendly). TF-IDF is explainable and testable.
- **Real mistake:** I guessed the duplicate threshold at 0.4. The new test `test_duplicate_flag_only_for_open_items` failed (the login-bug task scored 0.263 vs its open past item). I lowered it to 0.25 and verified that the 'done' pricing item is still not flagged. Honest caveat: this is hand-tuned on 4 documents.
- **Q&A:** *Why TF-IDF over embeddings?* No API/paid dependency, deterministic, easy to explain; the retriever interface could be swapped for embeddings. *How do you handle prompt injection from KB text?* Context is labelled as reference data and the LLM output is still schema-validated; enrichment fields can't be forged (tested). *How would you evaluate retrieval?* Labelled query->relevant-chunk pairs, measure recall@k and duplicate precision/recall.
- **Demo add-on:** run the sample, point at 'matches an open past item' on Marco's login bug, 'Suggested owner: Dana (from roster)' on the onboarding checklist, and the retrieved-evidence line under each task.
