"""Genie Agent configuration builder (L200-G, Waves 6-7).

Public API (cross-session contract, see ``docs/plans/INDEX.md``):

* ``MvRef`` / ``AgentPlan``                 - inputs and outputs of agent planning
* ``plan_agents(mvs, max_per_agent=50)``    - organize metric views into agents; splits at
  ``effective_max_per_agent(max_per_agent)`` = ``min(max_per_agent, MAX_DATA_SOURCES)``
* ``build_space(plan, ..., benchmarks=None) -> dict`` - deterministic ``.geniespace.json`` (serialized space v2)
* ``space_to_json(doc) -> str``             - canonical JSON text (sorted keys, 2-space indent)
* ``validate_space(doc) -> list[str]``      - structural problems (empty = valid)
* ``write_domain_manifest(plans, path)``    - ``docs/domain_manifest.yml`` (L200-G shape)
* ``render_text(text, params)``             - token substitution for any string (one SQL statement, ...)
* ``render_space_file(src, dst, params)``   - resolve ``${target_catalog}`` / ``${target_schema}`` /
  ``${warehouse_id}`` tokens; fails on any unresolved token
* ``check_identifiers(idents, ws, warehouse_id)`` - resolve schemas and identifiers through
  ``system.information_schema``; returns the missing ones
* CLI ``python -m genie_ontology_modeled_knowledge_sdk.geniespace render <src_dir> <dst_dir>
  [--params <resolved_target.json | variable-overrides.json>] [--catalog C] [--schema S]
  [--warehouse-id W] [--check]``

Benchmarks section (top-level ``benchmarks`` key of the serialized space). Shape from the
Genie Agents API docs ("Use the Genie Agents API", checked 2026-11-25), **from docs, not
verified** on an exported space (the build-0 TPC-H agent has no benchmarks)::

    "benchmarks": {"questions": [
        {"id": "<32 hex>", "question": ["..."],
         "answer": [{"format": "SQL", "content": ["SELECT ..."]}]}
    ]}

Rules: at most ``MAX_BENCHMARK_QUESTIONS`` (500) questions per agent, exactly one answer
with ``format`` ``SQL`` per question, ids unique and not shared with
``config.sample_questions``.

Committed agent files stay tokenized (``${target_catalog}.${target_schema}.<mv>``);
the bundle (or ``render``) resolves them per target. Pure Python: no Spark. The only
workspace calls are in ``check_identifiers`` / ``render --check`` (an injected or
default ``WorkspaceClient``).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import uuid
from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

__all__ = [
    "DEFAULT_MAX_PER_AGENT",
    "MAX_BENCHMARK_QUESTIONS",
    "MAX_DATA_SOURCES",
    "SPACE_VERSION",
    "TOKEN_IDENTIFIER_PREFIX",
    "MvRef",
    "AgentPlan",
    "mv_refs_from_manifest",
    "effective_max_per_agent",
    "plan_agents",
    "stable_id",
    "build_space",
    "space_to_json",
    "validate_space",
    "domain_manifest",
    "write_domain_manifest",
    "normalize_params",
    "render_text",
    "render_space_text",
    "render_space_file",
    "render_texts",
    "render_dir",
    "space_identifiers",
    "check_identifiers",
    "main",
]

DEFAULT_MAX_PER_AGENT = 50
SPACE_VERSION = 2
MAX_DATA_SOURCES = 30
MAX_BENCHMARK_QUESTIONS = 500
TOKEN_IDENTIFIER_PREFIX = "${target_catalog}.${target_schema}"
SPACE_FILE_SUFFIX = ".geniespace.json"
DEFAULT_SUBDOMAIN = "general"

# Fixed namespace so ids are stable across machines and runs.
_ID_NAMESPACE = uuid.uuid5(uuid.NAMESPACE_URL, "genie-ontology-modeled-knowledge-sdk/geniespace")
_HEX32 = re.compile(r"^[0-9a-f]{32}$")
_TOKEN = re.compile(r"\$\{([^}]*)\}")
_SLUG_STRIP = re.compile(r"[^a-z0-9]+")

# Bundle variable-overrides.json keys -> space file tokens.
_PARAM_ALIASES = {
    "catalog": "target_catalog",
    "schema": "target_schema",
    "warehouse_id": "warehouse_id",
    "target_catalog": "target_catalog",
    "target_schema": "target_schema",
}


# --------------------------------------------------------------------------- planning


@dataclass(frozen=True)
class MvRef:
    """A metric view to place in an agent.

    ``fq_name`` is normally tokenized (``${target_catalog}.${target_schema}.<name>``);
    an empty ``fq_name`` defaults to that form. ``subdomain`` may be ``None``.
    """

    name: str
    fq_name: str = ""
    domain: str = ""
    subdomain: str | None = None
    description: str | None = None

    @property
    def identifier(self) -> str:
        return self.fq_name or f"{TOKEN_IDENTIFIER_PREFIX}.{self.name}"

    @classmethod
    def from_dict(cls, d: Mapping[str, Any]) -> MvRef:
        return cls(
            name=str(d["name"]),
            fq_name=str(d.get("fq_name") or ""),
            domain=str(d.get("domain") or ""),
            subdomain=(str(d["subdomain"]) if d.get("subdomain") else None),
            description=(str(d["description"]) if d.get("description") else None),
        )


@dataclass
class AgentPlan:
    """One Genie Agent: its metric views and the agents it should point users to."""

    name: str
    domain: str
    subdomain: str | None
    metric_views: list[MvRef] = field(default_factory=list)
    related_agents: list[str] = field(default_factory=list)

    @property
    def mv_names(self) -> list[str]:
        return [mv.name for mv in self.metric_views]


def mv_refs_from_manifest(entries: Iterable[Mapping[str, Any]]) -> list[MvRef]:
    """Turn ``manifest.json`` entries (``name``, ``domain``, ``subdomain``) into ``MvRef`` s.

    Identifiers use the ``${target_catalog}.${target_schema}`` tokens.
    """
    return [MvRef.from_dict(e) for e in entries]


def _slug(text: str) -> str:
    s = _SLUG_STRIP.sub("_", text.strip().lower()).strip("_")
    return s or "ontology"


def _primary_domain(mvs: Sequence[MvRef]) -> str:
    counts = Counter(mv.domain for mv in mvs if mv.domain)
    if not counts:
        return "ontology"
    # Most common domain; ties broken by name for determinism.
    return sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[0][0]


def _chunks(items: list[MvRef], size: int) -> list[list[MvRef]]:
    return [items[i : i + size] for i in range(0, len(items), size)]


def effective_max_per_agent(max_per_agent: int = DEFAULT_MAX_PER_AGENT) -> int:
    """The split size ``plan_agents`` uses: ``min(max_per_agent, MAX_DATA_SOURCES)``.

    A Genie Agent holds at most ``MAX_DATA_SOURCES`` (30) tables / metric views, so a
    larger ``max_per_agent`` would produce agents that fail ``validate_space``.
    Raises ``ValueError`` for ``max_per_agent < 1``.
    """
    if not isinstance(max_per_agent, int) or max_per_agent < 1:
        raise ValueError(f"max_per_agent must be an integer >= 1, got {max_per_agent!r}")
    return min(max_per_agent, MAX_DATA_SOURCES)


def plan_agents(mvs: Iterable[MvRef], max_per_agent: int = DEFAULT_MAX_PER_AGENT) -> list[AgentPlan]:
    """Organize metric views into Genie Agents (L200-G organization logic).

    The limit is ``effective_max_per_agent(max_per_agent)``, i.e. never above
    ``MAX_DATA_SOURCES`` (30), so every agent passes ``validate_space``.

    * ``<= limit`` metric views: one agent for the domain.
    * More: one agent per subdomain (MVs without a subdomain go to ``general``).
      Each MV lands in exactly one agent. Cross-domain MVs (domain differs from the
      primary domain) are assigned by their subdomain like any other MV. A subdomain
      that alone exceeds the limit is split into numbered agents
      (``<domain>_<subdomain>_1_agent``, ...). Split agents list each other in
      ``related_agents`` so curation can add pointer instructions.

    Output is deterministic: agents and their metric views are sorted by name.
    Raises ``ValueError`` for ``max_per_agent < 1`` or duplicate metric view names.
    """
    limit = effective_max_per_agent(max_per_agent)
    refs = sorted(mvs, key=lambda m: m.name)
    dupes = sorted(n for n, c in Counter(m.name for m in refs).items() if c > 1)
    if dupes:
        raise ValueError(f"duplicate metric view names: {', '.join(dupes)}")
    if not refs:
        return []

    domain = _primary_domain(refs)
    domain_slug = _slug(domain)
    if len(refs) <= limit:
        return [AgentPlan(name=f"{domain_slug}_agent", domain=domain, subdomain=None, metric_views=refs)]

    groups: dict[str, list[MvRef]] = {}
    for mv in refs:
        groups.setdefault(mv.subdomain or DEFAULT_SUBDOMAIN, []).append(mv)

    plans: list[AgentPlan] = []
    for sub in sorted(groups):
        parts = _chunks(groups[sub], limit)
        for i, part in enumerate(parts, start=1):
            suffix = f"_{i}" if len(parts) > 1 else ""
            plans.append(
                AgentPlan(
                    name=f"{domain_slug}_{_slug(sub)}{suffix}_agent",
                    domain=domain,
                    subdomain=sub,
                    metric_views=part,
                )
            )
    names = [p.name for p in plans]
    for p in plans:
        p.related_agents = [n for n in names if n != p.name]
    return sorted(plans, key=lambda p: p.name)


# --------------------------------------------------------------------------- building


def stable_id(*parts: str) -> str:
    """Deterministic 32-character lowercase hex id (uuid5 of the joined parts)."""
    return uuid.uuid5(_ID_NAMESPACE, "\x1f".join(parts)).hex


def _lines(text: str | Sequence[str]) -> list[str]:
    """SQL / text as the list-of-lines form the serialized space uses."""
    if isinstance(text, str):
        return text.splitlines(keepends=True) or [""]
    return [str(t) for t in text]


def _norm(text: str) -> str:
    return " ".join(text.split()).lower()


def _unique(items: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        item = str(item).strip()
        key = _norm(item)
        if item and key not in seen:
            seen.add(key)
            out.append(item)
    return out


def _sort_keys(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k: _sort_keys(obj[k]) for k in sorted(obj)}
    if isinstance(obj, list):
        return [_sort_keys(v) for v in obj]
    return obj


def build_space(
    plan: AgentPlan,
    *,
    warehouse_id: str | None = None,
    sample_questions: Sequence[str] = (),
    text_instructions: Sequence[str] = (),
    example_sqls: Sequence[Mapping[str, Any]] = (),
    join_specs: Sequence[Mapping[str, Any]] = (),
    benchmarks: Mapping[str, Any] | Sequence[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build the serialized space (v2) for one agent.

    * ``data_sources.tables``: one entry per metric view, ``identifier`` =
      ``MvRef.identifier`` (tokenized by default), sorted by identifier, with the
      MV ``description`` when set.
    * ``config.sample_questions``: de-duplicated questions, id = ``stable_id(question)``.
    * ``instructions.text_instructions``: a single entry holding the de-duplicated
      lines (kept minimal: tune metric views first, L200-H Phase 2).
    * ``instructions.example_question_sqls``: ``{question, sql}`` mappings; ``sql``
      may be a string or a list of lines.
    * ``instructions.join_specs``: passed through; an ``id`` is derived from the
      spec content when missing.
    * ``benchmarks.questions`` (optional): either a benchmarks section
      (``{"questions": [...]}``, as ``benchmark.to_space_benchmarks`` returns) or a list of
      questions. Each question is ``{id?, question, answer}`` in the serialized form, or
      the short form ``{id?, question, sql}`` (``sql`` a string or list of lines), turned
      into one ``SQL`` answer. A missing ``id`` is ``stable_id("benchmark", question)``.
      Nothing is dropped or capped here; ``validate_space`` reports more than 500
      questions, duplicate ids and questions without SQL answer text.

    ``warehouse_id`` is not part of the serialized space (the bundle
    ``genie_spaces`` resource sets it); it is accepted for call-site symmetry and
    only checked for type. Lists are sorted by ``id`` and dict keys are sorted, so
    the same inputs always give byte-identical ``space_to_json`` output.
    """
    if warehouse_id is not None and not isinstance(warehouse_id, str):
        raise TypeError("warehouse_id must be a string or None")

    tables = []
    for mv in sorted(plan.metric_views, key=lambda m: m.identifier):
        entry: dict[str, Any] = {"identifier": mv.identifier}
        if mv.description:
            entry["description"] = [mv.description]
        tables.append(entry)

    questions = [{"id": stable_id(q), "question": [q]} for q in _unique(sample_questions)]

    instructions: dict[str, Any] = {}
    lines = _unique(text_instructions)
    if lines:
        instructions["text_instructions"] = [{"id": stable_id("text_instructions", plan.name), "content": lines}]

    examples = []
    seen_q: set[str] = set()
    for ex in example_sqls:
        q = str(ex["question"]).strip()
        if _norm(q) in seen_q:
            continue
        seen_q.add(_norm(q))
        examples.append({"id": stable_id("example_sql", q), "question": [q], "sql": _lines(ex["sql"])})
    if examples:
        instructions["example_question_sqls"] = sorted(examples, key=lambda e: e["id"])

    joins = []
    for spec in join_specs:
        spec = dict(spec)
        if not spec.get("id"):
            spec["id"] = stable_id("join_spec", json.dumps(spec, sort_keys=True))
        joins.append(spec)
    if joins:
        instructions["join_specs"] = sorted(joins, key=lambda j: j["id"])

    doc: dict[str, Any] = {
        "version": SPACE_VERSION,
        "config": {"sample_questions": sorted(questions, key=lambda q: q["id"])},
        "data_sources": {"tables": tables},
    }
    if instructions:
        doc["instructions"] = instructions
    if benchmarks is not None:
        bench = _benchmark_questions(benchmarks)
        if bench:
            doc["benchmarks"] = {"questions": sorted(bench, key=lambda b: str(b.get("id")))}
    return _sort_keys(doc)


