"""Tests for the pipeline-run kit template (templates/run/).

Renders the ``{{...}}`` tokens with sample values, then checks the manifest with
genie-build-waves' ``validate_manifest`` and a few structural rules of its own.

genie-build-waves is looked up in ``$GENIE_BUILD_WAVES_DIR`` first, then as a
``genie-build-waves`` folder next to the SDK root or any of its parents. When it
cannot be found, only the validate_manifest test is skipped (with a reason).
"""

from __future__ import annotations

import importlib
import json
import os
import re
import sys
from pathlib import Path

import pytest

SDK_ROOT = Path(__file__).resolve().parents[1]
RUN_DIR = SDK_ROOT / "templates" / "run"
SAMPLE_VALUES = {
    "project_name": "sample_project",
    "domain_name": "sample_domain",
    "bundle_target": "dev",
}
TOKEN_RE = re.compile(r"\{\{\s*(\w+)\s*\}\}")
KIT_FILES = ["waves.json", "INDEX.md", "PROJECT_MEMORY.md", "README.md"]
GIT_WRITE_RE = re.compile(
    r"\bgit\s+(checkout|commit|push|merge|rebase|reset|stash|switch|pull)\b", re.IGNORECASE
)
# Workspace-specific identifiers that must never appear in the kit.
WORKSPACE_ID_RES = [
    re.compile(r"https?://[\w.-]*(cloud\.databricks\.com|azuredatabricks\.net|gcp\.databricks\.com)"),
    re.compile(r"/Workspace/Users/"),
    re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+"),
    re.compile(r"\b[0-9a-f]{16}\b"),  # warehouse-id shaped hex
]


def render(text: str, values: dict[str, str] = SAMPLE_VALUES) -> str:
    return TOKEN_RE.sub(lambda m: values.get(m.group(1), m.group(0)), text)


def plan_paths() -> list[Path]:
    return sorted((RUN_DIR / "plans").glob("*.md"))


@pytest.fixture(scope="module")
def manifest() -> dict:
    return json.loads(render((RUN_DIR / "waves.json").read_text()))


def _find_build_waves() -> Path | None:
    env = os.environ.get("GENIE_BUILD_WAVES_DIR")
    candidates = [Path(env)] if env else []
    candidates += [p / "genie-build-waves" for p in [SDK_ROOT, *SDK_ROOT.parents]]
    for c in candidates:
        if (c / "src" / "notebooks" / "waves_manifest.py").is_file():
            return c
    return None


def test_template_files_exist():
    for name in KIT_FILES:
        assert (RUN_DIR / name).is_file(), name
    assert plan_paths(), "templates/run/plans/ has no plans"


def test_only_known_tokens_and_all_rendered():
    files = [RUN_DIR / n for n in KIT_FILES] + plan_paths()
    for f in files:
        text = f.read_text()
        unknown = set(TOKEN_RE.findall(text)) - set(SAMPLE_VALUES)
        assert not unknown, f"{f.name}: unknown tokens {sorted(unknown)}"
        assert "{{" not in render(text), f"{f.name}: token left after render"


def test_validate_manifest_zero_errors(manifest):
    gbw = _find_build_waves()
    if gbw is None:
        pytest.skip("genie-build-waves not found (set GENIE_BUILD_WAVES_DIR or place it next to the SDK)")
    sys.path.insert(0, str(gbw / "src" / "notebooks"))
    try:
        wm = importlib.import_module("waves_manifest")
    finally:
        sys.path.pop(0)
    errors, warnings = wm.validate_manifest(manifest)
    assert errors == [], errors
    print("validate_manifest warnings:", warnings)


def test_every_plan_file_exists(manifest):
    # plans_dir is docs/plans in the project; scaffold copies templates/run/* there.
    assert manifest["plans_dir"] == "docs/plans"
    for wave in manifest["waves"]:
        for s in wave["sessions"]:
            assert (RUN_DIR / s["plan_file"]).is_file(), s["plan_file"]


def test_every_plan_is_referenced(manifest):
    referenced = {s["plan_file"] for w in manifest["waves"] for s in w["sessions"]}
    on_disk = {f"plans/{p.name}" for p in plan_paths()}
    assert on_disk == referenced


def _prefix(glob: str) -> str:
    """Literal prefix of a glob (up to the first wildcard)."""
    return re.split(r"[*?\[]", glob, maxsplit=1)[0]


def _overlap(a: str, b: str) -> bool:
    pa, pb = _prefix(a), _prefix(b)
    return pa.startswith(pb) or pb.startswith(pa)


def test_owned_paths_disjoint_within_each_wave(manifest):
    for wave in manifest["waves"]:
        owned = [(s["session_id"], g) for s in wave["sessions"] for g in s.get("owned_paths", [])]
        for i, (sa, ga) in enumerate(owned):
            for sb, gb in owned[i + 1:]:
                if sa != sb:
                    assert not _overlap(ga, gb), f"wave {wave['wave_id']}: {sa} {ga} overlaps {sb} {gb}"


def test_edit_sessions_have_owned_paths(manifest):
    for wave in manifest["waves"]:
        for s in wave["sessions"]:
            if s.get("mode", "edit") in ("edit", "converge"):
                assert s.get("owned_paths"), s["session_id"]


def test_discovery_wave_is_parallel(manifest):
    disc = [w for w in manifest["waves"] if {"02", "03", "04"} <= {s["session_id"] for s in w["sessions"]}]
    assert len(disc) == 1, "research, context and EDA must share one wave"


def test_single_deployer_per_wave(manifest):
    for wave in manifest["waves"]:
        deployers = [s for s in wave["sessions"] if s.get("allow_deploy") or s.get("mode") == "converge"]
        if deployers:
            assert len(wave["sessions"]) == 1, wave["wave_id"]


def test_required_checks_and_bundle_validation(manifest):
    by_id = {w["wave_id"]: w for w in manifest["waves"]}
    checks = {c for w in manifest["waves"] for c in w.get("required_checks", [])}
    assert {"registration_job", "mv_smoke", "agent_probe", "benchmark_results"} <= checks
    for wid in ["2", "3", "4", "5", "6"]:
        roots = {vb["root"] for vb in by_id[wid].get("validate_bundles", [])}
        assert roots == {"ontology-metric-views", "ontology-genie-agents"}, wid


def test_context_files(manifest):
    assert manifest["context_files"] == ["sdk_config.json", "PROJECT_MEMORY.md", "docs/inputs_report.md"]
    assert manifest["workflow"]["mode"] == "hybrid"


def test_no_git_write_commands_in_kit():
    for f in [RUN_DIR / n for n in KIT_FILES] + plan_paths():
        m = GIT_WRITE_RE.search(f.read_text())
        assert m is None, f"{f.name}: contains '{m.group(0)}'"


def test_no_workspace_identifiers_in_kit():
    for f in [RUN_DIR / n for n in KIT_FILES] + plan_paths():
        text = f.read_text()
        for rx in WORKSPACE_ID_RES:
            m = rx.search(text)
            assert m is None, f"{f.name}: workspace-specific value '{m.group(0)}'"


def test_plans_have_planner_sections():
    sections = ["## Scope", "## Context", "## Tasks", "## Acceptance Criteria", "## Owned Paths", "## Dependencies"]
    for p in plan_paths():
        text = p.read_text()
        for sec in sections:
            assert sec in text, f"{p.name}: missing {sec}"
