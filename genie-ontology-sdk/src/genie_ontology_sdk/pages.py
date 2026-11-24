"""Glossary markdown -> Unity Catalog (Discover) knowledge pages.

Wave 5.5 of the pipeline turns the glossary term files written by the domain
research session (``docs/semantics/<term>.md``) into UC knowledge pages.

Glossary term file contract (``docs/plans/INDEX.md``)::

    ---
    term: Net Revenue
    synonyms: [net sales]
    domain: tpch_supply_chain
    subdomain: sales
    related_terms: [Discount, Gross Revenue]
    sources: [https://www.tpc.org/tpch/]
    ---
    ## Definition
    ...
    ## Business context
    ...
    ## Data usage
    ...

Page body sections (L200-F Wave 5.5): Definition, Business context, Data
usage, Related terms, Source.

Public API:

* ``parse_glossary(dir) -> list[Term]``
* ``to_page_payload(term, domain_id=None) -> dict``
* ``upsert_pages(terms, client, *, dry_run=True, domain_id=None) -> list[PageResult]``
* ``PagesClient`` (protocol) and ``RestPagesClient(ws)``

``upsert_pages`` is idempotent: it looks pages up by title, creates missing
ones as ``DRAFT``, updates only the fields that differ, and never deletes. In
``dry_run`` mode it only reads. All REST details live in ``RestPagesClient``,
so an endpoint change touches one class.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Protocol, runtime_checkable

import yaml

__all__ = [
    "Term",
    "PageResult",
    "PagesClient",
    "RestPagesClient",
    "parse_glossary",
    "parse_term_file",
    "to_page_payload",
    "upsert_pages",
    "PAGE_FIELDS",
]

# Page fields the SDK manages. ``state`` and ``owner_ids`` are left to people:
# pages are created as DRAFT and an existing page's state/owner is never changed.
PAGE_FIELDS = ("display_name", "description", "synonyms", "body")

MAX_DESCRIPTION = 160
MAX_SYNONYMS = 50
MAX_NAME = 200

# File names in a glossary folder that are never term files.
_SKIP_FILES = {"index.md", "readme.md"}

_FRONT_MATTER = re.compile(r"\A---[ \t]*\r?\n(.*?)\r?\n---[ \t]*(?:\r?\n|\Z)", re.DOTALL)
_HEADING = re.compile(r"^##[ \t]+(.+?)[ \t]*#*[ \t]*$", re.MULTILINE)

# Canonical section keys -> accepted heading spellings (lower case).
_SECTION_ALIASES = {
    "definition": {"definition"},
    "business_context": {"business context", "business use"},
    "data_usage": {"data usage", "usage in data", "in the data"},
}


@dataclass
class Term:
    """One glossary term parsed from a markdown file."""

    term: str
    synonyms: list[str] = field(default_factory=list)
    domain: str | None = None
    subdomain: str | None = None
    related_terms: list[str] = field(default_factory=list)
    sources: list[str] = field(default_factory=list)
    definition: str = ""
    business_context: str = ""
    data_usage: str = ""
    extra_sections: dict[str, str] = field(default_factory=dict)
    path: str | None = None


@dataclass
class PageResult:
    """Outcome of upserting one term.

    ``action`` is ``create``, ``update``, ``unchanged`` or ``error``. In dry-run
    mode ``create``/``update`` describe what *would* happen and nothing is
    written (``dry_run`` is True).
    """

    term: str
    action: str
    page_id: str | None = None
    changed_fields: list[str] = field(default_factory=list)
    dry_run: bool = True
    error: str | None = None


@runtime_checkable
class PagesClient(Protocol):
    """Minimal knowledge-page API used by ``upsert_pages``.

    Pages are plain dicts with the REST field names: ``name`` (``pages/<id>``),
    ``domain`` (``domains/<id>``), ``display_name``, ``body``, ``description``,
    ``synonyms``, ``state``.
    """

    def list_pages(self, domain: str | None = None) -> list[dict]:
        """All pages (optionally in one ``domains/<id>``); summary fields only."""

    def get_page(self, page_id: str) -> dict:
        """One page with all fields."""

    def create_page(self, payload: dict) -> dict:
        """Create a page from a ``to_page_payload`` dict; returns the page."""

    def update_page(self, page_id: str, fields: dict, update_mask: list[str]) -> dict:
        """Write only ``update_mask`` fields; returns the page."""


class RestPagesClient:
    """``PagesClient`` over the Discover knowledge-page REST API.

    Endpoints: ``GET/POST /api/2.0/knowledge/pages`` and
    ``GET/PATCH /api/2.0/knowledge/pages/{page_id}``, called through
    ``ws.api_client.do``. Bodies are the page fields themselves (not wrapped);
    ``update_mask`` and ``filter`` are query parameters. Listing without a
    domain needs account-wide Manage Discover; with one, domain admin rights.
    """

    BASE = "/api/2.0/knowledge/pages"

    def __init__(self, ws: Any, page_size: int = 100):
        self._api = ws.api_client
        self._page_size = page_size

    def list_pages(self, domain: str | None = None) -> list[dict]:
        query: dict[str, Any] = {"page_size": self._page_size}
        if domain:
            query["filter"] = f'domain = "{_domain_name(domain)}"'
        pages: list[dict] = []
        while True:
            resp = self._api.do("GET", self.BASE, query=query) or {}
            pages.extend(resp.get("pages") or [])
            token = resp.get("next_page_token")
            if not token:
                return pages
            query = {**query, "page_token": token}

    def get_page(self, page_id: str) -> dict:
        return self._api.do("GET", f"{self.BASE}/{_page_id(page_id)}") or {}

    def create_page(self, payload: dict) -> dict:
        return self._api.do("POST", self.BASE, body=dict(payload)) or {}

    def update_page(self, page_id: str, fields: dict, update_mask: list[str]) -> dict:
        body = {k: fields[k] for k in update_mask}
        return self._api.do(
            "PATCH",
            f"{self.BASE}/{_page_id(page_id)}",
            query={"update_mask": ",".join(update_mask)},
            body=body,
        ) or {}


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------


def _as_list(value: Any, key: str, path: str) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value.strip()] if value.strip() else []
    if isinstance(value, (list, tuple)):
        return [str(v).strip() for v in value if v is not None and str(v).strip()]
    raise ValueError(f"{path}: front matter '{key}' must be a list or string")


def _split_sections(body: str) -> dict[str, str]:
    """Split markdown on ``## `` headings -> {heading: text}."""
    sections: dict[str, str] = {}
    matches = list(_HEADING.finditer(body))
    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(body)
        sections[m.group(1).strip()] = body[m.end():end].strip()
    return sections


