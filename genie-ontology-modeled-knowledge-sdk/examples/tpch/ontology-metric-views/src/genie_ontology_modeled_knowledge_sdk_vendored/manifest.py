"""The metric view ``manifest.json``: the forEach input of the registration job.

Shape (see ``docs/plans/INDEX.md`` cross-session contracts)::

    [{"name": "mv_tpch_revenue",
      "yaml_path": "metric_views/tpch_supply_chain/mv_tpch_revenue.yml",
      "domain": "tpch_supply_chain",
      "subdomain": "sales"}]

* ``name`` is the YAML file stem (the metric view name).
* ``yaml_path`` is POSIX-style and relative to the bundle root (by default the
  parent of the ``metric_views`` directory).
* ``domain`` is the first folder under ``metric_views/``.
* ``subdomain`` comes from a ``# subdomain: <name>`` header comment in the YAML
  (the metric view spec has no key for it), else from a second folder level
  (``metric_views/<domain>/<subdomain>/x.yml``), else ``null``.
* Entries are sorted by ``name``.

CLI::

    python -m genie_ontology_modeled_knowledge_sdk.manifest build <metric_views_dir> <out.json>
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path, PurePosixPath
from typing import Any

from genie_ontology_modeled_knowledge_sdk.mv_yaml import iter_mv_files

__all__ = ["MANIFEST_KEYS", "build_manifest", "write_manifest", "validate_manifest_json", "main"]

MANIFEST_KEYS = ("name", "yaml_path", "domain", "subdomain")
_SUBDOMAIN_RE = re.compile(r"^\s*#\s*subdomain\s*:\s*([A-Za-z0-9_\-]+)\s*$", re.IGNORECASE | re.MULTILINE)
_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _subdomain_comment(path: Path) -> str | None:
    try:
        m = _SUBDOMAIN_RE.search(path.read_text(encoding="utf-8"))
    except OSError:
        return None
    return m.group(1) if m else None


def build_manifest(metric_views_dir: str | Path, *, bundle_root: str | Path | None = None) -> list[dict]:
    """Build manifest entries for every ``*.yml`` / ``*.yaml`` under ``metric_views_dir``.

    Raises ``ValueError`` if a YAML file is not inside a domain folder, if the
    directory is outside ``bundle_root``, or if two files share a name.
    """
    mv_dir = Path(metric_views_dir).resolve()
    if not mv_dir.is_dir():
        raise ValueError(f"{metric_views_dir} is not a directory")
    root = Path(bundle_root).resolve() if bundle_root is not None else mv_dir.parent
    try:
        mv_dir.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"{mv_dir} is not inside bundle root {root}") from exc

    entries: list[dict] = []
    problems: list[str] = []
    for path in iter_mv_files(mv_dir):
        rel_to_mv = path.resolve().relative_to(mv_dir).parts
        if len(rel_to_mv) < 2:
            problems.append(f"{path.name}: must be inside a domain folder (metric_views/<domain>/{path.name})")
            continue
        subdomain = _subdomain_comment(path)
        if subdomain is None and len(rel_to_mv) >= 3:
            subdomain = rel_to_mv[1]
        entries.append({
            "name": path.stem,
            "yaml_path": PurePosixPath(*path.resolve().relative_to(root).parts).as_posix(),
            "domain": rel_to_mv[0],
            "subdomain": subdomain,
        })
    entries.sort(key=lambda e: e["name"])
    for a, b in zip(entries, entries[1:]):
        if a["name"] == b["name"]:
            problems.append(f"duplicate metric view name {a['name']!r}: {a['yaml_path']} and {b['yaml_path']}")
    if problems:
        raise ValueError("; ".join(problems))
    return entries


def validate_manifest_json(entries: Any, *, base_dir: str | Path | None = None) -> list[str]:
    """Validate manifest entries; returns a list of problems (empty when valid).

    Checks: a list of objects with exactly the keys ``name``, ``yaml_path``,
    ``domain``, ``subdomain``; unique names; sorted by name; ``yaml_path``
    relative (no ``..``) and, when ``base_dir`` (the bundle root, default the
    current directory) is given or defaulted, an existing file.
    """
    if not isinstance(entries, list):
        return ["manifest must be a JSON array"]
    base = Path(base_dir) if base_dir is not None else Path.cwd()
    problems: list[str] = []
    seen: set[str] = set()
    names: list[str] = []
    for i, entry in enumerate(entries):
        where = f"entry[{i}]"
        if not isinstance(entry, dict):
            problems.append(f"{where}: must be an object")
            continue
        missing = [k for k in MANIFEST_KEYS if k not in entry]
        extra = sorted(set(entry) - set(MANIFEST_KEYS))
        if missing:
            problems.append(f"{where}: missing key(s) {', '.join(missing)}")
        if extra:
            problems.append(f"{where}: unknown key(s) {', '.join(extra)}")
        name = entry.get("name")
        if not isinstance(name, str) or not _NAME_RE.match(name):
            problems.append(f"{where}: name {name!r} must be an identifier")
        else:
            where = f"{where} '{name}'"
            if name in seen:
                problems.append(f"{where}: duplicate name")
            seen.add(name)
            names.append(name)
        if not isinstance(entry.get("domain"), str) or not entry.get("domain"):
            problems.append(f"{where}: domain must be a non-empty string")
        sub = entry.get("subdomain")
        if sub is not None and (not isinstance(sub, str) or not sub):
            problems.append(f"{where}: subdomain must be a non-empty string or null")
        yp = entry.get("yaml_path")
        if not isinstance(yp, str) or not yp:
            problems.append(f"{where}: yaml_path must be a non-empty string")
            continue
        pp = PurePosixPath(yp)
        if pp.is_absolute() or "\\" in yp or ".." in pp.parts:
            problems.append(f"{where}: yaml_path {yp!r} must be relative to the bundle root (POSIX, no '..')")
            continue
        if isinstance(name, str) and pp.stem != name:
            problems.append(f"{where}: yaml_path file name {pp.name!r} does not match name")
        if not (base / pp).is_file():
            problems.append(f"{where}: file {yp} does not exist under {base}")
    if names != sorted(names):
        problems.append("entries must be sorted by name")
    return problems


def write_manifest(entries: list[dict], path: str | Path, *, base_dir: str | Path | None = None) -> Path:
    """Validate ``entries`` and write them as ``manifest.json`` (2-space indent).

    ``base_dir`` is the bundle root used to check that files exist (default:
    the directory of ``path``). Raises ``ValueError`` listing all problems.
    """
    out = Path(path)
    problems = validate_manifest_json(entries, base_dir=base_dir if base_dir is not None else out.parent)
    if problems:
        raise ValueError("invalid manifest: " + "; ".join(problems))
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(entries, indent=2) + "\n", encoding="utf-8")
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m genie_ontology_modeled_knowledge_sdk.manifest", description="metric view manifest.json tools")
    sub = parser.add_subparsers(dest="command", required=True)
    p_build = sub.add_parser("build", help="build manifest.json from a metric_views directory")
    p_build.add_argument("metric_views_dir")
    p_build.add_argument("out", help="output path, e.g. <bundle_root>/manifest.json")
    p_build.add_argument("--bundle-root", default=None, help="default: parent of metric_views_dir")
    args = parser.parse_args(argv)
    try:
        root = Path(args.bundle_root) if args.bundle_root else Path(args.metric_views_dir).resolve().parent
        entries = build_manifest(args.metric_views_dir, bundle_root=root)
        write_manifest(entries, args.out, base_dir=root)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(f"wrote {len(entries)} entr{'y' if len(entries) == 1 else 'ies'} to {args.out}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
