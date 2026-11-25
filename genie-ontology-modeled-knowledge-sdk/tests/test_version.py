"""Version consistency (plan build-1/23, task 1).

``pyproject.toml`` is the only source. ``__version__``, the metric-views
template's ``sdk_version`` default and (in test_wheel.py) the built wheel's
METADATA must all agree with it.
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml

from genie_ontology_modeled_knowledge_sdk import __version__

ROOT = Path(__file__).resolve().parents[1]


def pyproject_version() -> str:
    m = re.search(r'(?m)^version\s*=\s*"([^"]+)"', (ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert m, "pyproject.toml has no [project] version"
    return m.group(1)


def test_pyproject_version_is_0_1_0():
    assert pyproject_version() == "0.1.0"


def test_dunder_version_matches_pyproject():
    assert __version__ == pyproject_version()


def test_template_sdk_version_matches():
    bundle = yaml.safe_load((ROOT / "templates" / "ontology-metric-views" / "databricks.yml").read_text())
    assert str(bundle["variables"]["sdk_version"]["default"]) == pyproject_version()


def test_changelog_has_current_version():
    text = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    assert pyproject_version() in text and "0.0.1" in text
