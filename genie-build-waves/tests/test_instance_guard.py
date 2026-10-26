"""Tests for instance_guard.py and scripts/deploy_instance.py (pure parts).

Scenarios come from the 2026-10-26 incident (docs/plans/2026-10-26_instance-state-isolation.md).
"""

import importlib.util
import os

import instance_guard as ig

U = "/Workspace/Users/me@example.com"
DEFAULT_ROOT = f"{U}/.bundle/genie-build-waves/dev"
SMOKE_ROOT = f"{U}/.bundle/genie-build-waves-smoke/dev"
SGT_MANIFEST = f"{U}/semanticGroundTruth/docs/plans/waves.json"
SMOKE_MANIFEST = f"{U}/mbp/genie-build-waves/.scratch/smoke-waves.json"
IDS = {"build_waves": "1079", "build_waves_smoke": "557", "setup_build_waves": "818"}


def job(name, meta_root=None, manifest=None):
    s = {"name": name}
    if meta_root:
        s["deployment"] = {"kind": "BUNDLE", "metadata_file_path": f"{meta_root}/state/metadata.json"}
    if manifest:
        s["parameters"] = [{"name": "branch", "default": "b"}, {"name": "manifest_path", "default": manifest}]
    return {"settings": s}


def summary(root, ids=IDS):
    return {"workspace": {"root_path": root},
            "resources": {"jobs": {k: {"id": v, "name": k} for k, v in ids.items()}}}


def state(ids=IDS):
    return {"lineage": "x", "serial": 6,
            "state": {f"resources.jobs.{k}": {"__id__": v, "state": {}} for k, v in ids.items()}}


def run(rid, manifest, value=True):
    p = {"name": "manifest_path", "default": manifest}
    if value:
        p["value"] = manifest
    return {"run_id": rid, "job_parameters": [p]}


# sGt default instance as it is after a normal setup run: build/smoke lost `deployment`.
SGT_JOBS = {
    "build_waves": job("[dev me] Semantic Ground Truth: Build Waves", manifest=SGT_MANIFEST),
    "build_waves_smoke": job("[dev me] Semantic Ground Truth: Build Waves Smoke Test"),
    "setup_build_waves": job("[dev me] Semantic Ground Truth: Build Waves Setup", meta_root=DEFAULT_ROOT),
}
SGT_RUNS = [run(110, SGT_MANIFEST)]


# --- paths ---------------------------------------------------------------------------

def test_under_root_handles_workspace_prefix_and_siblings():
    assert ig.under_root(f"{DEFAULT_ROOT}/state/metadata.json", DEFAULT_ROOT)
    assert ig.under_root("/Users/me@example.com/.bundle/genie-build-waves/dev/state/m.json", DEFAULT_ROOT + "/")
    # -smoke shares the prefix string but is a different root
    assert not ig.under_root(f"{SMOKE_ROOT}/state/metadata.json", DEFAULT_ROOT)
    assert not ig.under_root(f"{DEFAULT_ROOT}/state/m.json", SMOKE_ROOT)
    assert not ig.under_root("/x", "")


def test_summary_and_state_ids():
    assert ig.summary_job_ids(summary(DEFAULT_ROOT)) == IDS
    assert ig.summary_job_ids({"resources": {"jobs": {"a": {"name": "no id yet"}}}}) == {}
    assert ig.state_job_ids(state()) == IDS
    assert ig.state_job_ids(None) is None
    assert ig.state_job_ids({"state": {"resources.schemas.s": {"__id__": "c.s"}}}) == {}


# --- the incident -----------------------------------------------------------------------

def test_first_deploy_with_foreign_cache_is_refused():
    """-smoke had no remote state, but the cache carried the default instance's IDs."""
    p = ig.deploy_problems(summary(SMOKE_ROOT), None, SGT_JOBS, SGT_RUNS, SMOKE_MANIFEST)
    text = "\n".join(p)
    assert "no remote state" in text
    assert "was deployed from" in text            # setup job belongs to the default root
    assert "manifest_path default" in text         # build job is sGt's
    assert "latest run 110" in text


def test_redeploy_of_smoke_state_still_refused():
    """After the bad deploy, -smoke's remote state claims the same IDs; ownership still fails."""
    p = ig.deploy_problems(summary(SMOKE_ROOT), state(), SGT_JOBS, SGT_RUNS, SMOKE_MANIFEST)
    assert not [x for x in p if "remote state" in x]  # state matches the summary
    assert any("setup_build_waves" in x and "was deployed from" in x for x in p)


def test_owner_redeploy_passes():
    assert ig.deploy_problems(summary(DEFAULT_ROOT), state(), SGT_JOBS, SGT_RUNS, SGT_MANIFEST) == []


def test_clean_first_deploy_passes():
    assert ig.deploy_problems(summary(SMOKE_ROOT, ids={}), None, {}, [], SMOKE_MANIFEST) == []


def test_summary_ids_must_match_remote_state():
    p = ig.deploy_problems(summary(DEFAULT_ROOT, ids={**IDS, "build_waves": "295"}), state(),
                           {}, [], None)
    assert p == [f"build_waves: bundle summary shows job 295, but the remote state under {DEFAULT_ROOT} has job 1079"]
    p = ig.state_problems({"extra": "1"}, {}, DEFAULT_ROOT)
    assert "has no extra" in p[0]


def test_deleted_job_is_not_an_ownership_problem():
    assert ig.job_problems("build_waves", "1", None, DEFAULT_ROOT, SGT_MANIFEST) == []