def parse_term_file(path: str | Path) -> Term | None:
    """Parse one term file. Returns None for markdown without front matter.

    Raises ``ValueError`` when front matter exists but is invalid (not a
    mapping, missing ``term``, wrong list types).
    """
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    m = _FRONT_MATTER.match(text)
    if not m:
        return None
    meta = yaml.safe_load(m.group(1)) or {}
    if not isinstance(meta, dict):
        raise ValueError(f"{p}: front matter must be a mapping")
    name = str(meta.get("term") or "").strip()
    if not name:
        raise ValueError(f"{p}: front matter is missing 'term'")

    sections = _split_sections(text[m.end():])
    known: dict[str, str] = {}
    extra: dict[str, str] = {}
    for heading, content in sections.items():
        key = next((k for k, names in _SECTION_ALIASES.items() if heading.lower() in names), None)
        if key and key not in known:
            known[key] = content
        elif heading.lower() not in {"related terms", "source", "sources"}:
            extra[heading] = content

    return Term(
        term=name,
        synonyms=_as_list(meta.get("synonyms"), "synonyms", str(p)),
        domain=(str(meta["domain"]).strip() or None) if meta.get("domain") else None,
        subdomain=(str(meta["subdomain"]).strip() or None) if meta.get("subdomain") else None,
        related_terms=_as_list(meta.get("related_terms"), "related_terms", str(p)),
        sources=_as_list(meta.get("sources"), "sources", str(p)),
        definition=known.get("definition", ""),
        business_context=known.get("business_context", ""),
        data_usage=known.get("data_usage", ""),
        extra_sections=extra,
        path=str(p),
    )


