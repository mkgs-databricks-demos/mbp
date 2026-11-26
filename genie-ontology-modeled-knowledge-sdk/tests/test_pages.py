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
    created_ids,
    format_registration_table,
    parse_glossary,
    parse_term_file,
    to_page_payload,
    upsert_pages,
    write_terms,
)

GLOSSARY = Path(__file__).parent / "fixtures" / "glossary"
DOMAIN = "11111111-2222-3333-4444-555555555555"
OTHER_DOMAIN = "99999999-8888-7777-6666-555555555555"


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
            for p in self.pages.values()
            if domain is None or p.get("domain") == domain
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
    assert [r.action for r in results] == ["created"] * 3
    assert all(r.dry_run and r.page_id is None and r.status == "DRAFT" for r in results)
    assert client.writes == []
    assert client.pages == {}


def test_dry_run_is_the_default(terms):
    client = FakePagesClient()
    upsert_pages(terms, client, domain_id=DOMAIN)
    assert client.writes == []


def test_upsert_creates_then_is_idempotent(terms):
    client = FakePagesClient()
    first = upsert_pages(terms, client, dry_run=False, domain_id=DOMAIN)
    assert [r.action for r in first] == ["created"] * 3
    assert all(r.page_id and r.status == "DRAFT" for r in first)
    assert len(client.writes) == 3
    assert created_ids(first) == [r.page_id for r in first]

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
    assert [r.action for r in results] == ["updated", "unchanged", "unchanged"]
    assert results[0].changed_fields == ["synonyms"] and results[0].status == "PUBLISHED"
    assert client.writes == [("update_page", pid, {"synonyms": ["disc", "price reduction"]}, ["synonyms"])]
    assert client.pages[pid]["state"] == "PUBLISHED"


def test_upsert_ignores_synonym_order_from_the_api(terms):
    # The Pages API returns synonyms sorted; a second upsert must still report no change.
    unsorted = copy.deepcopy(terms)
    unsorted[0].synonyms = ["zeta rebate", "alpha markdown", "mid reduction"]
    client = FakePagesClient()
    upsert_pages(unsorted, client, dry_run=False, domain_id=DOMAIN)
    for page in client.pages.values():
        page["synonyms"] = sorted(page.get("synonyms") or [])  # what the API stores
    assert any(p["synonyms"] == ["alpha markdown", "mid reduction", "zeta rebate"] for p in client.pages.values())
    client.calls.clear()
    again = upsert_pages(unsorted, client, dry_run=False, domain_id=DOMAIN)
    assert [r.action for r in again] == ["unchanged"] * len(unsorted)
    assert client.writes == []


def test_upsert_matches_titles_case_insensitively_and_never_deletes(terms):
    existing = {
        "name": "pages/p1",
        "domain": f"domains/{DOMAIN}",
        "display_name": "net revenue",
        "body": "old",
        "description": "old",
        "synonyms": [],
        "state": "DRAFT",
    }
    other = {**existing, "name": "pages/p2", "display_name": "Unrelated Term"}
    client = FakePagesClient([existing, other])
    results = upsert_pages(terms, client, dry_run=False, domain_id=DOMAIN)
    by_term = {r.term: r for r in results}
    assert by_term["Net Revenue"].action == "updated" and by_term["Net Revenue"].page_id == "p1"
    assert "display_name" not in by_term["Net Revenue"].changed_fields
    assert "p2" in client.pages  # pages without a term are left alone


def _page(pid, title, domain, **extra):
    return {
        "name": f"pages/{pid}",
        "domain": f"domains/{domain}",
        "display_name": title,
        "body": "theirs",
        "description": "theirs",
        "synonyms": [],
        "state": "PUBLISHED",
        **extra,
    }


def test_live_upsert_without_domain_writes_nothing(terms):
    # same-title pages exist (in some domain): a live run without domain_id must still write nothing
    client = FakePagesClient([_page("x1", "Net Revenue", OTHER_DOMAIN), _page("x2", "Discount", DOMAIN)])
    before = copy.deepcopy(client.pages)
    results = upsert_pages(terms, client, dry_run=False)
    assert [r.action for r in results] == ["error"] * 3
    assert all("domain_id" in r.reason and r.error == r.reason for r in results)
    assert client.writes == []
    assert client.calls == []  # not even an account-wide listing
    assert client.pages == before


def test_same_title_page_in_other_domain_is_never_updated(terms):
    theirs = _page("theirs", "Net Revenue", OTHER_DOMAIN)
    client = FakePagesClient([theirs])

    dry = upsert_pages(terms, client, dry_run=True, domain_id=DOMAIN)
    nr = next(r for r in dry if r.term == "Net Revenue")
    assert nr.action == "created" and nr.reason == "collision_other_domain" and nr.collisions == ["theirs"]
    assert client.writes == []

    client.calls.clear()
    live = upsert_pages(terms, client, dry_run=False, domain_id=DOMAIN)
    nr = next(r for r in live if r.term == "Net Revenue")
    assert nr.action == "created" and nr.page_id != "theirs"
    assert client.pages["theirs"] == theirs  # untouched
    assert all(c[1] != "theirs" for c in client.calls if c[0] in {"get_page", "update_page"})
    # live runs list only the domain, never account-wide
    assert [c for c in client.calls if c[0] == "list_pages"] == [("list_pages", f"domains/{DOMAIN}")]


