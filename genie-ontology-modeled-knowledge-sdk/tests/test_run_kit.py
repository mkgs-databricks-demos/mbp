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
    "branch": "genie-build-sample_project",
    "sdk_version": "0.1.0",
}
TOKEN_RE = re.compile(r"\{\{\s*(\w+)\s*\}\}")
KIT_FILES = ["waves.json", "INDEX.md", "PROJECT_MEMORY.md", "README.md"]
GIT_WRITE_RE = re.compile(r"\bgit\s+(checkout|commit|push|merge|rebase|reset|stash|switch|pull)\b", re.IGNORECASE)
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


def _waves_manifest_module():
    gbw = _find_build_waves()
    if gbw is None:
        pytest.skip("genie-build-waves not found (set GENIE_BUILD_WAVES_DIR or place it next to the SDK)")
    sys.path.insert(0, str(gbw / "src" / "notebooks"))
    try:
        return importlib.import_module("waves_manifest"), importlib.import_module("authorizations")
    finally:
        sys.path.pop(0)


def test_validate_manifest_zero_errors(manifest):
    wm, auth = _waves_manifest_module()
    errors, warnings = wm.validate_manifest(manifest)
    assert errors == [], errors
    assert warnings == [], warnings
    a_errors, a_warnings = auth.validate_authorizations(manifest)
    assert a_errors == [] and a_warnings == [], (a_errors, a_warnings)
    n = wm.job_task_count(manifest)
    print("job_task_count:", n)
    assert n < 1000


def _structural_problems(m: dict) -> list[str]:
    """Run-kit rules beyond validate_manifest (build-1 R3). Empty = ok."""
    problems = []
    br = m.get("branch")
    if not isinstance(br, str) or not br.strip() or br.strip() in ("main", "master"):
        problems.append("top-level branch missing or main/master")
    pol = (m.get("authorization_policy") or {}).get("monitor_may_authorize") or []
    if {(e.get("action"), e.get("scope")) for e in pol} < {
        (a, "owned_assets") for a in ("jobs.run_now", "bundle.deploy", "volume.write", "workspace.write")
    }:
        problems.append("authorization_policy.monitor_may_authorize incomplete")
    sessions = [(w, s) for w in m.get("waves") or [] for s in w.get("sessions") or []]
    for w, s in sessions:
        auths = s.get("authorizations") or []
        sid = s.get("session_id")
        if s.get("allow_deploy"):
            deploy = [a["target"] for a in auths if a.get("action") == "bundle.deploy"]
            if not any(t.startswith("bundle:ontology-") for t in deploy):
                problems.append(f"session {sid}: allow_deploy without bundle.deploy naming a project bundle")
        targets = [a.get("target") for a in auths]
        if any(t not in (s.get("owned_assets") or []) for t in targets):
            problems.append(f"session {sid}: authorization target not in owned_assets")
        if "register_metric_views" in (s.get("scope") or "") and not any(
            a.get("action") == "jobs.run_now" for a in auths
        ):
            problems.append(f"session {sid}: runs register_metric_views without jobs.run_now")
    pages = [s for _, s in sessions if s.get("plan_file") == "plans/07_uc_pages.md"]
    pages_waves = [w for w, s in sessions if s in pages]
    if not pages or not any(
        "pages_domain_id" in p.get("title", "") for w in pages_waves for p in w.get("manual_prereqs") or []
    ):
        problems.append("Pages wave has no pages_domain_id manual_prereqs")
    iters = [w for w in m.get("waves") or [] if "Tuning Iteration" in w.get("name", "")]
    mandatory = [w for w in iters if "mandatory" in w["name"]]
    if len(mandatory) < 3:
        problems.append("fewer than 3 mandatory tuning iteration waves")
    if not iters or "asymptote" not in (iters[-1].get("required_checks") or []):
        problems.append("last tuning iteration wave has no asymptote required check")
    return problems


def test_run_kit_structure(manifest):
    assert _structural_problems(manifest) == []


@pytest.mark.parametrize("breakage", ["no_branch", "deploy_without_bundle_deploy"])
def test_broken_copy_fails(manifest, breakage):
    import copy

    broken = copy.deepcopy(manifest)
    if breakage == "no_branch":
        del broken["branch"]
    else:
        s = next(s for w in broken["waves"] for s in w["sessions"] if s.get("allow_deploy"))
        s["authorizations"] = [a for a in s["authorizations"] if a["action"] != "bundle.deploy"]
    assert _structural_problems(broken), breakage


