"""Resolve where a metric-views bundle registers its metric views (single source of truth).

A consumer bundle (the Genie Agents bundle) cannot reference another bundle's
resources, and in development mode the schema name gets a per-user prefix
(``dev_<short_name>_<schema_name>``). So the resolved target is read from
``databricks bundle summary -o json`` of the metric-views bundle and written to
a small JSON file that the agents render step consumes
(``geniespace render --params <resolved_target.json>``).

Public API (cross-session contract, see ``docs/plans/build-1/INDEX.md``):

* ``resolve_target(bundle_dir, target="dev", *, runner=None, ...) -> dict``
* ``target_from_summary(summary, *, schema_key="ontology_schema") -> dict``
* ``write_resolved_target(path, data) -> Path``
* CLI: ``python -m genie_ontology_modeled_knowledge_sdk.targets resolve --bundle <dir> --target dev --out <path>``

``resolved_target.json`` shape::

    {"catalog": "...", "schema": "...", "warehouse_id": "..." | null,
     "source": "bundle_summary", "resolved_at": "<UTC ISO-8601>"}

``warehouse_id`` is the metric-views bundle's optional ``warehouse_id`` variable;
``null`` when it is not set.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections.abc import Callable, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

__all__ = [
    "RESOLVED_KEYS",
    "SCHEMA_KEY",
    "SOURCE",
    "Runner",
    "main",
    "resolve_target",
    "summary_command",
    "target_from_summary",
    "write_resolved_target",
]

SCHEMA_KEY = "ontology_schema"  # resources.schemas key in templates/ontology-metric-views
SOURCE = "bundle_summary"
RESOLVED_KEYS = ("catalog", "schema", "warehouse_id", "source", "resolved_at")

# runner(command, cwd) -> stdout. Injectable so tests never call the CLI.
Runner = Callable[[Sequence[str], Path], str]


def _cli_runner(command: Sequence[str], cwd: Path) -> str:
    proc = subprocess.run(list(command), cwd=str(cwd), capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or "").strip()
        raise RuntimeError(f"'{' '.join(command)}' failed (exit {proc.returncode}): {detail}")
    return proc.stdout


def summary_command(target: str, extra_args: Sequence[str] = ()) -> list[str]:
    """The CLI command ``resolve_target`` runs in the bundle folder."""
    return ["databricks", "bundle", "summary", "-o", "json", "--target", target, *extra_args]


def _text(value: Any, what: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"bundle summary has no {what}")
    if "${" in value:
        raise ValueError(f"bundle summary {what} is not resolved: {value!r}")
    return value.strip()


def target_from_summary(
    summary: dict[str, Any],
    *,
    schema_key: str = SCHEMA_KEY,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Build the ``resolved_target.json`` dict from a parsed ``bundle summary``.

    The schema is ``resources.schemas.<schema_key>`` (or the only schema, if the
    bundle declares exactly one). Its ``name`` already carries the development
    prefix in a ``mode: development`` target. ``ValueError`` if it is missing or
    unresolved.
    """
    if not isinstance(summary, dict):
        raise ValueError("bundle summary must be a JSON object")
    schemas = (summary.get("resources") or {}).get("schemas") or {}
    if schema_key in schemas:
        spec = schemas[schema_key]
    elif len(schemas) == 1:
        spec = next(iter(schemas.values()))
    else:
        found = ", ".join(sorted(schemas)) or "none"
        raise ValueError(f"bundle summary has no schema resource '{schema_key}' (found: {found})")
    if not isinstance(spec, dict):
        raise ValueError(f"bundle summary schema '{schema_key}' is not an object")

    raw_wh = ((summary.get("variables") or {}).get("warehouse_id") or {}).get("value")
    warehouse_id = raw_wh.strip() if isinstance(raw_wh, str) and raw_wh.strip() else None

    return {
        "catalog": _text(spec.get("catalog_name"), "schema catalog_name"),
        "schema": _text(spec.get("name"), "schema name"),
        "warehouse_id": warehouse_id,
        "source": SOURCE,
        "resolved_at": (now or datetime.now(UTC)).isoformat(timespec="seconds"),
    }


def resolve_target(
    bundle_dir: str | Path,
    target: str = "dev",
    *,
    runner: Runner | None = None,
    schema_key: str = SCHEMA_KEY,
    extra_args: Sequence[str] = (),
    now: datetime | None = None,
) -> dict[str, Any]:
    """Run ``databricks bundle summary -o json --target <target>`` in ``bundle_dir`` and resolve the target.

    ``extra_args`` are appended to the command (for example ``["--var", "consumer_group=g"]``).
    ``RuntimeError`` if the CLI fails, ``ValueError`` if its output is not usable.
    """
    bundle = Path(bundle_dir)
    if not (bundle / "databricks.yml").is_file():
        raise ValueError(f"'{bundle}' is not a bundle folder (no databricks.yml)")
    out = (runner or _cli_runner)(summary_command(target, extra_args), bundle)
    try:
        summary = json.loads(out)
    except json.JSONDecodeError as exc:
        raise ValueError(f"bundle summary output is not JSON: {exc}") from exc
    return target_from_summary(summary, schema_key=schema_key, now=now)


def write_resolved_target(path: str | Path, data: dict[str, Any]) -> Path:
    """Write ``data`` (the ``resolve_target`` dict) as ``resolved_target.json``; returns the path."""
    missing = [k for k in RESOLVED_KEYS if k not in data]
    if missing:
        raise ValueError(f"resolved target is missing key(s): {', '.join(missing)}")
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({k: data[k] for k in RESOLVED_KEYS}, indent=2) + "\n", encoding="utf-8")
    return p


def main(argv: list[str] | None = None, *, runner: Runner | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m genie_ontology_modeled_knowledge_sdk.targets",
        description="Resolve the metric-views bundle target (catalog, schema) from bundle summary.",
    )
    sub = parser.add_subparsers(dest="command", required=True)
    res = sub.add_parser("resolve", help="write resolved_target.json from databricks bundle summary")
    res.add_argument("--bundle", required=True, help="metric-views bundle folder (has databricks.yml)")
    res.add_argument("--target", default="dev")
    res.add_argument("--out", default=None, help="resolved_target.json path (default: print only)")
    res.add_argument("--schema-key", default=SCHEMA_KEY)
    res.add_argument("--var", action="append", default=[], help="name=value, passed to bundle summary")
    args = parser.parse_args(argv)

    extra: list[str] = []
    for v in args.var:
        extra += ["--var", v]
    try:
        data = resolve_target(args.bundle, args.target, runner=runner, schema_key=args.schema_key, extra_args=extra)
        if args.out:
            write_resolved_target(args.out, data)
    except (ValueError, RuntimeError, OSError) as e:
        print(f"targets: {e}", file=sys.stderr)
        return 1
    print(json.dumps(data, indent=2))
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