def test_jobs_without_deployment_or_manifest_are_not_flagged():
    assert ig.job_problems("build_waves_smoke", "557", SGT_JOBS["build_waves_smoke"], SMOKE_ROOT, SMOKE_MANIFEST) == []


# --- history ----------------------------------------------------------------------------

def test_history_uses_latest_run_only():
    old_manifest = f"{U}/semanticGroundTruth/ground-truth-app/docs/plans/waves.json"
    runs = [run(3, SGT_MANIFEST), run(2, old_manifest)]  # project moved its manifest earlier
    assert ig.history_problems("1079", runs, SGT_MANIFEST) == []
    assert "latest run 3" in ig.history_problems("1079", runs, SMOKE_MANIFEST)[0]


def test_history_falls_back_to_default_and_skips_runs_without_it():
    runs = [{"run_id": 4, "job_parameters": []}, run(3, SGT_MANIFEST, value=False)]
    assert ig.history_problems("1079", runs, SGT_MANIFEST) == []
    assert ig.history_problems("1079", runs, SMOKE_MANIFEST)
    assert ig.history_problems("1079", [], SMOKE_MANIFEST) == []
    assert ig.history_problems("1079", runs, None) == []


# --- setup guard --------------------------------------------------------------------------

def _setup_jobs(jobs=SGT_JOBS):
    return {k: (IDS[k], jobs[k]) for k in IDS}


def test_setup_guard_after_bad_deploy():
    """The bad deploy rewrote names, defaults and metadata, so only the run history differs."""
    after = {
        "build_waves": job("[dev me] Build Waves Smoke: Build Waves", meta_root=SMOKE_ROOT, manifest=SMOKE_MANIFEST),
        "build_waves_smoke": job("[dev me] Build Waves Smoke: Build Waves Smoke Test", meta_root=SMOKE_ROOT),
        "setup_build_waves": job("[dev me] Build Waves Smoke: Build Waves Setup", meta_root=SMOKE_ROOT),
    }
    p = ig.setup_problems(_setup_jobs(after), SGT_RUNS, SMOKE_MANIFEST, SMOKE_ROOT, "Build Waves Smoke")
    assert p == [f"build job 1079: latest run 110 used manifest {SGT_MANIFEST}, this instance uses {SMOKE_MANIFEST}"]


def test_setup_guard_owner_passes_and_optional_inputs():
    assert ig.setup_problems(_setup_jobs(), SGT_RUNS, SGT_MANIFEST, DEFAULT_ROOT, "Semantic Ground Truth") == []
    # setup jobs deployed before root_path/project_name were passed
    assert ig.setup_problems(_setup_jobs(), SGT_RUNS, SGT_MANIFEST) == []


def test_setup_guard_wrong_root_name_and_missing_job():
    p = ig.setup_problems(_setup_jobs(), SGT_RUNS, SGT_MANIFEST, SMOKE_ROOT, "Agentic Trading")
    assert sum("expected the project name" in x for x in p) == 3
    assert any("setup_build_waves" in x and "was deployed from" in x for x in p)
    p = ig.setup_problems({"build_waves": ("1", None), "build_waves_smoke": ("", None)}, [], SGT_MANIFEST)
    assert p == ["build_waves: job 1 not found"]


def test_guard_message():
    assert ig.guard_message([]) == ""
    m = ig.guard_message(["a", "b"])
    assert m.startswith("INSTANCE_GUARD_FAILED: 2 problem(s)\n  - a\n  - b") and "force=true" in m
    assert "(force=true: continuing)" in ig.guard_message(["a"], force=True)


# --- deploy_instance.py --------------------------------------------------------------------

def _deploy_module():
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts", "deploy_instance.py")
    spec = importlib.util.spec_from_file_location("deploy_instance", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_var_flags_and_backup_path():
    d = _deploy_module()
    assert d.var_flags({"b": "x y", "a": 1, "c": None}) == ["--var=a=1", "--var=b=x y", "--var=c="]
    assert d.backup_path("/r/.databricks/bundle/dev") == "/r/.databricks/bundle/dev.bak"


def test_move_cache_aside_keeps_one_backup(tmp_path):
    d = _deploy_module()
    cache = tmp_path / ".databricks" / "bundle" / "dev"
    assert d.move_cache_aside(str(tmp_path), "dev") is None
    os.makedirs(cache)
    (cache / "resources.json").write_text("first")
    moved = d.move_cache_aside(str(tmp_path), "dev")
    assert moved.endswith("dev.bak") and not cache.exists()
    os.makedirs(cache)
    (cache / "resources.json").write_text("second")
    d.move_cache_aside(str(tmp_path), "dev")
    assert (tmp_path / ".databricks" / "bundle" / "dev.bak" / "resources.json").read_text() == "second"
    assert sorted(os.listdir(tmp_path / ".databricks" / "bundle")) == ["dev.bak"]


def test_post_deploy_problems():
    d = _deploy_module()
    jobs = {k: job(k, meta_root=SMOKE_ROOT) for k in IDS}
    new_ids = {"build_waves": "9", "build_waves_smoke": "8", "setup_build_waves": "7"}
    assert d.post_deploy_problems(summary(SMOKE_ROOT, new_ids), jobs, None) == []
    p = d.post_deploy_problems(summary(SMOKE_ROOT, new_ids), {**jobs, "build_waves": job("x", meta_root=DEFAULT_ROOT)},
                               {"build_waves_smoke": "557"})
    assert any("build_waves: job 9 metadata_file_path" in x for x in p)
    assert "build_waves_smoke: job ID changed from 557 to 8" in p
