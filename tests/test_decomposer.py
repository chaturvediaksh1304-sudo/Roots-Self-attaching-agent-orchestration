import asyncio

import pytest

from roots.core.decomposer import (
    Decomposition,
    DecompositionError,
    Subtask,
    decompose,
    detect_overlaps,
    parse,
    validate,
)
from tests.fake_adapter import FakeAdapter


# --- pure: overlap detection -------------------------------------------------

def test_detect_overlaps_flags_duplicate_work():
    subs = [
        Subtask("scrape-a", "Scrape product prices from the vendor website"),
        Subtask("scrape-b", "Scrape product prices from the vendor website again"),
    ]
    flagged = detect_overlaps(subs)
    assert flagged and flagged[0][:2] == ("scrape-a", "scrape-b")


def test_detect_overlaps_ignores_distinct_work():
    subs = [
        Subtask("api-research", "Document the payment gateway REST endpoints"),
        Subtask("schema-design", "Design the Postgres orders table columns"),
    ]
    assert detect_overlaps(subs) == []


# --- pure: structural validation ---------------------------------------------

def test_validate_rejects_empty():
    with pytest.raises(DecompositionError):
        validate([])


def test_validate_rejects_duplicate_names():
    with pytest.raises(DecompositionError):
        validate([Subtask("x", "do a"), Subtask("x", "do b")])


def test_validate_rejects_non_kebab_name():
    with pytest.raises(DecompositionError):
        validate([Subtask("Api_Research", "do a")])


def test_validate_rejects_unknown_dependency():
    with pytest.raises(DecompositionError):
        validate([Subtask("a", "do a", depends_on=["ghost"])])


def test_validate_rejects_self_dependency():
    with pytest.raises(DecompositionError):
        validate([Subtask("a", "do a", depends_on=["a"])])


def test_validate_accepts_valid_graph():
    validate([
        Subtask("a", "do a"),
        Subtask("b", "do b", depends_on=["a"]),
    ])


# --- pure: parsing -----------------------------------------------------------

def test_parse_handles_fenced_json():
    text = '```json\n[{"name": "a", "boundary": "do a"}]\n```'
    subs = parse(text)
    assert subs[0].name == "a" and subs[0].boundary == "do a"


def test_parse_rejects_non_array():
    with pytest.raises(DecompositionError):
        parse('{"name": "a"}')


def test_parse_rejects_malformed_entry():
    with pytest.raises(DecompositionError):
        parse('[{"boundary": "no name"}]')


# --- async: decompose end-to-end via fake adapter ----------------------------

def test_decompose_repairs_on_overlap():
    overlapping = (
        '[{"name":"scrape-a","boundary":"Scrape prices from the vendor site"},'
        '{"name":"scrape-b","boundary":"Scrape prices from the vendor site now"}]'
    )
    clean = (
        '[{"name":"scrape","boundary":"Scrape prices from the vendor site"},'
        '{"name":"summarize","boundary":"Summarize the scraped price table"}]'
    )
    adapter = FakeAdapter(responses=[overlapping, clean])
    result = asyncio.run(decompose("goal", "ctx", adapter))
    assert isinstance(result, Decomposition)
    assert [s.name for s in result.subtasks] == ["scrape", "summarize"]
    assert len(adapter.calls) == 2  # one repair pass fired


def test_decompose_retries_on_malformed_json():
    # first sample is malformed (trailing prose); retry must recover, not abort
    bad = '[{"name":"a","boundary":"do a"}] and here is some explanation'
    good = '[{"name":"research","boundary":"Document the REST API endpoints"}]'
    adapter = FakeAdapter(responses=[bad, good])
    result = asyncio.run(decompose("goal", "ctx", adapter))
    assert [s.name for s in result.subtasks] == ["research"]
    assert len(adapter.calls) == 2  # retried once


def test_decompose_raises_after_exhausting_retries():
    adapter = FakeAdapter(responses=["nonsense", "still bad", "nope"])
    with pytest.raises(DecompositionError):
        asyncio.run(decompose("goal", "ctx", adapter))


def test_decompose_single_pass_when_clean():
    clean = (
        '[{"name":"research","boundary":"Document the REST API endpoints"},'
        '{"name":"schema","boundary":"Design the database table columns"}]'
    )
    adapter = FakeAdapter(responses=[clean])
    result = asyncio.run(decompose("goal", "ctx", adapter))
    assert len(result.subtasks) == 2
    assert len(adapter.calls) == 1  # no repair needed
