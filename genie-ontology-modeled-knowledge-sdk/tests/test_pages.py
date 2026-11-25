"""Tests for genie_ontology_modeled_knowledge_sdk.pages (fake clients only, no live API calls)."""

from __future__ import annotations

import copy
import uuid
from pathlib import Path

import pytest

from genie_ontology_modeled_knowledge_sdk.pages import (
    PagesClient,
    RestPagesClient,
    Term,
    parse_glossary,
    parse_term_file,
    to_page_payload,
    upsert_pages,
)

GLOSSARY = Path(__file__).parent / "fixtures" / "glossary"
DOMAIN = "11111111-2222-3333-4444-555555555555"


class FakePagesClient:
    """In-memory PagesClient that records every call."""

    def __init__(self, pages: list[dict] | None = None):
        self.pages: dict[str, dict] = {}
        for p in pages or []:
            self.pages[p["name"].split("/", 1)[1]] = copy.deepcopy(p)
        self.calls: list[tuple] = []

    @property
    def writes(self) -> list[tuple]:
        return [c for c in self.calls if c[0] in {"create_page", "update_page", "delete_page"}]

    def list_pages(self, domain=None):
        self.calls.append(("list_pages", domain))
        return [
            {k: p.get(k) for k in ("name", "display_name", "domain", "state")}
            for p in self.pages.values() if domain is None or p.get("domain") == domain
        ]

    def get_page(self, page_id):
        self.calls.append(("get_page", page_id))
        return copy.deepcopy(self.pages[page_id])

    def create_page(self, payload):
        self.calls.append(("create_page", copy.deepcopy(payload)))
        pid = str(uuid.uuid4())
        page = {**copy.deepcopy(payload), "name": f"pages/{pid}", "state": "DRAFT"}
        self.pages[pid] = page
        return copy.deepcopy(page)

    def update_page(self, page_id, fields, update_mask):
        self.calls.append(("update_page", page_id, copy.deepcopy(fields), list(update_mask)))
        self.pages[page_id].update(copy.deepcopy(fields))
        return copy.deepcopy(self.pages[page_id])


@pytest.fixture
def terms() -> list[Term]:
    return parse_glossary(GLOSSARY)


def test_parse_glossary_reads_terms_sorted_and_skips_readme(terms):
    assert [t.term for t in terms] == ["Discount", "Net Revenue", "Order Priority"]
    nr = terms[1]
    assert nr.domain == "tpch_supply_chain" and nr.subdomain == "sales"
    assert nr.related_terms == ["Discount", "Gross Revenue"]
    assert nr.sources == ["https://www.tpc.org/tpch/"]
    assert nr.definition.startswith("Revenue after line item discounts")
    assert "Q5" in nr.business_context and "l_discount" in nr.data_usage


def test_parse_term_file_aliases_and_extra_sections(terms):
    disc = terms[0]
    assert disc.synonyms == ["disc"]  # a bare string becomes a one-item list
    assert disc.business_context.startswith("Drives the gap")  # "Business use" alias
    assert disc.extra_sections == {"Caveats": "Stored as a fraction, not a percentage."}
    op = terms[2]
    assert op.synonyms == [] and op.related_terms == [] and op.sources == []


def test_parse_term_file_without_front_matter_returns_none(tmp_path):
    f = tmp_path / "notes.md"
    f.write_text("# Just notes\n\nNo front matter.\n")
    assert parse_term_file(f) is None
    assert parse_glossary(tmp_path) == []


def test_parse_term_file_missing_term_raises(tmp_path):
    f = tmp_path / "bad.md"
    f.write_text("---\ndomain: x\n---\n## Definition\n\nx\n")
    with pytest.raises(ValueError, match="missing 'term'"):
        parse_term_file(f)


def test_parse_glossary_duplicate_terms_raise(tmp_path):
    for name in ("a.md", "b.md"):
        (tmp_path / name).write_text("---\nterm: Revenue\n---\n## Definition\n\nx\n")
    with pytest.raises(ValueError, match="duplicate term"):
        parse_glossary(tmp_path)