def test_other_domain_page_is_never_updated_even_if_client_ignores_filter(terms):
    class LeakyClient(FakePagesClient):
        def list_pages(self, domain=None):
            return super().list_pages(None)  # ignores the domain filter

    theirs = _page("theirs", "Discount", OTHER_DOMAIN)
    client = LeakyClient([theirs])
    results = upsert_pages(terms, client, dry_run=False, domain_id=DOMAIN)
    disc = next(r for r in results if r.term == "Discount")
    assert disc.action == "created" and disc.page_id != "theirs"
    assert client.pages["theirs"] == theirs
    assert not [c for c in client.writes if c[0] == "update_page"]


def test_not_owned_same_title_page_in_domain_is_skipped(terms):
    theirs = _page("theirs", "Discount", DOMAIN)
    client = FakePagesClient([theirs])
    results = upsert_pages(terms, client, dry_run=False, domain_id=DOMAIN, only_ids=["pages/mine"])
    by_term = {r.term: r for r in results}
    assert by_term["Discount"].action == "skipped" and by_term["Discount"].reason == "exists_not_owned"
    assert by_term["Discount"].page_id == "theirs" and by_term["Discount"].status == "PUBLISHED"
    assert client.pages["theirs"] == theirs
    assert [c[0] for c in client.writes] == ["create_page", "create_page"]

    # the same page is updated once its id is in only_ids
    client.calls.clear()
    again = upsert_pages(terms, client, dry_run=False, domain_id=DOMAIN, only_ids=["theirs", *created_ids(results)])
    assert {r.term: r.action for r in again} == {
        "Discount": "updated",
        "Net Revenue": "unchanged",
        "Order Priority": "unchanged",
    }
    assert client.pages["theirs"]["state"] == "PUBLISHED"  # state never changed


def test_status_option_for_new_pages(terms):
    client = FakePagesClient()
    upsert_pages(terms[:1], client, dry_run=False, domain_id=DOMAIN)
    assert "state" not in client.writes[0][1]  # DRAFT is the API default

    client = FakePagesClient()
    res = upsert_pages(terms[:1], client, dry_run=False, domain_id=DOMAIN, status="published")
    assert client.writes[0][1]["state"] == "PUBLISHED"
    with pytest.raises(ValueError, match="status"):
        upsert_pages(terms, FakePagesClient(), domain_id=DOMAIN, status="ARCHIVED")
    assert res[0].action == "created"


def test_dry_run_without_domain_reports_collisions_only(terms):
    client = FakePagesClient([_page("x1", "Net Revenue", OTHER_DOMAIN)])
    results = upsert_pages(terms, client)
    assert [r.action for r in results] == ["skipped"] * 3
    by_term = {r.term: r for r in results}
    assert by_term["Net Revenue"].collisions == ["x1"] and "collision_other_domain" in by_term["Net Revenue"].reason
    assert by_term["Discount"].reason == "no_domain_id"
    assert client.writes == []


def test_dry_run_collision_check_refused_keeps_domain_result(terms):
    class DomainOnly(FakePagesClient):
        def list_pages(self, domain=None):
            if domain is None:
                raise PermissionError("PERMISSION_DENIED: Manage Discover")
            return super().list_pages(domain)

    results = upsert_pages(terms, DomainOnly(), domain_id=DOMAIN)
    assert [r.action for r in results] == ["created"] * 3
    assert all("collision check unavailable" in r.reason for r in results)


def test_format_registration_table_hides_domain(terms):
    client = FakePagesClient()
    results = upsert_pages(terms, client, dry_run=False, domain_id=DOMAIN)
    table = format_registration_table(results)
    assert DOMAIN not in table and "domains/" not in table
    assert "development domain" in table
    lines = table.strip().splitlines()
    assert lines[2] == "| Term | Page id | Status | Action |"
    assert len(lines) == 4 + 3
    assert lines[4] == f"| Discount | {results[0].page_id} | DRAFT | created |"
    dry = format_registration_table(upsert_pages(terms, FakePagesClient(), domain_id=DOMAIN))
    assert "| Discount | - | DRAFT | created (dry run) |" in dry


def test_upsert_duplicate_titles_and_failures_do_not_stop_batch(terms):
    dup = {"domain": f"domains/{DOMAIN}", "display_name": "Discount", "body": "", "state": "DRAFT"}
    client = FakePagesClient([{**dup, "name": "pages/a"}, {**dup, "name": "pages/b"}])

    def boom(payload):
        if payload["display_name"] == "Net Revenue":
            raise RuntimeError("PERMISSION_DENIED")
        return FakePagesClient.create_page(client, payload)

    client.create_page = boom
    results = upsert_pages(terms, client, dry_run=False, domain_id=DOMAIN)
    assert [r.action for r in results] == ["error", "error", "created"]
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
    api = _RecordingApi(
        [
            {"pages": [{"name": "pages/1"}], "next_page_token": "t"},
            {"pages": [{"name": "pages/2"}]},
        ]
    )
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
        "PATCH",
        "/api/2.0/knowledge/pages/abc",
        {"update_mask": "body,synonyms"},
        {"body": "b", "synonyms": ["s"]},
    )


