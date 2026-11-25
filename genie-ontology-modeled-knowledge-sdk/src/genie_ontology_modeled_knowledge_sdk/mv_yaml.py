"""Metric view YAML: load, parameter substitution, static validation, DDL rendering.

Metric view YAML files in an ontology project are parameterized: table
references use the tokens ``${source_catalog}``, ``${source_schema}``,
``${target_catalog}`` and ``${target_schema}``, which are substituted at
registration time (the catalog is the environment discriminator).

Static rules (``validate_mv``):

* ``MV001`` required keys and well-formed structure (error)
* ``MV002`` unique dimension / measure / join / parameter names (error)
* ``MV003`` no wildcard or implicit (unnamed) fields, no ``SELECT *`` (error)
* ``MV004`` parameterized ``source:`` and ``joins[].source`` (error)
* ``MV005`` every join has ``on`` / ``using`` (error); a join with
  ``rely.at_most_one_match`` carries a ``# verified:`` comment or a
  ``verified_cardinality`` field from EDA (warning)
* ``MV006`` every measure has a ``comment`` (warning)
* ``MV007`` a ``materialization`` block has ``refresh_policy`` on every
  materialized view and lists only categorical dimensions (error)

CLI (used by session 11 and the wave gates)::

    python -m genie_ontology_modeled_knowledge_sdk.mv_yaml validate <dir-or-file>

prints findings and exits 1 when any error is found.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable, Iterator, Mapping

import yaml

__all__ = [
    "PARAMETER_NAMES",
    "Finding",
    "load_mv",
    "load_mv_text",
    "substitute",
    "find_tokens",
    "validate_mv",
    "validate_file",
    "validate_path",
    "has_errors",
    "render_ddl",
    "strip_sdk_only_keys",
    "iter_mv_files",
    "main",
]

#: Registration-time parameters a metric view YAML may reference.
PARAMETER_NAMES = ("source_catalog", "source_schema", "target_catalog", "target_schema")

TOKEN_RE = re.compile(r"\$\{([^}]*)\}")
# A parameter value is spliced into SQL, so it must be a plain identifier or a
# backtick-quoted identifier (no backticks inside).
_SAFE_VALUE_RE = re.compile(r"^(?:[A-Za-z_][A-Za-z0-9_]*|`[^`]+`)$")
_MV_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_IDENT_PART = r"(?:[A-Za-z_][A-Za-z0-9_]*|`[^`]+`|\$\{[A-Za-z_][A-Za-z0-9_]*\})"
_FQ_NAME_RE = re.compile(rf"^{_IDENT_PART}\.{_IDENT_PART}\.{_IDENT_PART}$")

ALLOWED_VERSIONS = ("0.1", "1.1")
TOP_LEVEL_KEYS = {
    "version", "source", "comment", "filter", "joins", "dimensions", "fields",
    "measures", "materialization", "parameters",
}
COLUMN_KEYS = {"name", "expr", "comment", "display_name", "format", "synonyms", "window", "partition"}
REFRESH_POLICIES = ("auto", "incremental", "incremental strict", "full")
MATERIALIZATION_TYPES = ("aggregated", "unaggregated")
#: ``format.type`` values that mark a continuous (non-categorical) dimension.
CONTINUOUS_FORMATS = ("number", "currency", "percentage", "byte")
#: SDK-only keys (EDA evidence) that are stripped before registration.
SDK_ONLY_KEYS = ("verified_cardinality",)
MV_SUFFIXES = (".yml", ".yaml")

_SQL_SOURCE_RE = re.compile(r"^\s*(select|with)\b", re.IGNORECASE)
_SQL_TABLE_REF_RE = re.compile(r"\b(?:from|join)\s+([^\s,()]+)", re.IGNORECASE)
_SQL_CTE_RE = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*)\s+as\s*\(", re.IGNORECASE)
_SQL_STAR_RE = re.compile(r"\bselect\s+(?:distinct\s+)?(?:[A-Za-z_][A-Za-z0-9_]*\.)?\*|,\s*(?:[A-Za-z_][A-Za-z0-9_]*\.)?\*\s*(?:,|\bfrom\b)", re.IGNORECASE)
_WILDCARD_EXPR_RE = re.compile(r"(?:^|\.)\*(?:\s|$)")
# order_id, Customer ID, key, and TPC-H style surrogate keys (o_orderkey, c_custkey)
_IDENTIFIER_SUFFIX_RE = re.compile(r"(?:^|[_\s])id$|key$", re.IGNORECASE)
_IDENTIFIER_CAMEL_RE = re.compile(r"[a-z0-9](?:Id|Key|ID)$")  # customerId (case-sensitive: not 'paid')


def _identifier_like(value: str) -> bool:
    return bool(_IDENTIFIER_SUFFIX_RE.search(value) or _IDENTIFIER_CAMEL_RE.search(value))


_VERIFIED_COMMENT_RE = re.compile(r"#\s*verified\s*:", re.IGNORECASE)


@dataclass(frozen=True)
class Finding:
    """One validation finding: ``{rule, severity: error|warning, message}``."""

    rule: str
    severity: str
    message: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)

    def __getitem__(self, key: str) -> str:  # dict-style access: f["rule"]
        return getattr(self, key)

    def __str__(self) -> str:
        return f"{self.severity.upper()} {self.rule}: {self.message}"


def _err(rule: str, message: str) -> Finding:
    return Finding(rule, "error", message)


def _warn(rule: str, message: str) -> Finding:
    return Finding(rule, "warning", message)


def has_errors(findings: Iterable[Finding]) -> bool:
    return any(f.severity == "error" for f in findings)


# --------------------------------------------------------------------------- load

class _MvLoader(yaml.SafeLoader):
    """SafeLoader with YAML 1.2 booleans: only true/false (any case) are booleans.

    PyYAML follows YAML 1.1, where ``on`` / ``off`` / ``yes`` / ``no`` are
    booleans, so the join key ``on:`` would load as ``True``.
    """


_MvLoader.yaml_implicit_resolvers = {
    first: [(tag, regexp) for tag, regexp in resolvers if tag != "tag:yaml.org,2002:bool"]
    for first, resolvers in yaml.SafeLoader.yaml_implicit_resolvers.items()
}
_MvLoader.add_implicit_resolver(
    "tag:yaml.org,2002:bool",
    re.compile(r"^(?:true|True|TRUE|false|False|FALSE)$"),
    list("tTfF"),
)


def load_mv_text(text: str) -> dict:
    """Parse metric view YAML text (unsubstituted tokens are fine). Raises ``ValueError``.

    Uses YAML 1.2 boolean rules so ``on:`` stays a string key.
    """
    try:
        doc = yaml.load(text, Loader=_MvLoader)  # noqa: S506 - SafeLoader subclass
    except yaml.YAMLError as exc:
        raise ValueError(f"invalid YAML: {exc}") from exc
    if not isinstance(doc, dict):
        raise ValueError("metric view YAML must be a mapping at the top level")
    return doc


def load_mv(path: str | Path) -> dict:
    """Load one metric view YAML file into a dict (tokens are not substituted)."""
    return load_mv_text(Path(path).read_text(encoding="utf-8"))


# --------------------------------------------------------------------- substitute

def find_tokens(text: str) -> list[str]:
    """Distinct ``${...}`` token names in ``text``, in first-seen order."""
    seen: dict[str, None] = {}
    for m in TOKEN_RE.finditer(text):
        seen.setdefault(m.group(1), None)
    return list(seen)


def substitute(text: str, params: Mapping[str, str]) -> str:
    """Replace ``${name}`` tokens with ``params[name]``.

    Raises ``ValueError`` if any ``${...}`` token is left unresolved (including
    malformed ones such as ``${}`` or ``${ x }``), or if a value used for
    substitution is not a safe SQL identifier (plain or backtick-quoted).
    Substitution is single-pass: values are never re-scanned for tokens.
    """
    used = [t for t in find_tokens(text) if t in params]
    bad = [t for t in used if not isinstance(params[t], str) or not _SAFE_VALUE_RE.match(params[t])]
    if bad:
        raise ValueError(
            "unsafe parameter value(s) for " + ", ".join(f"${{{t}}}" for t in bad)
            + ": values must be identifiers ([A-Za-z_][A-Za-z0-9_]*) or backtick-quoted"
        )
    unresolved: dict[str, None] = {}

    def repl(m: re.Match) -> str:
        key = m.group(1)
        if key in params:
            return params[key]
        unresolved.setdefault(key, None)
        return m.group(0)

    out = TOKEN_RE.sub(repl, text)
    if unresolved:
        raise ValueError("unresolved parameter(s): " + ", ".join(f"${{{t}}}" for t in unresolved))
    if "${" in out:  # e.g. an unterminated "${source_catalog"
        raise ValueError("unresolved parameter: unterminated '${' in text")
    return out


# ----------------------------------------------------------------------- helpers

def _columns(doc: Mapping) -> tuple[str, list]:
    """Return (key, entries) for dimensions (``fields`` is an alias)."""
    key = "fields" if "fields" in doc and "dimensions" not in doc else "dimensions"
    value = doc.get(key)
    return key, value if isinstance(value, list) else []


def _measures(doc: Mapping) -> list:
    value = doc.get("measures")
    return value if isinstance(value, list) else []


def _iter_joins(joins: Any, prefix: str = "joins") -> Iterator[tuple[str, Any]]:
    """Yield (label, join) for every join, including nested snowflake joins."""
    if not isinstance(joins, list):
        return
    for i, join in enumerate(joins):
        label = f"{prefix}[{i}]"
        if isinstance(join, dict) and join.get("name"):
            label = f"{label} '{join['name']}'"
        yield label, join
        if isinstance(join, dict) and "joins" in join:
            yield from _iter_joins(join["joins"], f"{label}.joins")


def _version_str(value: Any) -> str | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, int):
        return str(value)  # bare integer: rejected below (e.g. "1")
    if isinstance(value, float):
        return repr(value)
    if isinstance(value, str):
        return value.strip()
    return None


def _is_token(part: str) -> bool:
    return bool(TOKEN_RE.fullmatch(part))


# ------------------------------------------------------------------------- rules

def _rule_mv001(doc: Mapping, name: str) -> list[Finding]:
    out: list[Finding] = []
    if not name or not _MV_NAME_RE.match(name):
        out.append(_err("MV001", f"metric view name {name!r} must be an identifier ([A-Za-z_][A-Za-z0-9_]*)"))
    unknown = sorted(set(doc) - TOP_LEVEL_KEYS)
    if unknown:
        out.append(_err("MV001", f"unknown top-level key(s): {', '.join(map(str, unknown))}"))
    if "version" not in doc:
        out.append(_err("MV001", "missing required key 'version' (use 1.1)"))
    else:
        v = _version_str(doc["version"])
        if v not in ALLOWED_VERSIONS:
            out.append(_err("MV001", f"invalid version {doc['version']!r}: use 1.1"))
    source = doc.get("source")
    if not isinstance(source, str) or not source.strip():
        out.append(_err("MV001", "missing required key 'source' (a table reference or SQL query)"))
    if "dimensions" in doc and "fields" in doc:
        out.append(_err("MV001", "use either 'dimensions' or its alias 'fields', not both"))
    dim_key, dims = _columns(doc)
    measures = _measures(doc)
    if not dims and not measures:
        out.append(_err("MV001", "at least one of 'dimensions' (or 'fields') or 'measures' must be a non-empty list"))
    for key in (dim_key, "measures"):
        if key in doc and not isinstance(doc[key], list):
            out.append(_err("MV001", f"'{key}' must be a list"))
    for key, entries in ((dim_key, dims), ("measures", measures)):
        for i, col in enumerate(entries):
            where = f"{key}[{i}]"
            if not isinstance(col, dict):
                out.append(_err("MV001", f"{where} must be a mapping with 'expr'"))
                continue
            expr = col.get("expr")
            if not isinstance(expr, str) or not expr.strip():
                out.append(_err("MV001", f"{where} ({col.get('name', '?')}) is missing 'expr'"))
            if "name" in col and (not isinstance(col["name"], str) or not col["name"].strip()):
                out.append(_err("MV001", f"{where} has an empty or non-string 'name'"))
            extra = sorted(set(col) - COLUMN_KEYS)
            if extra:
                out.append(_warn("MV001", f"{where} ({col.get('name', '?')}) has unrecognized key(s): {', '.join(map(str, extra))}"))
    if "joins" in doc and not isinstance(doc["joins"], list):
        out.append(_err("MV001", "'joins' must be a list"))
    for label, join in _iter_joins(doc.get("joins")):
        if not isinstance(join, dict):
            out.append(_err("MV001", f"{label} must be a mapping"))
            continue
        for req in ("name", "source"):
            if not isinstance(join.get(req), str) or not join[req].strip():
                out.append(_err("MV001", f"{label} is missing '{req}'"))
    return out


def _rule_mv002(doc: Mapping) -> list[Finding]:
    out: list[Finding] = []
    seen: dict[str, str] = {}
    dim_key, dims = _columns(doc)
    for key, entries in ((dim_key, dims), ("measures", _measures(doc))):
        for col in entries:
            if isinstance(col, dict) and isinstance(col.get("name"), str):
                low = col["name"].strip().lower()
                if low in seen:
                    out.append(_err("MV002", f"duplicate name {col['name']!r} in {key} (already used in {seen[low]}); names are case-insensitive"))
                else:
                    seen[low] = key
    join_names: set[str] = set()
    for label, join in _iter_joins(doc.get("joins")):
        if isinstance(join, dict) and isinstance(join.get("name"), str):
            low = join["name"].lower()
            if low in join_names or low == "source":
                out.append(_err("MV002", f"{label}: join name {join['name']!r} is duplicated or reserved"))
            join_names.add(low)
    params = doc.get("parameters")
    if isinstance(params, list):
        for p in params:
            if isinstance(p, dict) and isinstance(p.get("name"), str):
                low = p["name"].lower()
                if low in seen or low == "source":
                    out.append(_err("MV002", f"parameter name {p['name']!r} collides with a column name or is reserved"))
    return out


def _rule_mv003(doc: Mapping) -> list[Finding]:
    out: list[Finding] = []
    dim_key, dims = _columns(doc)
    for key, entries in ((dim_key, dims), ("measures", _measures(doc))):
        for i, col in enumerate(entries):
            if not isinstance(col, dict):
                continue
            expr = col.get("expr")
            if isinstance(expr, str) and _WILDCARD_EXPR_RE.search(expr.strip()):
                out.append(_err("MV003", f"{key}[{i}] uses a wildcard expression {expr!r}; declare each field explicitly"))
            elif "name" not in col:
                out.append(_err("MV003", f"{key}[{i}] (expr {expr!r}) has no 'name'; implicit (derived) names are not allowed"))
    sources = [("source", doc.get("source"))] + [
        (f"{label}.source", j.get("source")) for label, j in _iter_joins(doc.get("joins")) if isinstance(j, dict)
    ]
    for where, src in sources:
        if isinstance(src, str) and _SQL_SOURCE_RE.match(src) and _SQL_STAR_RE.search(src):
            out.append(_err("MV003", f"{where} SQL selects '*'; list the columns explicitly"))
    return out


def _table_refs(source: str) -> list[str]:
    """Table references in a ``source`` value (a table name or a SQL query)."""
    src = source.strip()
    if not _SQL_SOURCE_RE.match(src):
        return [src]
    ctes = {m.group(1).lower() for m in _SQL_CTE_RE.finditer(src)}
    refs = []
    for m in _SQL_TABLE_REF_RE.finditer(src):
        ref = m.group(1).rstrip(";")
        if ref.lower() in ctes or ref.lower() in ("select", "lateral"):
            continue
        refs.append(ref)
    return refs


def _check_ref(where: str, ref: str) -> list[Finding]:
    out: list[Finding] = []
    for tok in find_tokens(ref):
        if tok not in PARAMETER_NAMES:
            out.append(_err("MV004", f"{where}: unknown parameter ${{{tok}}} in {ref!r}; allowed: " + ", ".join(f"${{{p}}}" for p in PARAMETER_NAMES)))
    parts = ref.split(".")
    if len(parts) != 3:
        out.append(_err("MV004", f"{where}: {ref!r} must be a 3-part name like ${{source_catalog}}.${{source_schema}}.<table>"))
        return out
    if not _is_token(parts[0]):
        out.append(_err("MV004", f"{where}: hardcoded catalog {parts[0]!r} in {ref!r}; use ${{source_catalog}} (or ${{target_catalog}} for a metric view source)"))
    if not _is_token(parts[1]):
        out.append(_warn("MV004", f"{where}: literal schema {parts[1]!r} in {ref!r}; prefer ${{source_schema}}"))
    return out


def _rule_mv004(doc: Mapping) -> list[Finding]:
    out: list[Finding] = []
    sources = [("source", doc.get("source"))] + [
        (f"{label}.source", j.get("source")) for label, j in _iter_joins(doc.get("joins")) if isinstance(j, dict)
    ]
    for where, src in sources:
        if not isinstance(src, str) or not src.strip():
            continue  # MV001 reports missing sources
        refs = _table_refs(src)
        if not refs:
            out.append(_err("MV004", f"{where}: no table reference found in SQL source"))
        for ref in refs:
            out.extend(_check_ref(where, ref))
    return out


def _join_block_has_verified_comment(text: str, join_name: str) -> bool:
    """True if the YAML list item for ``join_name`` (or the line above it) has a ``# verified:`` comment."""
    lines = text.splitlines()
    item_re = re.compile(r"^(\s*)-\s+name\s*:\s*[\"']?" + re.escape(join_name) + r"[\"']?\s*(#.*)?$")
    for i, line in enumerate(lines):
        m = item_re.match(line)
        if not m:
            continue
        indent = len(m.group(1))
        if _VERIFIED_COMMENT_RE.search(line):
            return True
        if i > 0 and lines[i - 1].strip().startswith("#") and _VERIFIED_COMMENT_RE.search(lines[i - 1]):
            return True
        for nxt in lines[i + 1:]:
            stripped = nxt.strip()
            if not stripped:
                continue
            nxt_indent = len(nxt) - len(nxt.lstrip())
            if nxt_indent <= indent and not stripped.startswith("#"):
                break
            if re.match(r"joins\s*:", stripped):
                break  # evidence inside nested joins belongs to those joins
            if _VERIFIED_COMMENT_RE.search(nxt):
                return True
    return False