def parse_glossary(directory: str | Path) -> list[Term]:
    """Parse every ``*.md`` term file in ``directory`` (not recursive).

    ``INDEX.md`` / ``README.md`` and markdown without front matter are skipped.
    Terms are returned sorted by term name. Duplicate term names (case
    insensitive) raise ``ValueError``, since page titles must be unique.
    """
    d = Path(directory)
    if not d.is_dir():
        raise FileNotFoundError(f"glossary directory not found: {d}")
    terms: list[Term] = []
    seen: dict[str, str] = {}
    for f in sorted(d.glob("*.md")):
        if f.name.lower() in _SKIP_FILES:
            continue
        t = parse_term_file(f)
        if t is None:
            continue
        key = t.term.casefold()
        if key in seen:
            raise ValueError(f"duplicate term '{t.term}' in {seen[key]} and {f}")
        seen[key] = str(f)
        terms.append(t)
    return sorted(terms, key=lambda t: t.term.casefold())


# ---------------------------------------------------------------------------
# Payloads
# ---------------------------------------------------------------------------


def _domain_name(domain_id: str) -> str:
    domain_id = domain_id.strip()
    return domain_id if domain_id.startswith("domains/") else f"domains/{domain_id}"


def _page_id(page: str) -> str:
    return page.split("/", 1)[1] if page.startswith("pages/") else page


def _first_sentence(text: str) -> str:
    flat = " ".join(text.split())
    if not flat:
        return ""
    m = re.match(r"(.+?[.!?])(\s|$)", flat)
    sentence = m.group(1) if m else flat
    if len(sentence) > MAX_DESCRIPTION:
        sentence = sentence[: MAX_DESCRIPTION - 3].rstrip() + "..."
    return sentence


def _clean_synonyms(term: Term) -> list[str]:
    out: list[str] = []
    seen = {term.term.casefold()}
    for s in term.synonyms:
        s = s.strip()[:MAX_NAME]
        if s and s.casefold() not in seen:
            seen.add(s.casefold())
            out.append(s)
    return out[:MAX_SYNONYMS]


def _render_body(term: Term) -> str:
    parts = [f"## Definition\n\n{term.definition or '_Not yet defined._'}"]
    if term.business_context:
        parts.append(f"## Business context\n\n{term.business_context}")
    if term.data_usage:
        parts.append(f"## Data usage\n\n{term.data_usage}")
    for heading, content in term.extra_sections.items():
        parts.append(f"## {heading}\n\n{content}")
    if term.related_terms:
        parts.append("## Related terms\n\n" + "\n".join(f"* {r}" for r in term.related_terms))
    if term.sources:
        parts.append("## Source\n\n" + "\n".join(f"* {s}" for s in term.sources))
    return "\n\n".join(parts) + "\n"


def to_page_payload(term: Term, domain_id: str | None = None) -> dict:
    """Create-page body for ``term``.

    Keys: ``display_name``, ``description`` (first sentence of the definition,
    at most 160 characters), ``synonyms`` (deduplicated, at most 50, the term
    itself removed), ``body`` (markdown sections Definition, Business context,
    Data usage, Related terms, Source) and, when ``domain_id`` is given,
    ``domain`` as ``domains/<id>``. ``state`` and ``owner_ids`` are omitted, so
    a new page is a DRAFT owned by the caller.
    """
    name = term.term.strip()
    if not name or len(name) > MAX_NAME:
        raise ValueError(f"term title must be 1-{MAX_NAME} characters: {name!r}")
    payload: dict[str, Any] = {
        "display_name": name,
        "description": _first_sentence(term.definition),
        "synonyms": _clean_synonyms(term),
        "body": _render_body(term),
    }
    if domain_id:
        payload["domain"] = _domain_name(domain_id)
    return payload


