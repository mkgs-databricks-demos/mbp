"""Genie Agent configuration builder (L200-G, Waves 6-7).

Public API (cross-session contract, see ``docs/plans/INDEX.md``):

* ``MvRef`` / ``AgentPlan``                 - inputs and outputs of agent planning
* ``plan_agents(mvs, max_per_agent=50)``    - organize metric views into agents (50-MV rule)
* ``build_space(plan, ...) -> dict``        - deterministic ``.geniespace.json`` (serialized space v2)
* ``space_to_json(doc) -> str``             - canonical JSON text (sorted keys, 2-space indent)
* ``validate_space(doc) -> list[str]``      - structural problems (empty = valid)
* ``write_domain_manifest(plans, path)``    - ``docs/domain_manifest.yml`` (L200-G shape)
* ``render_space_file(src, dst, params)``   - resolve ``${target_catalog}`` / ``${target_schema}`` /
  ``${warehouse_id}`` tokens; fails on any unresolved token
* CLI ``python -m genie_ontology_modeled_knowledge_sdk.geniespace render <src_dir> <dst_dir> --params <json file>``

Committed agent files stay tokenized (``${target_catalog}.${target_schema}.<mv>``);
the bundle (or ``render``) resolves them per target. Pure Python: no Spark, no
workspace calls.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import uuid
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import yaml

__all__ = [
    "DEFAULT_MAX_PER_AGENT",
    "MAX_DATA_SOURCES",
    "SPACE_VERSION",
    "TOKEN_IDENTIFIER_PREFIX",
    "MvRef",
    "AgentPlan",
    "mv_refs_from_manifest",
    "plan_agents",
    "stable_id",
    "build_space",
    "space_to_json",
    "validate_space",
    "domain_manifest",
    "write_domain_manifest",
    "normalize_params",
    "render_space_text",
    "render_space_file",
    "render_dir",
    "main",
]

DEFAULT_MAX_PER_AGENT = 50
SPACE_VERSION = 2
MAX_DATA_SOURCES = 30
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
    def from_dict(cls, d: Mapping[str, Any]) -> "MvRef":
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


def plan_agents(mvs: Iterable[MvRef], max_per_agent: int = DEFAULT_MAX_PER_AGENT) -> list[AgentPlan]:
    """Organize metric views into Genie Agents (L200-G organization logic).

    * ``<= max_per_agent`` metric views: one agent for the domain.
    * More: one agent per subdomain (MVs without a subdomain go to ``general``).
      Each MV lands in exactly one agent. Cross-domain MVs (domain differs from the
      primary domain) are assigned by their subdomain like any other MV. A subdomain
      that alone exceeds the limit is split into numbered agents
      (``<domain>_<subdomain>_1_agent``, ...). Split agents list each other in
      ``related_agents`` so curation can add pointer instructions.

    Output is deterministic: agents and their metric views are sorted by name.
    Raises ``ValueError`` for ``max_per_agent < 1`` or duplicate metric view names.
    """
    if not isinstance(max_per_agent, int) or max_per_agent < 1:
        raise ValueError(f"max_per_agent must be an integer >= 1, got {max_per_agent!r}")
    refs = sorted(mvs, key=lambda m: m.name)
    dupes = sorted(n for n, c in Counter(m.name for m in refs).items() if c > 1)
    if dupes:
        raise ValueError(f"duplicate metric view names: {', '.join(dupes)}")
    if not refs:
        return []

    domain = _primary_domain(refs)
    domain_slug = _slug(domain)
    if len(refs) <= max_per_agent:
        return [AgentPlan(name=f"{domain_slug}_agent", domain=domain, subdomain=None, metric_views=refs)]

    groups: dict[str, list[MvRef]] = {}
    for mv in refs:
        groups.setdefault(mv.subdomain or DEFAULT_SUBDOMAIN, []).append(mv)

    plans: list[AgentPlan] = []
    for sub in sorted(groups):
        parts = _chunks(groups[sub], max_per_agent)
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
        instructions["text_instructions"] = [
            {"id": stable_id("text_instructions", plan.name), "content": lines}
        ]

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
    return _sort_keys(doc)


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
    (whitespace- and case-insensitive).
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
        ident = src.get("identifier") if isinstance(src, dict) else None
        if not _is_three_part(ident):
            errors.append(f"{where}.identifier: must be a 3-part name catalog.schema.name, got {ident!r}")
        elif ident in seen_ident:
            errors.append(f"{where}.identifier: duplicate {ident!r}")
        else:
            seen_ident.add(ident)

    config = doc.get("config", {})
    questions = config.get("sample_questions", []) if isinstance(config, dict) else None
    if questions is None:
        errors.append("config: must be an object")
    else:
        ids = _check_ids(questions, "config.sample_questions", errors)
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
    return errors


# --------------------------------------------------------------------------- domain manifest


def domain_manifest(
    plans: Sequence[AgentPlan], descriptions: Mapping[str, str] | None = None
) -> dict[str, Any]:
    """The L200-G ``domain_manifest.yml`` structure for a list of agent plans.

    A single-agent plan (no subdomain) is listed as one subdomain named after the
    domain. ``descriptions`` maps domain or subdomain names to descriptions.
    """
    descriptions = descriptions or {}
    by_domain: dict[str, list[AgentPlan]] = {}
    for p in plans:
        by_domain.setdefault(p.domain, []).append(p)
    domains = []
    for dom in sorted(by_domain):
        subs = []
        for p in sorted(by_domain[dom], key=lambda x: x.name):
            sub_name = p.subdomain or dom
            sub: dict[str, Any] = {"name": sub_name}
            if p.subdomain and descriptions.get(p.subdomain):
                sub["description"] = descriptions[p.subdomain]
            sub["metric_views"] = p.mv_names
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


def render_space_text(text: str, params: Mapping[str, Any]) -> str:
    """Substitute ``${token}`` values in space JSON text.

    Values are JSON-string escaped. Raises ``ValueError`` naming every token left
    unresolved, or if the result is not valid JSON.
    """
    values = normalize_params(params)
    missing = sorted({m.group(1) for m in _TOKEN.finditer(text) if m.group(1) not in values})
    if missing:
        raise ValueError("unresolved tokens: " + ", ".join("${" + t + "}" for t in missing))
    rendered = _TOKEN.sub(lambda m: json.dumps(values[m.group(1)])[1:-1], text)
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


def render_dir(src_dir: str | Path, dst_dir: str | Path, params: Mapping[str, Any]) -> list[Path]:
    """Render every ``*.geniespace.json`` under ``src_dir`` into ``dst_dir`` (same relative paths).

    All files are checked before any is written, so a missing token leaves
    ``dst_dir`` untouched. Raises ``ValueError`` listing every failing file.
    """
    src_root, dst_root = Path(src_dir), Path(dst_dir)
    if not src_root.is_dir():
        raise ValueError(f"{src_root}: not a directory")
    files = sorted(src_root.rglob(f"*{SPACE_FILE_SUFFIX}"))
    if not files:
        raise ValueError(f"{src_root}: no *{SPACE_FILE_SUFFIX} files found")
    rendered: list[tuple[Path, str]] = []
    problems: list[str] = []
    for f in files:
        try:
            rendered.append((dst_root / f.relative_to(src_root), render_space_text(f.read_text(encoding="utf-8"), params)))
        except ValueError as exc:
            problems.append(f"{f}: {exc}")
    if problems:
        raise ValueError("\n".join(problems))
    out = []
    for path, text in rendered:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        out.append(path)
    return out


# --------------------------------------------------------------------------- CLI


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m genie_ontology_modeled_knowledge_sdk.geniespace")
    sub = parser.add_subparsers(dest="command", required=True)
    render = sub.add_parser("render", help="resolve tokens in *.geniespace.json files")
    render.add_argument("src_dir")
    render.add_argument("dst_dir")
    render.add_argument(
        "--params",
        required=True,
        help="JSON file: token values, or a bundle variable-overrides.json (catalog, schema, warehouse_id)",
    )
    args = parser.parse_args(argv)

    try:
        params = json.loads(Path(args.params).read_text(encoding="utf-8"))
        if not isinstance(params, dict):
            raise ValueError(f"{args.params}: must contain a JSON object")
        written = render_dir(args.src_dir, args.dst_dir, params)
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    for path in written:
        print(f"rendered {path}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