def _rule_mv005(doc: Mapping, text: str | None) -> list[Finding]:
    out: list[Finding] = []
    for label, join in _iter_joins(doc.get("joins")):
        if not isinstance(join, dict):
            continue
        on = join.get("on", join.get(True))  # True: parsed by a YAML 1.1 loader (yaml.safe_load)
        has_on = isinstance(on, str) and on.strip()
        has_using = isinstance(join.get("using"), list) and len(join["using"]) > 0
        if not has_on and not has_using:
            out.append(_err("MV005", f"{label} has no 'on' condition or 'using' column list"))
        if has_on and has_using:
            out.append(_err("MV005", f"{label} sets both 'on' and 'using'; use one"))
        rely = join.get("rely")
        if isinstance(rely, dict) and rely.get("at_most_one_match"):
            if join.get("verified_cardinality"):
                continue
            jname = join.get("name")
            if text is not None and isinstance(jname, str) and _join_block_has_verified_comment(text, jname):
                continue
            out.append(_warn(
                "MV005",
                f"{label} sets rely.at_most_one_match without EDA evidence; add a '# verified: <query/result>' comment "
                "or a 'verified_cardinality' field from the data model summary",
            ))
    return out


def _rule_mv006(doc: Mapping) -> list[Finding]:
    out: list[Finding] = []
    for i, col in enumerate(_measures(doc)):
        if isinstance(col, dict):
            comment = col.get("comment")
            if not isinstance(comment, str) or not comment.strip():
                out.append(_warn("MV006", f"measures[{i}] ({col.get('name', '?')}) has no 'comment'"))
    return out


