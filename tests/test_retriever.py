import json
from datetime import date
from extractor import extract
from retriever import KnowledgeBase, load_kb

TODAY = date(2026, 10, 27)
KB = load_kb()


def test_kb_loads_chunks_and_skips_headings():
    assert len(KB.chunks) >= 8 and not any(c["text"].startswith("#") for c in KB.chunks)


def test_retrieval_ranks_relevant_chunk_first():
    top = KB.search("fix the login bug on Safari", k=1)[0]
    assert top["source"] == "past_meetings.md" and "login" in top["text"].lower()


def test_unrelated_query_returns_nothing():
    assert KB.search("zebra quantum banana") == []


def test_empty_kb_does_not_crash():
    assert KnowledgeBase([]).search("anything") == []


def test_duplicate_flag_only_for_open_items():
    r = extract("Marco needs to fix the login bug.\nPriya will send the pricing deck to finance.", TODAY, use_ai=False)
    by = {i["owner"]: i for i in r["items"]}
    assert by["Marco"]["possible_duplicate"] is True      # open item in past meetings
    assert by["Priya"]["possible_duplicate"] is False     # that one is marked done


def test_suggested_owner_from_roster_for_unassigned():
    r = extract("TODO: update the onboarding checklist", TODAY, use_ai=False)
    assert r["items"][0]["owner"] == "Unassigned" and r["items"][0]["suggested_owner"] == "Dana"


def test_context_is_passed_to_llm_and_enrichment_not_forgeable():
    seen = {}
    def fake(text, today, context):
        seen["ctx"] = context
        return json.dumps([{"task": "fix login bug", "owner": "Marco", "related": [{"source": "FAKE"}]}])
    r = extract("Marco should fix the login bug", TODAY, llm=fake)
    assert "past_meetings.md" in seen["ctx"]
    assert all(x["source"] != "FAKE" for x in r["items"][0]["related"])
