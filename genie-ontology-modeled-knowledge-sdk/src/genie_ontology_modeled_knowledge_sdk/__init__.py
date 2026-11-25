"""Genie Ontology Modeled Knowledge SDK.

Automates the standup of modeled knowledge for Genie Ontology: Unity Catalog
source assets + supplemental business context -> parameterized metric views ->
UC Pages -> curated Genie Agents -> an initial tuning plan.

Modules (import them directly; nothing is imported eagerly here):

* ``config``     - input contract: ``SdkConfig``, ``load_config``, ``config_from_dict``,
                   ``validate_config``, ``check_access``, ``expand_tables``
* ``mv_yaml``    - metric view YAML load / substitute / validate / render DDL (+ CLI)
* ``manifest``   - ``manifest.json`` (forEach registration input) build / write / validate
* ``geniespace`` - Genie Agent planning and ``.geniespace.json`` builder (+ CLI)
* ``pages``      - glossary term files -> UC Pages payloads and upsert
* ``benchmark``  - Genie Agent benchmark questions, run and scoring
* ``scaffold``   - ``scaffold_project`` for a new run project
* ``targets``    - ``resolve_target`` from ``databricks bundle summary``

Library modules are pure Python (no Spark imports). Databricks access goes
through an injected ``WorkspaceClient`` so tests can pass a fake.

The version has one source, ``pyproject.toml``. ``__version__`` comes from the
installed distribution's metadata; in a source tree (``src/`` on the path, the
package not installed from this checkout) it is read from ``pyproject.toml``.
"""

from __future__ import annotations

import re
from importlib import metadata as _metadata
from pathlib import Path as _Path

DIST_NAME = "genie-ontology-modeled-knowledge-sdk"
_PYPROJECT = _Path(__file__).resolve().parents[2] / "pyproject.toml"
_VERSION_RE = re.compile(r'(?m)^version\s*=\s*"([^"]+)"')
_NAME_RE = re.compile(r'(?m)^name\s*=\s*"([^"]+)"')


def _source_tree_version() -> str | None:
    """Version from ``pyproject.toml`` when this package sits in an SDK source tree."""
    try:
        text = _PYPROJECT.read_text(encoding="utf-8")
    except OSError:
        return None
    name, version = _NAME_RE.search(text), _VERSION_RE.search(text)
    if not name or name.group(1) != DIST_NAME or not version:
        return None
    return version.group(1)


def _resolve_version() -> str:
    # A source tree wins, so a stale installed copy never masks the checkout's version.
    found = _source_tree_version()
    if found:
        return found
    try:
        return _metadata.version(DIST_NAME)
    except _metadata.PackageNotFoundError:
        return "0+unknown"


__version__ = _resolve_version()


def check_config_main(argv: list[str] | None = None) -> int:
    """``gos-check-config <sdk_config.json|.yml>``: validate the input contract (exit 1 on errors)."""
    import argparse
    import sys

    from genie_ontology_modeled_knowledge_sdk.config import load_config, validate_config

    parser = argparse.ArgumentParser(
        prog="gos-check-config", description="Validate an sdk_config.json / .yml against the SDK input contract."
    )
    parser.add_argument("config", help="path to sdk_config.json or sdk_config.yml")
    args = parser.parse_args(argv)
    try:
        cfg = load_config(args.config)
    except (OSError, ValueError) as e:
        print(f"gos-check-config: {e}", file=sys.stderr)
        return 1
    errors = validate_config(cfg.to_dict())
    for err in errors:
        print(f"error: {err}", file=sys.stderr)
    print(f"{args.config}: {len(errors)} error(s)")
    return 1 if errors else 0


__all__ = ["DIST_NAME", "__version__", "check_config_main"]