def _is_categorical(col: Mapping) -> str | None:
    """Return a reason the dimension is not categorical, or None."""
    fmt = col.get("format")
    if isinstance(fmt, dict) and str(fmt.get("type", "")).lower() in CONTINUOUS_FORMATS:
        return f"format type '{fmt.get('type')}' is continuous"
    if col.get("window") is not None:
        return "it is a window expression"
    name = str(col.get("name", ""))
    expr = str(col.get("expr", "")).strip()
    last = expr.split(".")[-1].strip("`") if re.fullmatch(r"[\w.`]+", expr) else ""
    if _identifier_like(name) or (last and _identifier_like(last)):
        return "it looks like a unique identifier (id/key)"
    return None


def _rule_mv007(doc: Mapping) -> list[Finding]:
    if "materialization" not in doc:
        return []
    out: list[Finding] = []
    mat = doc["materialization"]
    if not isinstance(mat, dict):
        return [_err("MV007", "'materialization' must be a mapping")]
    if doc.get("parameters"):
        out.append(_err("MV007", "materialization is not supported on a metric view with 'parameters'"))
    if str(mat.get("mode", "")).lower() != "relaxed":
        out.append(_err("MV007", "materialization.mode must be 'relaxed'"))
    mvs = mat.get("materialized_views")
    if not isinstance(mvs, list) or not mvs:
        return out + [_err("MV007", "materialization.materialized_views must be a non-empty list")]
    _, dims = _columns(doc)
    dims_by_name = {c["name"]: c for c in dims if isinstance(c, dict) and isinstance(c.get("name"), str)}
    measure_names = {c["name"] for c in _measures(doc) if isinstance(c, dict) and isinstance(c.get("name"), str)}
    version = _version_str(doc.get("version"))
    unaggregated = 0
    for i, entry in enumerate(mvs):
        where = f"materialized_views[{i}]"
        if not isinstance(entry, dict):
            out.append(_err("MV007", f"{where} must be a mapping"))
            continue
        if entry.get("name"):
            where = f"{where} '{entry['name']}'"
        else:
            out.append(_err("MV007", f"{where} is missing 'name'"))
        mtype = str(entry.get("type", "")).lower()
        if mtype not in MATERIALIZATION_TYPES:
            out.append(_err("MV007", f"{where}: type must be one of {', '.join(MATERIALIZATION_TYPES)}"))
        policy = entry.get("refresh_policy")
        if policy is None:
            out.append(_err("MV007", f"{where} is missing 'refresh_policy' (use auto)"))
        elif str(policy).strip().lower() not in REFRESH_POLICIES:
            out.append(_err("MV007", f"{where}: refresh_policy {policy!r} must be one of {', '.join(REFRESH_POLICIES)}"))
        elif version != "1.1":
            out.append(_err("MV007", f"{where}: refresh_policy requires version 1.1"))
        if "cluster_by" in entry and "partition_by" in entry:
            out.append(_err("MV007", f"{where}: use cluster_by or partition_by, not both"))
        if mtype == "unaggregated":
            unaggregated += 1
            if entry.get("dimensions") or entry.get("measures"):
                out.append(_err("MV007", f"{where}: an unaggregated materialization does not list dimensions or measures"))
            continue
        listed_dims = entry.get("dimensions") or []
        listed_measures = entry.get("measures") or []
        if mtype == "aggregated" and not listed_dims and not listed_measures:
            out.append(_err("MV007", f"{where}: an aggregated materialization needs dimensions, measures or both"))
        if not isinstance(listed_dims, list):
            out.append(_err("MV007", f"{where}: dimensions must be a list"))
            listed_dims = []
        for d in listed_dims:
            d = str(d)
            if d.strip().startswith("*"):
                out.append(_err("MV007", f"{where}: dimensions {d!r} is a wildcard; list the categorical dimensions explicitly"))
            elif d in dims_by_name:
                reason = _is_categorical(dims_by_name[d])
                if reason:
                    out.append(_err("MV007", f"{where}: dimension {d!r} is not categorical ({reason})"))
            elif d in measure_names:
                out.append(_err("MV007", f"{where}: {d!r} is a measure, not a dimension"))
            else:
                out.append(_err("MV007", f"{where}: unknown dimension {d!r}"))
        if not isinstance(listed_measures, list):
            out.append(_err("MV007", f"{where}: measures must be a list"))
            listed_measures = []
        for m in listed_measures:
            m = str(m)
            if not m.strip().startswith("*") and m not in measure_names:
                out.append(_err("MV007", f"{where}: unknown measure {m!r}"))
    if unaggregated > 1:
        out.append(_err("MV007", "only one unaggregated materialization is allowed"))
    return out