@pytest.mark.parametrize(
    "text, expected",
    [
        ("Rate per e.g. order. Second sentence.", "Rate per e.g. order."),
        ("Share of orders, i.e. the fraction shipped late. More.", "Share of orders, i.e. the fraction shipped late."),
        ("Sum of costs (approx. 10%) per part. More.", "Sum of costs (approx. 10%) per part."),
        ("Revenue after discounts. Before tax.", "Revenue after discounts."),
        ("Is it late? Yes when shipped after commit.", "Is it late?"),
        ("Version 1.5 of the metric applies. More.", "Version 1.5 of the metric applies."),
        ("No terminal punctuation", "No terminal punctuation"),
        ("Ends at the end.", "Ends at the end."),
    ],
)
def test_first_sentence_skips_abbreviations(text, expected):
    from genie_ontology_modeled_knowledge_sdk.pages import _first_sentence

    assert _first_sentence(text) == expected


def test_description_strips_link_starting_at_character_150():
    prefix = ("x" * 9 + " ") * 15  # 150 characters
    link = "[TPC-H specification](https://www.tpc.org/tpc_documents_current_versions/pdf/tpc-h_v3.0.1.pdf)"
    text = prefix + link + " and more words after it."
    assert text.index("[") == 150
    desc = to_page_payload(Term(term="T", definition=text))["description"]
    assert len(desc) <= 160
    assert "](" not in desc and "http" not in desc and "[" not in desc
    assert desc.endswith("...") and desc.startswith(prefix.strip())


@pytest.mark.parametrize(
    "text, expected",
    [
        ("See [the spec](https://x.org/a) for rules.", "See the spec for rules."),
        ("Logo ![alt text](img.png) here.", "Logo alt text here."),
        ("Ref [Net Revenue][nr] style.", "Ref Net Revenue style."),
        ("Auto <https://x.org/a> link.", "Auto https://x.org/a link."),
    ],
)
def test_description_link_forms(text, expected):
    from genie_ontology_modeled_knowledge_sdk.pages import _first_sentence

    assert _first_sentence(text) == expected


def test_bare_url_at_the_cut_is_dropped_whole():
    from genie_ontology_modeled_knowledge_sdk.pages import _first_sentence

    text = "y " * 70 + "https://example.com/a/very/long/path/that/crosses/the/limit more"
    desc = _first_sentence(text)
    assert len(desc) <= 160 and "http" not in desc and desc.endswith("...")


def test_write_terms_round_trips_through_parse_glossary(terms, tmp_path):
    paths = write_terms(terms, tmp_path / "semantics")
    assert [Path(p).name for p in paths] == ["discount.md", "net_revenue.md", "order_priority.md"]
    back = parse_glossary(tmp_path / "semantics")
    strip = [{**t.__dict__, "path": None} for t in back]
    assert strip == [{**t.__dict__, "path": None} for t in terms]

    # idempotent: a second call rewrites nothing and returns the same paths
    mtimes = {p: Path(p).stat().st_mtime_ns for p in paths}
    assert write_terms(terms, tmp_path / "semantics") == paths
    assert {p: Path(p).stat().st_mtime_ns for p in paths} == mtimes


def test_write_terms_accepts_mappings_and_updates_in_place(tmp_path):
    (tmp_path / "custom_name.md").write_text("---\nterm: Gross Margin\n---\n## Definition\n\nOld.\n")
    paths = write_terms(
        [
            {"term": "Gross Margin", "synonyms": "gm", "definition": "Revenue minus cost."},
            {"term": "Late Shipment", "related_terms": ["Gross Margin"], "definition": "Shipped after commit."},
        ],
        tmp_path,
    )
    assert [Path(p).name for p in paths] == ["custom_name.md", "late_shipment.md"]
    gm, late = parse_glossary(tmp_path)
    assert gm.synonyms == ["gm"] and gm.definition == "Revenue minus cost."
    assert late.related_terms == ["Gross Margin"]


def test_write_terms_rejects_bad_input_before_writing(tmp_path):
    with pytest.raises(ValueError, match="duplicate term"):
        write_terms([{"term": "A"}, {"term": "a"}], tmp_path)
    with pytest.raises(ValueError, match="unknown term keys"):
        write_terms([{"term": "A", "colour": "red"}], tmp_path)
    with pytest.raises(ValueError, match="heading"):
        write_terms([Term(term="A", definition="x\n\n## Sneaky\n\ny")], tmp_path)
    assert list(tmp_path.glob("*.md")) == []
