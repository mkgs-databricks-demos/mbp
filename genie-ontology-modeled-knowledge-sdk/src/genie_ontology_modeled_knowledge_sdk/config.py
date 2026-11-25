"""Input contract for a Genie Ontology Modeled Knowledge SDK run (``sdk_config.json``).

Public API (cross-session contract, see ``docs/plans/INDEX.md``):

* ``SdkConfig``                         - typed view of a validated config
* ``load_config(path) -> SdkConfig``    - read JSON (or YAML) and validate
* ``config_from_dict(d) -> SdkConfig``  - validate a dict and apply defaults
* ``validate_config(d) -> list[str]``   - schema + name-shape problems (empty = valid); emits a
  ``UserWarning`` for each ``config_warnings(d)`` item
* ``config_warnings(d) -> list[str]``   - non-fatal advice (``max_metric_views_per_agent`` above 30)
* ``check_access(cfg, ws) -> list[str]`` - L200-A Unity Catalog / volume checks; never raises
* ``expand_tables(cfg, ws) -> list[str]`` - catalogs/schemas/tables -> sorted unique 3-part names

Pure Python: no Spark imports. Databricks access goes through an injected
``WorkspaceClient`` (or any object with the same ``catalogs`` / ``schemas`` /
``tables`` / ``files`` surface), so tests can pass a fake.
"""

from __future__ import annotations

import json
import warnings
from collections.abc import Iterable
from dataclasses import dataclass, field, fields
from functools import lru_cache
from importlib import resources
from pathlib import Path
from typing import Any

import jsonschema
import yaml

__all__ = [
    "DEFAULT_MAX_METRIC_VIEWS_PER_AGENT",
    "AGENT_DATA_SOURCE_LIMIT",
    "SdkConfig",
    "load_schema",
    "load_config",
    "config_from_dict",
    "validate_config",
    "config_warnings",
    "check_access",
    "expand_tables",
]

DEFAULT_MAX_METRIC_VIEWS_PER_AGENT = 50
# Most data sources one Genie Agent holds (= geniespace.MAX_DATA_SOURCES; kept here so
# config does not import geniespace). plan_agents never splits above it.
AGENT_DATA_SOURCE_LIMIT = 30
SOURCE_KEYS = ("source_catalogs", "source_schemas", "source_tables")
_SYSTEM_SCHEMAS = {"information_schema"}


@lru_cache(maxsize=1)
def load_schema() -> dict[str, Any]:
    """Return the JSON Schema (draft 2020-12) for ``sdk_config.json``."""
    text = (
        resources.files("genie_ontology_modeled_knowledge_sdk")
        .joinpath("schemas", "sdk_config.schema.json")
        .read_text(encoding="utf-8")
    )
    return json.loads(text)