def validate_mv(doc: Mapping | str, *, name: str, text: str | None = None) -> list[Finding]:
    """Validate a metric view document against rules MV001-MV007.

    ``doc`` is the parsed YAML (from ``load_mv``) or the raw YAML text. Pass
    the raw ``text`` as well when ``doc`` is a dict so MV005 can see
    ``# verified:`` comments (``validate_file`` does this). ``name`` is the
    metric view name (normally the file stem).
    """
    if isinstance(doc, str):
        text = doc
        try:
            doc = load_mv_text(doc)
        except ValueError as exc:
            return [_err("MV001", str(exc))]
    if not isinstance(doc, Mapping):
        return [_err("MV001", "metric view YAML must be a mapping at the top level")]
    findings: list[Finding] = []
    findings += _rule_mv001(doc, name)
    findings += _rule_mv002(doc)
    findings += _rule_mv003(doc)
    findings += _rule_mv004(doc)
    findings += _rule_mv005(doc, text)
    findings += _rule_mv006(doc)
    findings += _rule_mv007(doc)
    return findings


def validate_file(path: str | Path) -> list[Finding]:
    """Validate one YAML file; the metric view name is the file stem."""
    p = Path(path)
    try:
        text = p.read_text(encoding="utf-8")
    except OSError as exc:
        return [_err("MV001", f"cannot read file: {exc}")]
    return validate_mv(text, name=p.stem)