def test_tuning_and_report_waves(manifest):
    names = [w["name"] for w in manifest["waves"]]
    assert any(n.startswith("Benchmark Authoring") for n in names)
    assert any(n.startswith("Benchmark Baseline") for n in names)
    assert sum("conditional" in n for n in names) == 3
    assert names[-1] == "Independent Report Simulation"
    checks = {c for w in manifest["waves"] for c in w.get("required_checks", [])}
    assert {"benchmark_coverage", "asymptote", "report_simulation"} <= checks


def test_registration_wave_has_wheel_prereq(manifest):
    reg = next(w for w in manifest["waves"] if w["name"] == "Metric View Registration")
    assert any(p["session_id"] == "P-wheel" and "0.1.0" in p["title"] for p in reg["manual_prereqs"])


def test_no_vendored_paths_in_kit():
    # Gate check run_kit_no_vendored_paths: the vendored copy is only mentioned for vendor=True.
    for f in [RUN_DIR / n for n in KIT_FILES] + plan_paths():
        for line in f.read_text().splitlines():
            assert "PYTHONPATH=" not in line, f"{f.name}: {line}"
            assert "sys.path" not in line, f"{f.name}: {line}"
            if "_vendored" in line:
                assert "vendor=True" in line, f"{f.name}: {line}"


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
            for sb, gb in owned[i + 1 :]:
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
    assert {"registration_job", "mv_smoke", "resolved_target", "agent_probe", "baseline_results"} <= checks
    for wid in ["2", "3", "4", "5", "7", "8", "9", "10", "11", "12", "13"]:
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


def _scaffold(tmp_path, cfg, **kw):
    from genie_ontology_modeled_knowledge_sdk.scaffold import scaffold_project

    target = tmp_path / "proj"
    scaffold_project(cfg, target, SDK_ROOT, **kw)
    return target, json.loads((target / "docs" / "plans" / "waves.json").read_text())


def test_scaffold_renders_branch_and_sdk_version(tmp_path, tpch_config):
    from genie_ontology_modeled_knowledge_sdk.scaffold import _sdk_version

    target, m = _scaffold(tmp_path, tpch_config, branch="genie-build-tpch")
    assert m["branch"] == "genie-build-tpch"
    text = (target / "docs" / "plans" / "waves.json").read_text()
    assert "{{" not in text and _sdk_version(SDK_ROOT) in text
    assert json.loads((target / "sdk_config.json").read_text())["sdk_distribution"] == "wheel"
    assert _structural_problems(m) == []


def test_scaffolded_kit_validates(tmp_path, tpch_config):
    _, m = _scaffold(tmp_path, tpch_config)
    wm, auth = _waves_manifest_module()
    assert wm.validate_manifest(m) == ([], [])
    assert auth.validate_authorizations(m) == ([], [])


def test_scaffold_vendor_drops_wheel_prereq(tmp_path, tpch_config):
    target, m = _scaffold(tmp_path, tpch_config, vendor=True)
    prereqs = [p for w in m["waves"] for p in w.get("manual_prereqs") or []]
    assert not any(p["session_id"] == "P-wheel" for p in prereqs)
    assert any("pages_domain_id" in p["title"] for p in prereqs)
    assert json.loads((target / "sdk_config.json").read_text())["sdk_distribution"] == "vendored"


@pytest.mark.parametrize("branch", ["main", "master"])
def test_scaffold_rejects_main_branch(tmp_path, tpch_config, branch):
    from genie_ontology_modeled_knowledge_sdk.scaffold import scaffold_project

    with pytest.raises(ValueError):
        scaffold_project(tpch_config, tmp_path / "p", SDK_ROOT, branch=branch)


def test_config_run_kit_keys(tpch_config):
    from genie_ontology_modeled_knowledge_sdk.config import config_from_dict, validate_config

    d = {**tpch_config, "pages_domain_id": "dom-1", "pages_status": "DRAFT", "sdk_distribution": "wheel"}
    assert validate_config(d) == []
    assert config_from_dict(d).to_dict()["pages_domain_id"] == "dom-1"
    assert validate_config({**tpch_config, "pages_status": "LIVE"})
    assert validate_config({**tpch_config, "sdk_distribution": "pip"})