def test_to_page_payload_shape(terms):
    nr = terms[1]
    payload = to_page_payload(nr, domain_id=DOMAIN)
    assert set(payload) == {"display_name", "description", "synonyms", "body", "domain"}
    assert payload["display_name"] == "Net Revenue"
    assert payload["domain"] == f"domains/{DOMAIN}"
    assert payload["description"] == "Revenue after line item discounts, before tax."
    # the term itself is removed from synonyms; order kept
    assert payload["synonyms"] == ["net sales", "discounted revenue"]
    body = payload["body"]
    headings = [line for line in body.splitlines() if line.startswith("## ")]
    assert headings == ["## Definition", "## Business context", "## Data usage", "## Related terms", "## Source"]
    assert "* Gross Revenue" in body and "* https://www.tpc.org/tpch/" in body
    assert "state" not in payload and "owner_ids" not in payload


def test_to_page_payload_without_domain_and_limits():
    long_def = "word " * 100
    t = Term(term="Long", synonyms=[f"s{i}" for i in range(60)], definition=long_def)
    payload = to_page_payload(t, domain_id="domains/abc")
    assert payload["domain"] == "domains/abc"  # already-prefixed ids are kept
    assert len(payload["description"]) <= 160 and payload["description"].endswith("...")
    assert len(payload["synonyms"]) == 50
    assert "domain" not in to_page_payload(t)
    with pytest.raises(ValueError):
        to_page_payload(Term(term="  "))


def test_fake_satisfies_protocol():
    assert isinstance(FakePagesClient(), PagesClient)


def test_dry_run_makes_no_writes(terms):
    client = FakePagesClient()
    results = upsert_pages(terms, client, dry_run=True, domain_id=DOMAIN)
    assert [r.action for r in results] == ["create"] * 3
    assert all(r.dry_run and r.page_id is None for r in results)
    assert client.writes == []
    assert client.pages == {}


def test_dry_run_is_the_default(terms):
    client = FakePagesClient()
    upsert_pages(terms, client, domain_id=DOMAIN)
    assert client.writes == []


def test_upsert_creates_then_is_idempotent(terms):
    client = FakePagesClient()
    first = upsert_pages(terms, client, dry_run=False, domain_id=DOMAIN)
    assert [r.action for r in first] == ["create"] * 3
    assert all(r.page_id for r in first)
    assert len(client.writes) == 3

    client.calls.clear()
    second = upsert_pages(terms, client, dry_run=False, domain_id=DOMAIN)
    assert [r.action for r in second] == ["unchanged"] * 3
    assert client.writes == []
    assert {r.page_id for r in second} == {r.page_id for r in first}


def test_upsert_updates_only_changed_fields_and_keeps_state(terms):
    client = FakePagesClient()
    upsert_pages(terms, client, dry_run=False, domain_id=DOMAIN)
    # someone published one page; the glossary then changed its synonyms
    pid = next(k for k, p in client.pages.items() if p["display_name"] == "Discount")
    client.pages[pid]["state"] = "PUBLISHED"
    changed = copy.deepcopy(terms)
    changed[0].synonyms = ["disc", "price reduction"]

    client.calls.clear()
    results = upsert_pages(changed, client, dry_run=False, domain_id=DOMAIN)
    assert [r.action for r in results] == ["update", "unchanged", "unchanged"]
    assert results[0].changed_fields == ["synonyms"]
    assert client.writes == [("update_page", pid, {"synonyms": ["disc", "price reduction"]}, ["synonyms"])]
    assert client.pages[pid]["state"] == "PUBLISHED"


