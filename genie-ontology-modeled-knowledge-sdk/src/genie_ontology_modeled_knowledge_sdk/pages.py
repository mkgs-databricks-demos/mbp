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
* ``write_terms(terms, folder) -> list[str]`` (many term files in one call)
* ``to_page_payload(term, domain_id=None) -> dict``
* ``upsert_pages(terms, client, *, domain_id=None, dry_run=True, status="DRAFT", only_ids=None)
  -> list[PageResult]``
* ``created_ids(results)`` and ``format_registration_table(results)``
* ``PagesClient`` (protocol) and ``RestPagesClient(ws)``

``upsert_pages`` is idempotent and domain scoped: a live run needs
``domain_id``, matches titles only among that domain's pages, creates missing
pages (``DRAFT`` by default), updates only the fields that differ, never
changes a page in another domain and never deletes. In ``dry_run`` mode it
only reads. All REST details live in ``RestPagesClient``, so an endpoint
change touches one class.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

import yaml

__all__ = [
    "Term",
    "PageResult",
    "PagesClient",
    "RestPagesClient",
    "parse_glossary",
    "parse_term_file",
    "render_term_file",
    "write_terms",
    "to_page_payload",
    "upsert_pages",
    "created_ids",
    "format_registration_table",
    "PAGE_FIELDS",
    "PAGE_STATUSES",
]

# Page fields the SDK manages. ``state`` and ``owner_ids`` are left to people:
# pages are created as DRAFT (unless ``status`` asks otherwise) and an existing
# page's state/owner is never changed.
PAGE_FIELDS = ("display_name", "description", "synonyms", "body")