def _benchmark_questions(benchmarks: Mapping[str, Any] | Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Normalize a benchmarks section or question list to serialized-space questions."""
    items: Any = benchmarks.get("questions", []) if isinstance(benchmarks, Mapping) else benchmarks
    out: list[dict[str, Any]] = []
    for item in items or []:
        entry = dict(item)
        question = entry.get("question")
        if isinstance(question, str):
            question = [question.strip()]
        question = [str(q) for q in question] if isinstance(question, list) else []
        if "answer" not in entry:
            sql = entry.pop("sql", None)
            has_sql = bool(sql) and any(str(s).strip() for s in ([sql] if isinstance(sql, str) else sql))
            entry["answer"] = [{"format": "SQL", "content": _lines(sql)}] if has_sql else []
        entry["question"] = question
        if not entry.get("id"):
            entry["id"] = stable_id("benchmark", " ".join(question).strip())
        out.append(entry)
    return out


def space_to_json(doc: Mapping[str, Any]) -> str:
    """Canonical text for a ``.geniespace.json`` file."""
    return json.dumps(doc, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


# --------------------------------------------------------------------------- validation


def _is_three_part(identifier: Any) -> bool:
    if not isinstance(identifier, str):
        return False
    # Tokens contain no dots, so a plain split works for tokenized identifiers too.
    parts = identifier.split(".")
    return len(parts) == 3 and all(p.strip() for p in parts)


def _check_ids(items: Any, where: str, errors: list[str]) -> list[str]:
    ids: list[str] = []
    if not isinstance(items, list):
        errors.append(f"{where}: must be a list")
        return ids
    for i, item in enumerate(items):
        if not isinstance(item, dict):
            errors.append(f"{where}[{i}]: must be an object")
            continue
        item_id = item.get("id")
        if not isinstance(item_id, str) or not _HEX32.match(item_id):
            errors.append(f"{where}[{i}].id: must be a 32-character lowercase hex string, got {item_id!r}")
        else:
            ids.append(item_id)
    return ids


def validate_space(doc: Any) -> list[str]:
    """Structural checks for a serialized space. Returns problems; empty = valid.

    Rules: ``version`` is 2; 1-30 data sources (``data_sources.tables`` plus
    ``data_sources.metric_views`` if present); every identifier is 3-part and
    unique; sample-question ids are unique 32-hex strings with a non-empty
    question; instruction ids are 32-hex; no duplicate text-instruction lines
    (whitespace- and case-insensitive). Optional ``benchmarks.questions``: at most
    ``MAX_BENCHMARK_QUESTIONS`` (500), unique 32-hex ids not shared with sample
    questions, a non-empty question and exactly one ``SQL`` answer with non-empty text.
    """
    if not isinstance(doc, dict):
        return ["space: must be a JSON object"]
    errors: list[str] = []

    if doc.get("version") != SPACE_VERSION:
        errors.append(f"version: must be {SPACE_VERSION}, got {doc.get('version')!r}")

    ds = doc.get("data_sources")
    sources: list[tuple[str, Any]] = []
    if not isinstance(ds, dict):
        errors.append("data_sources: missing or not an object")
    else:
        for key in ("tables", "metric_views"):
            items = ds.get(key, [])
            if not isinstance(items, list):
                errors.append(f"data_sources.{key}: must be a list")
                continue
            sources.extend((f"data_sources.{key}[{i}]", t) for i, t in enumerate(items))
    if not (1 <= len(sources) <= MAX_DATA_SOURCES):
        errors.append(f"data_sources: must have 1-{MAX_DATA_SOURCES} tables/metric views, got {len(sources)}")
    seen_ident: set[str] = set()
    for where, src in sources:
        ident: Any = src.get("identifier") if isinstance(src, dict) else None
        if not _is_three_part(ident):
            errors.append(f"{where}.identifier: must be a 3-part name catalog.schema.name, got {ident!r}")
        elif ident in seen_ident:
            errors.append(f"{where}.identifier: duplicate {ident!r}")
        else:
            seen_ident.add(ident)

    config = doc.get("config", {})
    questions = config.get("sample_questions", []) if isinstance(config, dict) else None
    sample_ids: list[str] = []
    if questions is None:
        errors.append("config: must be an object")
    else:
        ids = sample_ids = _check_ids(questions, "config.sample_questions", errors)
        for qid, count in sorted(Counter(ids).items()):
            if count > 1:
                errors.append(f"config.sample_questions: duplicate id {qid}")
        for i, q in enumerate(questions if isinstance(questions, list) else []):
            text = q.get("question") if isinstance(q, dict) else None
            if not isinstance(text, list) or not any(str(t).strip() for t in text):
                errors.append(f"config.sample_questions[{i}].question: must be a non-empty list of strings")

    instr = doc.get("instructions", {})
    if not isinstance(instr, dict):
        errors.append("instructions: must be an object")
        instr = {}
    for key in ("text_instructions", "example_question_sqls", "join_specs"):
        if key in instr:
            _check_ids(instr[key], f"instructions.{key}", errors)
    seen_lines: set[str] = set()
    for i, ti in enumerate(instr.get("text_instructions", []) or []):
        content = ti.get("content", []) if isinstance(ti, dict) else []
        for line in content if isinstance(content, list) else [content]:
            key = _norm(str(line))
            if not key:
                continue
            if key in seen_lines:
                errors.append(f"instructions.text_instructions[{i}]: duplicate instruction {str(line).strip()!r}")
            seen_lines.add(key)
    if "benchmarks" in doc:
        errors.extend(_validate_benchmarks(doc["benchmarks"], sample_ids))
    return errors


def _validate_benchmarks(section: Any, sample_ids: Sequence[str]) -> list[str]:
    if not isinstance(section, dict):
        return ["benchmarks: must be an object"]
    questions = section.get("questions", [])
    if not isinstance(questions, list):
        return ["benchmarks.questions: must be a list"]
    errors: list[str] = []
    if len(questions) > MAX_BENCHMARK_QUESTIONS:
        errors.append(
            f"benchmarks.questions: at most {MAX_BENCHMARK_QUESTIONS} questions per agent, got {len(questions)}"
        )
    ids = _check_ids(questions, "benchmarks.questions", errors)
    for qid, count in sorted(Counter(ids).items()):
        if count > 1:
            errors.append(f"benchmarks.questions: duplicate id {qid}")
    for qid in sorted(set(ids) & set(sample_ids)):
        errors.append(f"benchmarks.questions: id {qid} is also a config.sample_questions id")
    for i, q in enumerate(questions):
        if not isinstance(q, dict):
            continue
        where = f"benchmarks.questions[{i}]"
        text = q.get("question")
        if not isinstance(text, list) or not any(str(t).strip() for t in text):
            errors.append(f"{where}.question: must be a non-empty list of strings")
        answer = q.get("answer")
        if not isinstance(answer, list) or len(answer) != 1 or not isinstance(answer[0], dict):
            errors.append(f"{where}.answer: must hold exactly one SQL answer")
            continue
        if answer[0].get("format") != "SQL":
            errors.append(f"{where}.answer[0].format: must be 'SQL', got {answer[0].get('format')!r}")
        content = answer[0].get("content")
        if not isinstance(content, list) or not any(str(c).strip() for c in content):
            errors.append(f"{where}.answer[0].content: SQL answer text must not be empty")
    return errors


# --------------------------------------------------------------------------- domain manifest


def domain_manifest(plans: Sequence[AgentPlan], descriptions: Mapping[str, str] | None = None) -> dict[str, Any]:
    """The L200-G ``domain_manifest.yml`` structure for a list of agent plans.

    A single-agent plan (no subdomain) lists every real subdomain of its metric
    views, each pointing at that same agent (metric views without a subdomain go to
    ``general``); only when no metric view has a subdomain is it listed as one
    subdomain named after the domain. ``descriptions`` maps domain or subdomain names
    to descriptions.
    """
    descriptions = descriptions or {}
    by_domain: dict[str, list[AgentPlan]] = {}
    for p in plans:
        by_domain.setdefault(p.domain, []).append(p)
    domains = []
    for dom in sorted(by_domain):
        subs = []
        for p in sorted(by_domain[dom], key=lambda x: x.name):
            for sub_name, mv_names in _manifest_subdomains(p):
                sub: dict[str, Any] = {"name": sub_name}
                if sub_name != dom and descriptions.get(sub_name):
                    sub["description"] = descriptions[sub_name]
                sub["metric_views"] = mv_names
                sub["agent"] = p.name
                if p.related_agents:
                    sub["related_agents"] = list(p.related_agents)
                subs.append(sub)
        entry: dict[str, Any] = {"name": dom}
        if descriptions.get(dom):
            entry["description"] = descriptions[dom]
        entry["subdomains"] = subs
        domains.append(entry)
    return {"domains": domains}


def _manifest_subdomains(p: AgentPlan) -> list[tuple[str, list[str]]]:
    """(subdomain, metric view names) pairs for one agent plan in the domain manifest."""
    if p.subdomain:
        return [(p.subdomain, p.mv_names)]
    if not any(mv.subdomain for mv in p.metric_views):
        return [(p.domain, p.mv_names)]
    groups: dict[str, list[str]] = {}
    for mv in p.metric_views:
        groups.setdefault(mv.subdomain or DEFAULT_SUBDOMAIN, []).append(mv.name)
    return sorted(groups.items())


def write_domain_manifest(
    plans: Sequence[AgentPlan], path: str | Path, descriptions: Mapping[str, str] | None = None
) -> dict[str, Any]:
    """Write ``domain_manifest(plans, descriptions)`` as YAML to ``path``; return the dict."""
    data = domain_manifest(plans, descriptions)
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8")
    return data


# --------------------------------------------------------------------------- rendering


def normalize_params(params: Mapping[str, Any]) -> dict[str, str]:
    """Map params to token names.

    Accepts token names (``target_catalog``, ``target_schema``, ``warehouse_id``)
    or a bundle ``variable-overrides.json`` (``catalog``, ``schema``,
    ``warehouse_id``). Explicit token names win over aliases. Non-string values
    and unrelated keys are ignored.
    """
    out: dict[str, str] = {}
    for key, value in params.items():
        token = _PARAM_ALIASES.get(key)
        if token and isinstance(value, str) and value and (token not in out or key == token):
            out[token] = value
    return out


def render_text(text: str, params: Mapping[str, Any], *, json_escape: bool = False) -> str:
    """Substitute ``${token}`` values in any string (a SQL statement for ``EXPLAIN``, a file, ...).

    ``params`` as for ``normalize_params``. Values are inserted as-is, or JSON-string
    escaped with ``json_escape=True``. Raises ``ValueError`` naming every token left
    unresolved; the result is not otherwise checked.
    """
    values = normalize_params(params)
    missing = sorted({m.group(1) for m in _TOKEN.finditer(text) if m.group(1) not in values})
    if missing:
        raise ValueError("unresolved tokens: " + ", ".join("${" + t + "}" for t in missing))
    if json_escape:
        return _TOKEN.sub(lambda m: json.dumps(values[m.group(1)])[1:-1], text)
    return _TOKEN.sub(lambda m: values[m.group(1)], text)


def render_space_text(text: str, params: Mapping[str, Any]) -> str:
    """Substitute ``${token}`` values in space JSON text (``render_text`` with JSON escaping).

    Raises ``ValueError`` naming every token left unresolved, or if the result is
    not valid JSON.
    """
    rendered = render_text(text, params, json_escape=True)
    try:
        json.loads(rendered)
    except json.JSONDecodeError as exc:
        raise ValueError(f"rendered space is not valid JSON: {exc}") from exc
    return rendered


def render_space_file(src: str | Path, dst: str | Path, params: Mapping[str, Any]) -> Path:
    """Render one tokenized ``.geniespace.json`` file to ``dst`` (parents created)."""
    src_path, dst_path = Path(src), Path(dst)
    try:
        rendered = render_space_text(src_path.read_text(encoding="utf-8"), params)
    except ValueError as exc:
        raise ValueError(f"{src_path}: {exc}") from exc
    dst_path.parent.mkdir(parents=True, exist_ok=True)
    dst_path.write_text(rendered, encoding="utf-8")
    return dst_path


def render_texts(src_dir: str | Path, params: Mapping[str, Any]) -> list[tuple[Path, str]]:
    """Render every ``*.geniespace.json`` under ``src_dir`` in memory.

    Returns ``(relative path, rendered text)`` pairs, sorted by path. Raises
    ``ValueError`` listing every failing file; nothing is written.
    """
    src_root = Path(src_dir)
    if not src_root.is_dir():
        raise ValueError(f"{src_root}: not a directory")
    files = sorted(src_root.rglob(f"*{SPACE_FILE_SUFFIX}"))
    if not files:
        raise ValueError(f"{src_root}: no *{SPACE_FILE_SUFFIX} files found")
    rendered: list[tuple[Path, str]] = []
    problems: list[str] = []
    for f in files:
        try:
            rendered.append((f.relative_to(src_root), render_space_text(f.read_text(encoding="utf-8"), params)))
        except ValueError as exc:
            problems.append(f"{f}: {exc}")
    if problems:
        raise ValueError("\n".join(problems))
    return rendered


def _write_rendered(rendered: Sequence[tuple[Path, str]], dst_dir: str | Path) -> list[Path]:
    out = []
    for rel, text in rendered:
        path = Path(dst_dir) / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        out.append(path)
    return out


def render_dir(src_dir: str | Path, dst_dir: str | Path, params: Mapping[str, Any]) -> list[Path]:
    """Render every ``*.geniespace.json`` under ``src_dir`` into ``dst_dir`` (same relative paths).

    All files are checked before any is written, so a missing token leaves
    ``dst_dir`` untouched. Raises ``ValueError`` listing every failing file.
    """
    return _write_rendered(render_texts(src_dir, params), dst_dir)


# --------------------------------------------------------------------------- identifier check


def space_identifiers(doc: Mapping[str, Any]) -> list[str]:
    """Identifiers of ``data_sources.tables`` and ``data_sources.metric_views``, in file order."""
    ds = doc.get("data_sources")
    out: list[str] = []
    if isinstance(ds, Mapping):
        for key in ("tables", "metric_views"):
            for item in ds.get(key) or []:
                if isinstance(item, Mapping) and isinstance(item.get("identifier"), str):
                    out.append(item["identifier"])
    return out


def _state(resp: Any) -> str:
    state = getattr(getattr(resp, "status", None), "state", None)
    return str(getattr(state, "value", state))


def _sql_rows(ws: Any, warehouse_id: str, statement: str, params: Mapping[str, str], wait_seconds: int) -> list[Any]:
    """Run one parameterized read-only statement; return ``result.data_array`` rows."""
    from databricks.sdk.service.sql import StatementParameterListItem

    items = [StatementParameterListItem(name=k, value=v) for k, v in params.items()]
    resp = ws.statement_execution.execute_statement(
        statement=statement, warehouse_id=warehouse_id, parameters=items, wait_timeout="30s"
    )
    deadline = time.monotonic() + wait_seconds
    while _state(resp) in ("PENDING", "RUNNING") and time.monotonic() < deadline:
        time.sleep(2)
        resp = ws.statement_execution.get_statement(resp.statement_id)
    state = _state(resp)
    if state != "SUCCEEDED":
        message = getattr(getattr(getattr(resp, "status", None), "error", None), "message", None)
        raise RuntimeError(f"information_schema query ended {state}: {message or 'no error message'}")
    return list(getattr(getattr(resp, "result", None), "data_array", None) or [])


def check_identifiers(
    identifiers: Iterable[str],
    ws: Any,
    warehouse_id: str,
    *,
    target: tuple[str, str] | None = None,
    wait_seconds: int = 120,
) -> list[str]:
    """Resolve schemas and 3-part identifiers through ``system.information_schema``.

    ``ws`` is a ``WorkspaceClient`` (or a fake with ``statement_execution``), run on
    ``warehouse_id`` with bound parameters. ``target`` = ``(catalog, schema)`` is
    checked even when no identifier names it. Returns one problem per missing schema
    or identifier (empty = everything resolves). Names compare case-insensitively.
    Raises ``RuntimeError`` if a query does not succeed.
    """
    problems: list[str] = []
    wanted: dict[tuple[str, str], set[str]] = {}
    for ident in identifiers:
        if not _is_three_part(ident) or _TOKEN.search(ident):
            problems.append(f"{ident!r}: not a resolved 3-part name")
            continue
        catalog, schema, name = (p.strip().strip("`").lower() for p in ident.split("."))
        wanted.setdefault((catalog, schema), set()).add(name)
    if target:
        wanted.setdefault((target[0].strip().lower(), target[1].strip().lower()), set())
    for (catalog, schema), names in sorted(wanted.items()):
        rows = _sql_rows(
            ws,
            warehouse_id,
            "SELECT schema_name FROM system.information_schema.schemata "
            "WHERE catalog_name = :catalog AND schema_name = :schema",
            {"catalog": catalog, "schema": schema},
            wait_seconds,
        )
        if not rows:
            problems.append(f"schema {catalog}.{schema}: not found (or not visible to this user)")
            problems.extend(f"{catalog}.{schema}.{n}: not found" for n in sorted(names))
            continue
        if not names:
            continue
        ordered = sorted(names)
        placeholders = ", ".join(f":n{i}" for i in range(len(ordered)))
        rows = _sql_rows(
            ws,
            warehouse_id,
            "SELECT table_name FROM system.information_schema.tables "
            f"WHERE table_catalog = :catalog AND table_schema = :schema AND table_name IN ({placeholders})",
            {"catalog": catalog, "schema": schema, **{f"n{i}": n for i, n in enumerate(ordered)}},
            wait_seconds,
        )
        found = {str(r[0]).lower() for r in rows if r}
        problems.extend(f"{catalog}.{schema}.{n}: not found" for n in ordered if n not in found)
    return problems


def _check_rendered(rendered: Sequence[tuple[Path, str]], params: Mapping[str, str], ws: Any) -> tuple[int, list[str]]:
    warehouse_id = params.get("warehouse_id")
    if not warehouse_id:
        raise ValueError("--check needs a warehouse_id (in --params or --warehouse-id)")
    if ws is None:
        from databricks.sdk import WorkspaceClient

        ws = WorkspaceClient()
    idents = sorted({i for _, text in rendered for i in space_identifiers(json.loads(text))})
    catalog, schema = params.get("target_catalog"), params.get("target_schema")
    target = (catalog, schema) if catalog and schema else None
    return len(idents), check_identifiers(idents, ws, warehouse_id, target=target)


# --------------------------------------------------------------------------- CLI


def main(argv: Sequence[str] | None = None, *, ws: Any = None) -> int:
    """CLI entry point. ``ws`` injects a workspace client for ``--check`` (tests)."""
    parser = argparse.ArgumentParser(prog="python -m genie_ontology_modeled_knowledge_sdk.geniespace")
    sub = parser.add_subparsers(dest="command", required=True)
    render = sub.add_parser("render", help="resolve tokens in *.geniespace.json files")
    render.add_argument("src_dir")
    render.add_argument("dst_dir")
    render.add_argument(
        "--params",
        help=(
            "JSON file: a resolved_target.json or bundle variable-overrides.json (catalog, schema, "
            "warehouse_id), or token values"
        ),
    )
    render.add_argument("--catalog", help="target catalog (overrides --params)")
    render.add_argument("--schema", help="target schema (overrides --params)")
    render.add_argument("--warehouse-id", help="SQL warehouse id (overrides --params)")
    render.add_argument(
        "--check",
        action="store_true",
        help="resolve the target schema and every identifier through information_schema; fail if any is missing",
    )
    args = parser.parse_args(argv)

    try:
        params: dict[str, str] = {}
        if args.params:
            loaded = json.loads(Path(args.params).read_text(encoding="utf-8"))
            if not isinstance(loaded, dict):
                raise ValueError(f"{args.params}: must contain a JSON object")
            params.update(normalize_params(loaded))
        for token, value in (
            ("target_catalog", args.catalog),
            ("target_schema", args.schema),
            ("warehouse_id", args.warehouse_id),
        ):
            if value:
                params[token] = value
        if not params:
            raise ValueError("give --params <json file> or --catalog / --schema / --warehouse-id")
        rendered = render_texts(args.src_dir, params)
        if args.check:
            count, problems = _check_rendered(rendered, params, ws)
            if problems:
                print("error: --check found missing objects:\n  " + "\n  ".join(problems), file=sys.stderr)
                return 1
            print(f"check: target schema and {count} identifiers resolve")
        written = _write_rendered(rendered, args.dst_dir)
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    for path in written:
        print(f"rendered {path}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