@dataclass
class SdkConfig:
    """Validated SDK inputs (L100 Inputs & Interface Contract)."""

    target_catalog: str
    target_schema: str
    domain_name: str
    domain_context: str
    source_catalogs: list[str] = field(default_factory=list)
    source_schemas: list[str] = field(default_factory=list)
    source_tables: list[str] = field(default_factory=list)
    supplemental_volume_dirs: list[str] = field(default_factory=list)
    dashboard_inputs: list[str] = field(default_factory=list)
    source_catalog_for_reads: str | None = None
    source_schema_for_reads: str | None = None
    warehouse_id: str | None = None
    max_metric_views_per_agent: int = DEFAULT_MAX_METRIC_VIEWS_PER_AGENT
    project_root: str | None = None
    repo_path: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a ``sdk_config.json``-shaped dict.

        ``None`` values and empty lists are omitted, so the result always passes
        ``validate_config`` again (round trip).
        """
        out: dict[str, Any] = {}
        for f in fields(self):
            value = getattr(self, f.name)
            if value is None or (isinstance(value, list) and not value):
                continue
            out[f.name] = list(value) if isinstance(value, list) else value
        return out


def _split_name(name: str) -> list[str]:
    return [part.strip().strip("`") for part in name.split(".")]


def _name_shape_errors(key: str, names: Iterable[Any], parts: int, shape: str) -> list[str]:
    errors = []
    for i, name in enumerate(names):
        if not isinstance(name, str):
            continue  # reported by the schema
        split = _split_name(name)
        if len(split) != parts or not all(split):
            errors.append(f"{key}[{i}]: '{name}' must be a {parts}-part name {shape}")
    return errors


def _format_schema_error(err: jsonschema.ValidationError) -> str:
    if err.validator == "anyOf" and not err.absolute_path:
        return "config: at least one of source_catalogs, source_schemas, source_tables must be a non-empty list"
    where = ".".join(str(p) for p in err.absolute_path) or "config"
    return f"{where}: {err.message}"


def validate_config(d: Any) -> list[str]:
    """Return the problems with a raw config dict (empty list = valid).

    Checks the JSON Schema, then name shapes the schema does not express:
    ``source_tables`` entries must be 3-part names, ``source_schemas`` entries
    2-part names. Each ``config_warnings(d)`` item is emitted as a ``UserWarning``
    and is not an error.
    """
    if not isinstance(d, dict):
        return ["config: must be a JSON object"]
    for message in config_warnings(d):
        warnings.warn(message, UserWarning, stacklevel=2)
    validator = jsonschema.Draft202012Validator(load_schema())
    errors = sorted(
        (_format_schema_error(e) for e in validator.iter_errors(d)),
    )
    tables = d.get("source_tables")
    if isinstance(tables, list):
        errors += _name_shape_errors("source_tables", tables, 3, "catalog.schema.table")
    schemas = d.get("source_schemas")
    if isinstance(schemas, list):
        errors += _name_shape_errors("source_schemas", schemas, 2, "catalog.schema")
    return errors


def config_warnings(d: Any) -> list[str]:
    """Non-fatal advice for a raw config dict (empty list = nothing to report).

    ``max_metric_views_per_agent`` above ``AGENT_DATA_SOURCE_LIMIT`` (30): a Genie
    Agent holds at most 30 data sources, so agents are split at 30 anyway.
    """
    if not isinstance(d, dict):
        return []
    value = d.get("max_metric_views_per_agent")
    if isinstance(value, int) and not isinstance(value, bool) and value > AGENT_DATA_SOURCE_LIMIT:
        return [
            f"max_metric_views_per_agent: {value} is above {AGENT_DATA_SOURCE_LIMIT}, the most data sources "
            f"a Genie Agent can hold; agents are split at {AGENT_DATA_SOURCE_LIMIT} metric views"
        ]
    return []


def config_from_dict(d: dict[str, Any]) -> SdkConfig:
    """Validate ``d`` and return an ``SdkConfig`` with defaults applied.

    Raises ``ValueError`` listing every problem when ``d`` is invalid.
    """
    errors = validate_config(d)
    if errors:
        raise ValueError("invalid sdk config:\n  " + "\n  ".join(errors))
    known = {f.name for f in fields(SdkConfig)}
    kwargs: dict[str, Any] = {k: (list(v) if isinstance(v, list) else v) for k, v in d.items() if k in known}
    return SdkConfig(**kwargs)


def load_config(path: str | Path) -> SdkConfig:
    """Read ``sdk_config.json`` (or a ``.yml`` / ``.yaml`` file) and validate it."""
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    if p.suffix.lower() in {".yml", ".yaml"}:
        data = yaml.safe_load(text)
    else:
        data = json.loads(text)
    return config_from_dict(data)


def _as_config(cfg: SdkConfig | dict[str, Any]) -> SdkConfig:
    return cfg if isinstance(cfg, SdkConfig) else config_from_dict(cfg)


def _err(e: Exception) -> str:
    msg = str(e).strip() or type(e).__name__
    return msg.splitlines()[0]


def check_access(cfg: SdkConfig | dict[str, Any], ws: Any) -> list[str]:
    """Run the L200-A input checks against Unity Catalog. Never raises.

    Each check calls the matching ``get`` (``ws.catalogs.get``,
    ``ws.schemas.get``, ``ws.tables.get``) or, for volume directories,
    ``ws.files.list_directory_contents``. A failed call (not found, no
    permission) becomes one problem string. Existence and readability are
    checked; fine-grained privileges (``CREATE SCHEMA``) are not.
    """
    try:
        c = _as_config(cfg)
    except Exception as e:  # invalid config: report it, do not raise
        return [f"config: {_err(e)}"]

    problems: list[str] = []

    def probe(label: str, fn, *args, **kwargs) -> None:
        try:
            result = fn(*args, **kwargs)
            if result is not None and not isinstance(result, (dict, str)) and hasattr(result, "__iter__"):
                next(iter(result), None)  # force lazy iterators to make the call
        except Exception as e:
            problems.append(f"{label}: not found or not accessible ({_err(e)})")

    try:
        for name in c.source_catalogs:
            probe(f"source catalog '{name}'", ws.catalogs.get, name)
        for name in c.source_schemas:
            probe(f"source schema '{name}'", ws.schemas.get, name)
        for name in c.source_tables:
            probe(f"source table '{name}'", ws.tables.get, name)
        probe(f"target catalog '{c.target_catalog}'", ws.catalogs.get, c.target_catalog)
        if c.source_catalog_for_reads:
            probe(
                f"source_catalog_for_reads '{c.source_catalog_for_reads}'",
                ws.catalogs.get,
                c.source_catalog_for_reads,
            )
        for kind, paths in (
            ("supplemental volume dir", c.supplemental_volume_dirs),
            ("dashboard input", c.dashboard_inputs),
        ):
            for path in paths:
                if not path.startswith("/Volumes/"):
                    problems.append(f"{kind} '{path}': must be a /Volumes/ path")
                    continue
                if kind == "dashboard input" and not path.endswith("/"):
                    # a dashboard input may be a single file: check its directory
                    parent = path.rsplit("/", 1)[0]
                    probe(f"{kind} '{path}'", ws.files.list_directory_contents, parent)
                else:
                    probe(f"{kind} '{path}'", ws.files.list_directory_contents, path)
    except Exception as e:  # defensive: a broken client must not raise
        problems.append(f"check_access: unexpected error ({_err(e)})")
    return problems


def _table_full_name(t: Any) -> str:
    full = getattr(t, "full_name", None)
    if full:
        return full
    return f"{t.catalog_name}.{t.schema_name}.{t.name}"


def _schema_name(s: Any) -> str:
    name = getattr(s, "name", None)
    if name:
        return name
    return _split_name(s.full_name)[-1]


def expand_tables(cfg: SdkConfig | dict[str, Any], ws: Any) -> list[str]:
    """Resolve all source inputs to sorted, unique 3-part table names.

    ``source_tables`` are taken as given; each ``source_schemas`` entry is listed
    with ``ws.tables.list``; each ``source_catalogs`` entry is listed with
    ``ws.schemas.list`` (skipping ``information_schema``) and then
    ``ws.tables.list``. API errors propagate; run ``check_access`` first.
    """
    c = _as_config(cfg)
    names: set[str] = {".".join(_split_name(t)) for t in c.source_tables}

    def add_schema(catalog: str, schema: str) -> None:
        for t in ws.tables.list(catalog_name=catalog, schema_name=schema):
            names.add(_table_full_name(t))

    for full in c.source_schemas:
        catalog, schema = _split_name(full)
        add_schema(catalog, schema)
    for catalog in c.source_catalogs:
        for s in ws.schemas.list(catalog_name=catalog):
            schema = _schema_name(s)
            if schema in _SYSTEM_SCHEMAS:
                continue
            add_schema(catalog, schema)
    return sorted(names)