# ``status`` values accepted by ``upsert_pages`` for new pages.
PAGE_STATUSES = ("DRAFT", "PUBLISHED")

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

    ``action`` is ``created``, ``updated``, ``unchanged``, ``skipped`` or
    ``error``. In dry-run mode ``created``/``updated`` describe what *would*
    happen and nothing is written (``dry_run`` is True).

    ``status`` is the page state (``DRAFT``/``PUBLISHED``) when known.
    ``reason`` explains a ``skipped`` or ``error`` result and flags notes on
    the others; machine-readable values are ``collision_other_domain`` (a
    same-title page exists in another domain; it is never updated),
    ``exists_not_owned`` (a same-title page in the domain is not in
    ``only_ids``) and ``no_domain_id``. ``collisions`` lists the ids of
    same-title pages in other domains (dry runs only; live runs never list
    outside the domain).
    """

    term: str
    action: str
    page_id: str | None = None
    status: str | None = None
    reason: str = ""
    changed_fields: list[str] = field(default_factory=list)
    dry_run: bool = True
    collisions: list[str] = field(default_factory=list)

    @property
    def error(self) -> str | None:
        """The error message of an ``error`` result (kept for build-0 callers)."""
        return self.reason if self.action == "error" else None


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
        return (
            self._api.do(
                "PATCH",
                f"{self.BASE}/{_page_id(page_id)}",
                query={"update_mask": ",".join(update_mask)},
                body=body,
            )
            or {}
        )


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
        sections[m.group(1).strip()] = body[m.end() : end].strip()
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

    sections = _split_sections(text[m.end() :])
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
# Writing term files
# ---------------------------------------------------------------------------

_TERM_KEYS = {f for f in Term.__dataclass_fields__ if f != "path"}
_RESERVED_HEADINGS = {"related terms", "source", "sources"} | {n for names in _SECTION_ALIASES.values() for n in names}


def _term_slug(name: str) -> str:
    slug = re.sub(r"[^0-9a-z]+", "_", name.casefold()).strip("_")
    if not slug:
        raise ValueError(f"term {name!r} has no letters or digits for a file name")
    return slug


def _coerce_term(item: Term | Mapping[str, Any]) -> Term:
    if isinstance(item, Term):
        return item
    if not isinstance(item, Mapping):
        raise ValueError(f"a term must be a Term or a mapping, got {type(item).__name__}")
    unknown = set(item) - _TERM_KEYS
    if unknown:
        raise ValueError(f"unknown term keys: {sorted(unknown)}")
    name = str(item.get("term") or "").strip()
    if not name:
        raise ValueError("a term mapping needs 'term'")
    kw: dict[str, Any] = {k: item[k] for k in item if k != "term"}
    for key in ("synonyms", "related_terms", "sources"):
        if key in kw:
            kw[key] = _as_list(kw[key], key, name)
    for key in ("definition", "business_context", "data_usage"):
        if key in kw:
            kw[key] = str(kw[key] or "")
    if "extra_sections" in kw:
        kw["extra_sections"] = {str(h): str(c or "") for h, c in dict(kw["extra_sections"] or {}).items()}
    return Term(term=name, **kw)


def render_term_file(term: Term) -> str:
    """Glossary term file text for ``term`` (the inverse of ``parse_term_file``).

    Empty optional front matter keys and sections are left out. Raises
    ``ValueError`` when a section would not survive a parse: an extra section
    named like a built-in one, or content that contains its own ``## `` heading.
    """
    name = term.term.strip()
    if not name:
        raise ValueError("term name is empty")
    meta: dict[str, Any] = {"term": name}
    if term.synonyms:
        meta["synonyms"] = list(term.synonyms)
    if term.domain:
        meta["domain"] = term.domain
    if term.subdomain:
        meta["subdomain"] = term.subdomain
    if term.related_terms:
        meta["related_terms"] = list(term.related_terms)
    if term.sources:
        meta["sources"] = list(term.sources)
    front = yaml.safe_dump(meta, sort_keys=False, allow_unicode=True, default_flow_style=None, width=10_000).strip()

    sections = [("Definition", term.definition)]
    if term.business_context.strip():
        sections.append(("Business context", term.business_context))
    if term.data_usage.strip():
        sections.append(("Data usage", term.data_usage))
    for heading, content in term.extra_sections.items():
        if heading.strip().lower() in _RESERVED_HEADINGS:
            raise ValueError(f"{name}: extra section {heading!r} clashes with a built-in section")
        sections.append((heading.strip(), content))
    parts = []
    for heading, content in sections:
        text = (content or "").strip()
        if _HEADING.search(text):
            raise ValueError(f"{name}: section {heading!r} contains a '## ' heading")
        parts.append(f"## {heading}\n\n{text}" if text else f"## {heading}")
    return f"---\n{front}\n---\n" + "\n\n".join(parts) + "\n"


def write_terms(terms: Iterable[Term | Mapping[str, Any]], folder: str | Path) -> list[str]:
    """Write many glossary term files in one call; returns their paths.

    Each term (a ``Term`` or a mapping with the same keys) goes to
    ``<folder>/<term_slug>.md``, or to the file that already holds that term
    (matched case insensitively), so re-running updates in place. A file whose
    content is already identical is not rewritten. Duplicate terms in one call
    raise ``ValueError`` before anything is written. The output parses back
    with ``parse_glossary``.
    """
    d = Path(folder)
    d.mkdir(parents=True, exist_ok=True)
    existing: dict[str, Path] = {}
    for f in sorted(d.glob("*.md")):
        if f.name.lower() in _SKIP_FILES:
            continue
        try:
            t = parse_term_file(f)
        except (ValueError, yaml.YAMLError):
            continue
        if t is not None:
            existing.setdefault(t.term.casefold(), f)

    planned: list[tuple[Path, str]] = []
    seen_terms: set[str] = set()
    seen_paths: set[Path] = set()
    for item in terms:
        term = _coerce_term(item)
        key = term.term.strip().casefold()
        if key in seen_terms:
            raise ValueError(f"duplicate term {term.term!r} in write_terms")
        seen_terms.add(key)
        path = existing.get(key) or d / f"{_term_slug(term.term)}.md"
        if path in seen_paths:
            raise ValueError(f"terms collide on file name {path.name}")
        seen_paths.add(path)
        planned.append((path, render_term_file(term)))

    out: list[str] = []
    for path, text in planned:
        if not path.exists() or path.read_text(encoding="utf-8") != text:
            path.write_text(text, encoding="utf-8")
        out.append(str(path))
    return out


# ---------------------------------------------------------------------------
# Payloads
# ---------------------------------------------------------------------------


def _domain_name(domain_id: str) -> str:
    domain_id = domain_id.strip()
    return domain_id if domain_id.startswith("domains/") else f"domains/{domain_id}"


def _page_id(page: str) -> str:
    return page.split("/", 1)[1] if page.startswith("pages/") else page


# Words ending in "." that do not end a sentence (compared lowercase, without the final dot).
_ABBREVIATIONS = frozenset(
    {
        # Only unambiguous abbreviations: a word that also ends sentences ("max", "no") would make
        # a real sentence end run on.
        "e.g",
        "i.e",
        "etc",
        "vs",
        "approx",
        "incl",
        "excl",
        "cf",
        "mr",
        "mrs",
        "dr",
        "inc",
        "ltd",
        "corp",
        "dept",
        "jan",
        "feb",
        "apr",
        "jun",
        "jul",
        "aug",
        "sept",
        "oct",
        "nov",
        "dec",
        "u.s",
        "u.k",
    }
)
_SENTENCE_END = re.compile(r"[.!?](?=\s|$)")

# Markdown links: images ``![alt](url)``, inline ``[text](url "title")``, reference
# ``[text][ref]`` and autolinks ``<https://...>``. Descriptions keep the text only.
_MD_IMAGE = re.compile(r"!\[([^\]]*)\]\([^)]*\)")
_MD_LINK = re.compile(r"\[([^\]]+)\]\((?:[^()]|\([^)]*\))*\)")
_MD_REF_LINK = re.compile(r"\[([^\]]+)\]\[[^\]]*\]")
_MD_AUTOLINK = re.compile(r"<((?:https?|mailto):[^>\s]+)>")


def _strip_links(text: str) -> str:
    """Replace markdown links with their text (autolinks with the bare URL)."""
    text = _MD_IMAGE.sub(r"\1", text)
    text = _MD_LINK.sub(r"\1", text)
    text = _MD_REF_LINK.sub(r"\1", text)
    return _MD_AUTOLINK.sub(r"\1", text)


def _truncate(text: str, limit: int) -> str:
    """Cut ``text`` to ``limit`` characters with ``...``, never inside a URL."""
    if len(text) <= limit:
        return text
    cut = limit - 3
    start = text.rfind(" ", 0, cut) + 1
    end = text.find(" ", start)
    token = text[start : end if end != -1 else len(text)]
    if "://" in token and start + len(token) > cut:
        cut = start
    return text[:cut].rstrip() + "..."


def _first_sentence(text: str) -> str:
    """First sentence of `text`, truncated to MAX_DESCRIPTION.

    Markdown links are reduced to their text first, so truncation never cuts a link in
    half, and a bare URL at the cut is dropped whole. A `.` ends the sentence only when
    it follows a word that is not a known abbreviation ("e.g.", "i.e.", "etc.",
    "approx.") and the next word does not start in lower case, so "Rate per e.g. order."
    is kept whole.
    """
    flat = _strip_links(" ".join(text.split()))
    if not flat:
        return ""
    sentence = flat
    for m in _SENTENCE_END.finditer(flat):
        end = m.end()
        if flat[m.start()] == ".":
            word = flat[: m.start()].rsplit(" ", 1)[-1].lower().lstrip("(\"'")
            if word in _ABBREVIATIONS:
                continue
            nxt = flat[end:].lstrip()[:1]
            if nxt and nxt.islower():
                continue
        sentence = flat[:end]
        break
    return _truncate(sentence, MAX_DESCRIPTION)


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
    return [f for f in PAGE_FIELDS if f in payload and _normalize(f, existing.get(f)) != _normalize(f, payload[f])]


def _page_domain(page: dict) -> str | None:
    d = str(page.get("domain") or "").strip()
    return _domain_name(d) if d else None


def _title_key(page: dict) -> str:
    return str(page.get("display_name") or "").strip().casefold()


def upsert_pages(
    terms: Iterable[Term],
    client: PagesClient,
    *,
    domain_id: str | None = None,
    dry_run: bool = True,
    status: str = "DRAFT",
    only_ids: Iterable[str] | None = None,
) -> list[PageResult]:
    """Create or update one page per term inside one domain; never deletes.

    * A live run (``dry_run=False``) without ``domain_id`` writes nothing and
      lists nothing: every term is an ``error`` result.
    * Titles (``display_name``, case insensitive) are matched only among the
      pages of ``domain_id`` (``client.list_pages(domain)``). A page from any
      other domain is never fetched for update or written, even if the client
      returns it.
    * Dry runs also list account-wide to report same-title pages in other
      domains (``reason == "collision_other_domain"``, ids in ``collisions``).
      If that listing is refused, the domain-scoped result is still returned
      with a note in ``reason``. Live runs never list outside the domain.
    * ``only_ids`` (ids created earlier, e.g. from ``pages_registration.md``):
      when given, only pages in this set are updated; any other same-title
      page in the domain is ``skipped`` with ``reason == "exists_not_owned"``.
    * New pages get ``status`` (``DRAFT`` by default; ``DRAFT`` is sent by
      omitting ``state``). An existing page's state is never changed.

    A match is fetched in full and only the fields in ``PAGE_FIELDS`` that
    differ are written (``update_mask``), so a second run over the same terms
    reports every page ``unchanged``. Several in-scope pages with the same
    title are an ``error`` (resolve by hand). One failing term does not stop
    the others. Each result carries ``page_id`` and ``status``; use
    ``created_ids`` to record the pages a live run created.

    ``dry_run=True`` (the default) only calls ``list_pages`` / ``get_page``.
    """
    status = (status or "").strip().upper()
    if status not in PAGE_STATUSES:
        raise ValueError(f"status must be one of {PAGE_STATUSES}, got {status!r}")
    terms = list(terms)
    domain = _domain_name(domain_id) if domain_id and domain_id.strip() else None
    owned = {_page_id(str(i).strip()) for i in only_ids if str(i).strip()} if only_ids is not None else None

    if domain is None and not dry_run:
        return [
            PageResult(
                term=t.term,
                action="error",
                dry_run=False,
                reason="no_domain_id: a live run needs domain_id; nothing was written",
            )
            for t in terms
        ]

    in_domain: dict[str, list[dict]] = {}
    elsewhere: dict[str, set[str]] = {}
    domain_page_ids: set[str] = set()
    if domain is not None:
        for page in client.list_pages(domain):
            pid = _page_id(str(page.get("name") or ""))
            page_domain = _page_domain(page)
            if page_domain is not None and page_domain != domain:
                # Defensive: a client that ignores the filter must not make us touch this page.
                elsewhere.setdefault(_title_key(page), set()).add(pid)
                continue
            domain_page_ids.add(pid)
            in_domain.setdefault(_title_key(page), []).append(page)

    note = ""
    if dry_run:
        try:
            account_pages = client.list_pages(None)
        except Exception as e:  # noqa: BLE001 - collisions are advisory; report and keep the domain result
            account_pages = []
            note = f"collision check unavailable: {e}"
        for page in account_pages:
            pid = _page_id(str(page.get("name") or ""))
            if pid in domain_page_ids or (domain is not None and _page_domain(page) == domain):
                continue
            elsewhere.setdefault(_title_key(page), set()).add(pid)

    results: list[PageResult] = []
    for term in terms:
        try:
            payload = to_page_payload(term, domain)
        except ValueError as e:
            results.append(PageResult(term=term.term, action="error", dry_run=dry_run, reason=str(e)))
            continue

        key = payload["display_name"].casefold()
        collisions = sorted(elsewhere.get(key, set()))
        flag = "collision_other_domain" if collisions else note
        if domain is None:
            results.append(
                PageResult(
                    term=term.term,
                    action="skipped",
                    dry_run=True,
                    reason="no_domain_id" + ("; collision_other_domain" if collisions else ""),
                    collisions=collisions,
                )
            )
            continue

        matches = in_domain.get(key, [])
        try:
            if owned is not None and matches:
                mine = [p for p in matches if _page_id(str(p.get("name") or "")) in owned]
                if not mine:
                    first = matches[0]
                    results.append(
                        PageResult(
                            term=term.term,
                            action="skipped",
                            page_id=_page_id(str(first.get("name") or "")) or None,
                            status=str(first.get("state") or "") or None,
                            reason="exists_not_owned",
                            dry_run=dry_run,
                            collisions=collisions,
                        )
                    )
                    continue
                matches = mine
            if len(matches) > 1:
                ids = ", ".join(str(p.get("name")) for p in matches)
                results.append(
                    PageResult(
                        term=term.term,
                        action="error",
                        dry_run=dry_run,
                        reason=f"several pages titled '{term.term}': {ids}",
                        collisions=collisions,
                    )
                )
                continue

            if not matches:
                create_payload = dict(payload)
                if status != "DRAFT":
                    create_payload["state"] = status
                page_id = None
                page_status: str | None = status
                if not dry_run:
                    created = client.create_page(create_payload)
                    page_id = _page_id(str(created.get("name") or "")) or None
                    page_status = str(created.get("state") or status)
                    in_domain[key] = [created]
                    if owned is not None and page_id:
                        owned.add(page_id)
                results.append(
                    PageResult(
                        term=term.term,
                        action="created",
                        page_id=page_id,
                        status=page_status,
                        reason=flag,
                        changed_fields=[f for f in PAGE_FIELDS if f in payload],
                        dry_run=dry_run,
                        collisions=collisions,
                    )
                )
                continue

            page_id = _page_id(str(matches[0].get("name") or ""))
            existing = client.get_page(page_id)
            existing_domain = _page_domain(existing)
            if existing_domain is not None and existing_domain != domain:
                results.append(
                    PageResult(
                        term=term.term,
                        action="skipped",
                        reason="collision_other_domain",
                        dry_run=dry_run,
                        collisions=sorted({*collisions, page_id}),
                    )
                )
                continue
            page_status = str(existing.get("state") or matches[0].get("state") or "") or None
            changed = [f for f in _diff(existing, payload) if f != "display_name"]
            if not changed:
                results.append(
                    PageResult(
                        term=term.term,
                        action="unchanged",
                        page_id=page_id,
                        status=page_status,
                        reason=flag,
                        dry_run=dry_run,
                        collisions=collisions,
                    )
                )
                continue
            if not dry_run:
                client.update_page(page_id, {f: payload[f] for f in changed}, changed)
            results.append(
                PageResult(
                    term=term.term,
                    action="updated",
                    page_id=page_id,
                    status=page_status,
                    reason=flag,
                    changed_fields=changed,
                    dry_run=dry_run,
                    collisions=collisions,
                )
            )
        except Exception as e:  # noqa: BLE001 - one failing term must not stop the batch; reported per term
            results.append(PageResult(term=term.term, action="error", dry_run=dry_run, reason=str(e)))
    return results


def created_ids(results: Iterable[PageResult]) -> list[str]:
    """Ids of the pages a live run created, in result order (for cleanup records)."""
    return [r.page_id for r in results if r.action == "created" and not r.dry_run and r.page_id]


def _cell(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ").strip() or "-"


def format_registration_table(results: Iterable[PageResult]) -> str:
    """Markdown registration table: one ``term | page id | status | action`` row per result.

    The domain is shown only as "development domain"; no domain id is written,
    so the table can be committed. Dry-run actions are marked ``(dry run)``.
    """
    lines = [
        "Domain: development domain",
        "",
        "| Term | Page id | Status | Action |",
        "| --- | --- | --- | --- |",
    ]
    for r in results:
        action = r.action + (" (dry run)" if r.dry_run else "")
        lines.append(f"| {_cell(r.term)} | {_cell(r.page_id or '')} | {_cell(r.status or '')} | {_cell(action)} |")
    return "\n".join(lines) + "\n"