def test_upsert_matches_titles_case_insensitively_and_never_deletes(terms):
    existing = {
        "name": "pages/p1", "domain": f"domains/{DOMAIN}", "display_name": "net revenue",
        "body": "old", "description": "old", "synonyms": [], "state": "DRAFT",
    }
    other = {**existing, "name": "pages/p2", "display_name": "Unrelated Term"}
    client = FakePagesClient([existing, other])
    results = upsert_pages(terms, client, dry_run=False, domain_id=DOMAIN)
    by_term = {r.term: r for r in results}
    assert by_term["Net Revenue"].action == "update" and by_term["Net Revenue"].page_id == "p1"
    assert "display_name" not in by_term["Net Revenue"].changed_fields
    assert "p2" in client.pages  # pages without a term are left alone


def test_upsert_without_domain_reports_errors_for_missing_pages(terms):
    client = FakePagesClient()
    results = upsert_pages(terms, client, dry_run=False)
    assert {r.action for r in results} == {"error"}
    assert all("domain_id" in r.error for r in results)
    assert client.writes == []


def test_upsert_duplicate_titles_and_failures_do_not_stop_batch(terms):
    dup = {"domain": f"domains/{DOMAIN}", "display_name": "Discount", "body": "", "state": "DRAFT"}
    client = FakePagesClient([{**dup, "name": "pages/a"}, {**dup, "name": "pages/b"}])

    def boom(payload):
        if payload["display_name"] == "Net Revenue":
            raise RuntimeError("PERMISSION_DENIED")
        return FakePagesClient.create_page(client, payload)

    client.create_page = boom
    results = upsert_pages(terms, client, dry_run=False, domain_id=DOMAIN)
    assert [r.action for r in results] == ["error", "error", "create"]
    assert "several pages" in results[0].error and "PERMISSION_DENIED" in results[1].error


class _RecordingApi:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def do(self, method, path, query=None, body=None, **_):
        self.calls.append((method, path, query, body))
        return self.responses.pop(0) if self.responses else {}


class _Ws:
    def __init__(self, api):
        self.api_client = api


def test_rest_client_requests():
    api = _RecordingApi([
        {"pages": [{"name": "pages/1"}], "next_page_token": "t"},
        {"pages": [{"name": "pages/2"}]},
    ])
    client = RestPagesClient(_Ws(api))
    assert isinstance(client, PagesClient)
    assert [p["name"] for p in client.list_pages(DOMAIN)] == ["pages/1", "pages/2"]
    assert api.calls[0][2]["filter"] == f'domain = "domains/{DOMAIN}"'
    assert api.calls[1][2]["page_token"] == "t"

    api.calls.clear()
    client.get_page("pages/abc")
    client.create_page({"display_name": "X", "domain": "domains/d"})
    client.update_page("abc", {"body": "b", "synonyms": ["s"]}, ["body", "synonyms"])
    assert api.calls[0][:2] == ("GET", "/api/2.0/knowledge/pages/abc")
    assert api.calls[1] == ("POST", "/api/2.0/knowledge/pages", None, {"display_name": "X", "domain": "domains/d"})
    assert api.calls[2] == (
        "PATCH", "/api/2.0/knowledge/pages/abc", {"update_mask": "body,synonyms"}, {"body": "b", "synonyms": ["s"]},
    )


@pytest.mark.parametrize("text, expected", [
    ("Rate per e.g. order. Second sentence.", "Rate per e.g. order."),
    ("Share of orders, i.e. the fraction shipped late. More.", "Share of orders, i.e. the fraction shipped late."),
    ("Sum of costs (approx. 10%) per part. More.", "Sum of costs (approx. 10%) per part."),
    ("Revenue after discounts. Before tax.", "Revenue after discounts."),
    ("Is it late? Yes when shipped after commit.", "Is it late?"),
    ("Version 1.5 of the metric applies. More.", "Version 1.5 of the metric applies."),
    ("No terminal punctuation", "No terminal punctuation"),
    ("Ends at the end.", "Ends at the end."),
])
def test_first_sentence_skips_abbreviations(text, expected):
    from genie_ontology_modeled_knowledge_sdk.pages import _first_sentence

    assert _first_sentence(text) == expected
