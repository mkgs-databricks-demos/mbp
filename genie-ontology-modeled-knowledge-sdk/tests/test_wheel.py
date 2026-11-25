"""Wheel contents (plan build-1/23, task 10).

Builds the wheel once with ``pip wheel --no-deps`` into a temp folder and checks
its name, METADATA version, package data (JSON schemas) and console-script
entry points. Skipped when the source tree is not available (installed-wheel
runs) or the build backend cannot be reached.
"""

from __future__ import annotations

import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
ENTRY_POINTS = (
    "gos-check-config",
    "gos-validate-mv",
    "gos-build-manifest",
    "gos-render-agents",
    "gos-scaffold",
    "gos-resolve-target",
    "gos-benchmark",
)


@pytest.fixture(scope="module")
def wheel(tmp_path_factory) -> Path:
    if not (ROOT / "pyproject.toml").is_file():
        pytest.skip("no SDK source tree")
    out = tmp_path_factory.mktemp("dist")
    proc = subprocess.run(
        [sys.executable, "-m", "pip", "wheel", "--no-deps", "-q", "-w", str(out), str(ROOT)],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        pytest.skip(f"wheel build unavailable: {proc.stderr[-500:]}")
    (whl,) = out.glob("*.whl")
    return whl


def test_wheel_name(wheel):
    from test_version import pyproject_version

    assert wheel.name == f"genie_ontology_modeled_knowledge_sdk-{pyproject_version()}-py3-none-any.whl"


def test_wheel_metadata_version(wheel):
    from test_version import pyproject_version

    with zipfile.ZipFile(wheel) as z:
        meta = next(n for n in z.namelist() if n.endswith(".dist-info/METADATA"))
        text = z.read(meta).decode()
    assert f"Version: {pyproject_version()}" in text.splitlines()


def test_wheel_has_package_and_schemas(wheel):
    with zipfile.ZipFile(wheel) as z:
        names = set(z.namelist())
    assert "genie_ontology_modeled_knowledge_sdk/__init__.py" in names
    assert "genie_ontology_modeled_knowledge_sdk/schemas/sdk_config.schema.json" in names
    assert not [n for n in names if n.startswith(("tests/", "templates/", "examples/"))]


def test_wheel_entry_points(wheel):
    with zipfile.ZipFile(wheel) as z:
        ep = next(n for n in z.namelist() if n.endswith(".dist-info/entry_points.txt"))
        text = z.read(ep).decode()
    for name in ENTRY_POINTS:
        assert f"{name} =" in text, name