# ---------------------------------------------------------------------------
# Upsert
# ---------------------------------------------------------------------------


def _normalize(field_name: str, value: Any) -> Any:
    if field_name == "synonyms":
        return list(value or [])
    if isinstance(value, str):
        return value.strip()
    return value or ""


def _diff(existing: dict, payload: dict) -> list[str]:
    return [
        f for f in PAGE_FIELDS
        if f in payload and _normalize(f, existing.get(f)) != _normalize(f, payload[f])
    ]


def upsert_pages(
    terms: Iterable[Term],
    client: PagesClient,
    *,
    dry_run: bool = True,
    domain_id: str | None = None,
) -> list[PageResult]:
    """Create or update one page per term; never deletes.

    Pages are matched by title (``display_name``, case insensitive) among
    ``client.list_pages(domain)``. A match is fetched in full and only the
    fields in ``PAGE_FIELDS`` that differ are written (``update_mask``), so a
    second run over the same terms reports every page ``unchanged``. Creating
    a page needs ``domain_id``; without one, missing pages are ``error``
    results. Several pages with the same title are an ``error`` (resolve by
    hand). One failing term does not stop the others.

    ``dry_run=True`` (the default) only calls ``list_pages`` / ``get_page``.
    """
    domain = _domain_name(domain_id) if domain_id else None
    by_title: dict[str, list[dict]] = {}
    for page in client.list_pages(domain):
        title = str(page.get("display_name") or "").casefold()
        by_title.setdefault(title, []).append(page)

    results: list[PageResult] = []
    for term in terms:
        try:
            payload = to_page_payload(term, domain_id)
        except ValueError as e:
            results.append(PageResult(term=term.term, action="error", dry_run=dry_run, error=str(e)))
            continue

        matches = by_title.get(payload["display_name"].casefold(), [])
        try:
            if len(matches) > 1:
                ids = ", ".join(str(p.get("name")) for p in matches)
                results.append(PageResult(term=term.term, action="error", dry_run=dry_run,
                                          error=f"several pages titled '{term.term}': {ids}"))
                continue

            if not matches:
                if not domain:
                    results.append(PageResult(term=term.term, action="error", dry_run=dry_run,
                                              error="no existing page and no domain_id to create one in"))
                    continue
                page_id = None
                if not dry_run:
                    created = client.create_page(payload)
                    page_id = _page_id(str(created.get("name") or "")) or None
                    by_title[payload["display_name"].casefold()] = [created]
                results.append(PageResult(term=term.term, action="create", page_id=page_id,
                                          changed_fields=[f for f in PAGE_FIELDS if f in payload],
                                          dry_run=dry_run))
                continue

            page_id = _page_id(str(matches[0].get("name") or ""))
            existing = client.get_page(page_id)
            changed = [f for f in _diff(existing, payload) if f != "display_name"]
            if not changed:
                results.append(PageResult(term=term.term, action="unchanged", page_id=page_id, dry_run=dry_run))
                continue
            if not dry_run:
                client.update_page(page_id, {f: payload[f] for f in changed}, changed)
            results.append(PageResult(term=term.term, action="update", page_id=page_id,
                                      changed_fields=changed, dry_run=dry_run))
        except Exception as e:  # noqa: BLE001 - one failing term must not stop the batch; reported per term
            results.append(PageResult(term=term.term, action="error", dry_run=dry_run, error=str(e)))
    return results