def iter_mv_files(root: str | Path) -> list[Path]:
    """Metric view YAML files under ``root`` (recursive, sorted), or ``[root]`` for a file."""
    r = Path(root)
    if r.is_file():
        return [r]
    return sorted(p for p in r.rglob("*") if p.is_file() and p.suffix.lower() in MV_SUFFIXES)


def validate_path(root: str | Path) -> dict[Path, list[Finding]]:
    """Validate every metric view YAML under ``root``.

    Adds a cross-file ``MV002`` error when two files share a metric view name
    (the file stem), since they would register to the same view.
    """
    results: dict[Path, list[Finding]] = {}
    by_name: dict[str, Path] = {}
    for path in iter_mv_files(root):
        findings = validate_file(path)
        stem = path.stem.lower()
        if stem in by_name:
            findings.append(_err("MV002", f"metric view name {path.stem!r} is also defined in {by_name[stem]}"))
        else:
            by_name[stem] = path
        results[path] = findings
    return results


# ------------------------------------------------------------------------ render

def strip_sdk_only_keys(text: str) -> str:
    """Remove SDK-only evidence keys (``verified_cardinality: ...`` lines) that the
    metric view YAML spec does not accept. Comments and layout are preserved."""
    pattern = re.compile(r"^[ \t]*(?:" + "|".join(SDK_ONLY_KEYS) + r")[ \t]*:[^\n]*\n?", re.MULTILINE)
    return pattern.sub("", text)


