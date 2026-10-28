import json
from datetime import date
import pytest
from app import app
from extractor import ExtractionError, extract, extract_with_rules, parse_deadline, parse_llm_json

TODAY = date(2026, 10, 27)  # a Tuesday


def test_rules_extract_sample():
    items = extract_with_rules(open("samples/meeting.txt", encoding="utf-8").read(), TODAY)
    by_owner = {i["owner"]: i for i in items}
    assert by_owner["Priya"]["deadline"] == "2026-10-30"
    assert by_owner["Marco"]["priority"] == "high"
    assert by_owner["Dana"]["deadline"] == "2026-10-30"
    assert by_owner["Leo"]["deadline"] == "2026-10-28"
    assert not any("next sync" in i["task"] for i in items)  # plain statements are not actions


def test_deadline_parsing():
    assert parse_deadline("by 2026-11-02", TODAY) == "2026-11-02"
    assert parse_deadline("by 2026-13-45", TODAY) is None
    assert parse_deadline("nothing here", TODAY) is None


@pytest.mark.parametrize("bad", ["", "   ", None, "x" * 20001])
def test_invalid_input(bad):
    with pytest.raises(ExtractionError):
        extract(bad, TODAY)


def test_no_actions_message():
    with pytest.raises(ExtractionError, match="No action items"):
        extract("Just chatting about the weather.", TODAY, use_ai=False)


def test_llm_output_in_markdown_fences_is_parsed():
    raw = '```json\n[{"task":"Ship it","owner":"Ana","deadline":"2026-11-01","priority":"urgent"}]\n```'
    item = parse_llm_json(raw)[0]
    assert item["priority"] == "medium" and item["owner"] == "Ana"  # invalid priority repaired


def test_llm_garbage_falls_back_to_rules():
    r = extract("Priya will send the deck by Friday.", TODAY, llm=lambda t, d, c="": "Sorry, I can't help.")
    assert r["source"] == "rules" and "used rules" in r["warning"]


def test_llm_failure_falls_back_to_rules():
    def boom(t, d, c=""): raise TimeoutError("network down")
    r = extract("Priya will send the deck by Friday.", TODAY, llm=boom)
    assert r["source"] == "rules" and r["items"]


def test_llm_success_labelled_ai():
    ok = lambda t, d, c="": json.dumps([{"task": "A", "owner": None, "deadline": "bad", "priority": "low"}])
    r = extract("anything", TODAY, llm=ok)
    assert r["source"] == "ai" and r["items"][0]["owner"] == "Unassigned" and r["items"][0]["deadline"] is None


def test_api_endpoints(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    c = app.test_client()
    assert c.post("/api/extract", json={"text": ""}).status_code == 400
    text = c.get("/api/sample").get_json()["text"]
    r = c.post("/api/extract", json={"text": text}).get_json()
    assert r["source"] == "rules" and len(r["items"]) >= 4