def render_ddl(doc_text: str, fq_name: str, params: Mapping[str, str]) -> str:
    """Render ``CREATE OR REPLACE VIEW <fq> WITH METRICS LANGUAGE YAML AS $$ ... $$``.

    ``doc_text`` is the raw YAML text; tokens in it and in ``fq_name`` are
    substituted with ``params`` (unresolved tokens raise ``ValueError``).
    SDK-only keys are stripped. ``fq_name`` must resolve to a 3-part name.
    """
    fq = substitute(fq_name, params).strip()
    if not _FQ_NAME_RE.match(fq) or "${" in fq:
        raise ValueError(f"fq_name {fq!r} must be a 3-part name catalog.schema.view")
    body = strip_sdk_only_keys(substitute(doc_text, params))
    if "$$" in body:
        raise ValueError("metric view YAML must not contain '$$' (it ends the DDL body)")
    load_mv_text(body)  # the substituted body must still be valid YAML
    if not body.endswith("\n"):
        body += "\n"
    return f"CREATE OR REPLACE VIEW {fq}\nWITH METRICS\nLANGUAGE YAML\nAS $$\n{body}$$"


# --------------------------------------------------------------------------- CLI

def _cmd_validate(args: argparse.Namespace) -> int:
    root = Path(args.path)
    if not root.exists():
        print(f"error: {root} does not exist", file=sys.stderr)
        return 2
    results = validate_path(root)
    if not results:
        print(f"error: no metric view YAML files (*.yml, *.yaml) under {root}", file=sys.stderr)
        return 1
    n_err = n_warn = 0
    for path, findings in results.items():
        for f in findings:
            if f.severity == "error":
                n_err += 1
            else:
                n_warn += 1
            if f.severity == "error" or not args.quiet:
                print(f"{path}: {f}")
    print(f"{len(results)} file(s) checked: {n_err} error(s), {n_warn} warning(s)")
    return 1 if n_err else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m genie_ontology_modeled_knowledge_sdk.mv_yaml", description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    p_val = sub.add_parser("validate", help="validate metric view YAML files (rules MV001-MV007)")
    p_val.add_argument("path", help="a directory (searched recursively) or a single YAML file")
    p_val.add_argument("--quiet", action="store_true", help="print errors only")
    p_val.set_defaults(func=_cmd_validate)
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
