"""Tiered authorizations: validation, tiers 1-3, rendering, and the task graph wiring."""

import copy
import json

import authorizations as az
from waves_manifest import RUNNER_PARAMS, generate_wave_tasks, validate_manifest


def _m():
    """A Build 0-like manifest: session 06 converges a setup job, session 08 publishes skills."""
    return {
        "version": 1, "status_dir": ".build-status", "plans_dir": "docs/plans", "sessions_dir": "docs/sessions",
        "workflow": {"mode": "git"}, "bundle_target": "dev",
        "runtime_targets": {
            "setup_demo_job": {"type": "job", "name": "[dev] setup_demo", "id": "989657833792246",
                               "resource_key": "setup_demo"},
        },
        "authorization_policy": {
            "project_schema": "hls_fde_dev.uw_genie",
            "monitor_may_authorize": [
                {"action": "jobs.run_now", "scope": "own_runtime_targets"},
                {"action": "workspace.write", "scope": "owned_paths"},
                {"action": "uc_skills.publish", "scope": "project_schema"},
            ],
        },
        "waves": [
            {"wave_id": "0-2", "gate": ["ok"], "runtime_gate": ["setup_demo_job"], "sessions": [
                {"session_id": "06", "title": "Setup demo", "plan_file": "06.md", "scope": "deploy and run setup",
                 "mode": "converge", "owned_paths": ["src/setup/**"], "runtime_targets": ["setup_demo_job"]}]},
            {"wave_id": "0-4", "gate": ["ok"], "sessions": [
                {"session_id": "08", "title": "Skills", "plan_file": "08.md", "scope": "publish skills",
                 "owned_paths": ["skills/**"],
                 "authorizations": [{"action": "uc_skills.publish", "target": "hls_fde_dev.uw_genie",
                                     "reason": "publish 4 demo skills"}]}]},
        ],
    }


def _session(m, sid):
    return next(s for wv in m["waves"] for s in wv["sessions"] if s["session_id"] == sid)


def test_build0_manifest_is_valid():
    errors, _ = validate_manifest(_m())
    assert errors == []


def test_tier1_converge_session_may_deploy_and_run_its_job_with_the_id():
    m = _m()
    text = az.render_authorizations(m, _session(m, "06"))
    assert text.startswith(az.HEADING)
    assert "`bundle.deploy`" in text and "`jobs.run_now`" in text
    assert "id 989657833792246" in text and "tier 1" in text


def test_authorize_run_false_drops_the_run_approval_only():
    m = _m()
    m["runtime_targets"]["setup_demo_job"]["authorize_run"] = False
    actions = [e["action"] for e in az.session_authorizations(m, _session(m, "06"))]
    assert actions == ["bundle.deploy"]


def test_implied_false_turns_tier1_off():
    m = _m()
    m["authorization_policy"]["implied"] = False
    assert az.render_authorizations(m, _session(m, "06")) == az.NONE_TEXT


def test_tier2_owner_entry_is_rendered():
    m = _m()
    text = az.render_authorizations(m, _session(m, "08"))
    assert "`uc_skills.publish` on `hls_fde_dev.uw_genie` (publish 4 demo skills; tier 2)" in text


def test_edit_session_without_entries_gets_none_text():
    m = _m()
    _session(m, "08").pop("authorizations")
    assert az.render_authorizations(m, _session(m, "08")) == az.NONE_TEXT


def test_owner_only_unknown_and_missing_target_are_errors():
    m = _m()
    _session(m, "08")["authorizations"] = [
        {"action": "permissions.change", "target": "job 1"},
        {"action": "jobs.delete", "target": "job 1"},
        {"action": "jobs.run_now", "target": "runtime_target:nope"},
    ]
    errors, _ = validate_manifest(m)
    assert any("owner-only (tier 4)" in e for e in errors)
    assert any("unknown action 'jobs.delete'" in e for e in errors)
    assert any("'runtime_target:nope' is not in runtime_targets" in e for e in errors)


def test_monitor_policy_cannot_allow_owner_only_or_bad_scope():
    m = _m()
    m["authorization_policy"]["monitor_may_authorize"] = [
        {"action": "uc.grant", "scope": "owned_assets"},
        {"action": "jobs.run_now", "scope": "anything"},
    ]
    errors, _ = validate_manifest(m)
    assert any("owner-only" in e for e in errors)
    assert any("scope must be one of" in e for e in errors)


def test_project_schema_scope_needs_project_schema():
    m = _m()
    del m["authorization_policy"]["project_schema"]
    errors, _ = validate_manifest(m)
    assert any("needs authorization_policy.project_schema" in e for e in errors)


def test_approval_wording_in_context_notes_warns():
    m = _m()
    _session(m, "06")["context_notes"] = "The owner authorizes run-now on job 989657833792246."
    _, warnings = validate_manifest(m)
    assert any("context_notes mention approval" in w for w in warnings)


def test_monitor_grants_are_kept_only_inside_policy_and_own_targets():
    m = _m()
    ev = "Auto Mode refused run-now, run 121608533170151"
    grants = {"grants": [
        {"action": "jobs.run_now", "target": "runtime_target:setup_demo_job", "session": "06", "evidence": ev},
        {"action": "jobs.run_now", "target": "runtime_target:setup_demo_job", "session": "08", "evidence": ev},
        {"action": "workspace.write", "target": "skills/a/SKILL.md", "session": "08", "evidence": ev},
        {"action": "workspace.write", "target": "/Workspace/Shared/x", "session": "08", "evidence": ev},
        {"action": "uc_skills.publish", "target": "hls_fde_dev.uw_genie", "session": "08", "evidence": ev},
        {"action": "uc_skills.publish", "target": "other.schema", "session": "08", "evidence": ev},
        {"action": "uc.grant", "target": "hls_fde_dev.uw_genie", "session": "08", "evidence": ev},
        {"action": "jobs.run_now", "target": "runtime_target:setup_demo_job", "session": "06"},
        {"action": "jobs.run_now", "target": "runtime_target:setup_demo_job", "session": "99", "evidence": ev},
    ]}
    kept, dropped = az.filter_monitor_grants(m, grants)
    assert [(e["action"], e["target"]) for e in kept["06"]] == [("jobs.run_now", "runtime_target:setup_demo_job")]
    assert [(e["action"], e["target"]) for e in kept["08"]] == [
        ("workspace.write", "skills/a/SKILL.md"), ("uc_skills.publish", "hls_fde_dev.uw_genie")]
    assert len(dropped) == 6
    reasons = " | ".join(r for _, r in dropped)
    assert "owner-only" in reasons and "evidence" in reasons and "not a runnable session" in reasons


def test_monitor_grant_is_labelled_and_deduplicated():
    m = _m()
    _session(m, "08").pop("authorizations")
    kept, _ = az.filter_monitor_grants(m, [
        {"action": "uc_skills.publish", "target": "hls_fde_dev.uw_genie", "session": "08", "evidence": "refused"}])
    text = az.render_authorizations(m, _session(m, "08"), kept)
    assert "granted by the build monitor within the owner's policy" in text
    m2 = _m()  # owner entry already covers it: rendered once, as tier 2
    entries = az.session_authorizations(m2, _session(m2, "08"), kept)
    assert [e["tier"] for e in entries] == [2]


def test_monitor_grants_file_default_and_override():
    m = _m()
    assert az.grants_file(m) == "docs/plans/authorizations.monitor.json"
    m["authorization_policy"]["monitor_grants_file"] = "ops/grants.json"
    assert az.grants_file(m) == "ops/grants.json"
    m["authorization_policy"]["monitor_grants_file"] = "/abs/grants.json"
    errors, _ = validate_manifest(m)
    assert any("monitor_grants_file" in e for e in errors)


def test_rendered_text_is_one_line():
    m = _m()
    for sid in ("06", "08"):
        assert "\n" not in az.render_authorizations(m, _session(m, sid))


def test_task_graph_carries_authorizations_in_inputs():
    m = _m()
    kept, _ = az.filter_monitor_grants(m, [
        {"action": "workspace.write", "target": "skills/x.md", "session": "08", "evidence": "refused"}])
    tasks = generate_wave_tasks(m, {"runner": "r", "integrator": "i"}, "/x/wave_gate_check.ipynb",
                                monitor_kept=kept)
    for_each = [t for t in tasks if "for_each_task" in t and t["task_key"].endswith("_sessions")]
    assert len(for_each) == 2
    for t in for_each:
        inner = t["for_each_task"]["task"]["genie_task"]["parameters"]
        assert inner["authorizations"] == "{{input.authorizations}}"
        assert set(inner) <= set(RUNNER_PARAMS)
        for i in json.loads(t["for_each_task"]["inputs"]):
            assert i["authorizations"].startswith(az.HEADING)
    w08 = json.loads(for_each[1]["for_each_task"]["inputs"])
    assert "skills/x.md" in az.inputs_authorizations(w08, "08")
    # Continuation passes reuse the same inner parameters.
    cont = [t for t in tasks if t["task_key"].endswith("_continue")]
    assert cont and all(t["for_each_task"]["task"]["genie_task"]["parameters"]["authorizations"]
                        == "{{input.authorizations}}" for t in cont)


def test_inputs_authorizations_handles_json_and_misses():
    inputs = json.dumps([{"session_id": "06", "title": "t", "authorizations": "A"}])
    assert az.inputs_authorizations(inputs, "06") == "A"
    assert az.inputs_authorizations(inputs, "07") is None
    assert az.inputs_authorizations("not json", "06") is None


def test_parameter_overrides_flags_changed_and_undeclared():
    defs = [{"name": "branch", "default": "b1"}, {"name": "empty", "default": ""}]
    run = [{"name": "branch", "default": "b1", "value": "b1"},
           {"name": "empty", "default": "", "value": ""},
           {"name": "session_id", "default": "", "value": "99"}]
    assert az.parameter_overrides(run, defs) == ["session_id (not declared by the job)"]
    run[0]["value"] = "main"
    out = az.parameter_overrides(run, defs)
    assert out[0].startswith("branch (default 'b1', run used 'main')") and len(out) == 2
    assert az.parameter_overrides(None, defs) == []


def test_validate_does_not_mutate():
    m = _m()
    before = copy.deepcopy(m)
    validate_manifest(m)
    az.filter_monitor_grants(m, [])
    assert m == before


def _deploy_m(**session):
    s = {"session_id": "12", "title": "Register", "plan_file": "12.md", "mode": "edit", "allow_deploy": True,
         "owned_paths": ["examples/mv/**"], "scope": "deploy the metric views bundle"}
    s.update(session)
    return {"version": 1, "workflow": {"mode": "git"}, "branch": "feature-x",
            "waves": [{"wave_id": "0-6", "gate": ["ok"], "sessions": [s]}]}


def test_allow_deploy_without_named_bundle_or_run_approval_warns():
    # The case that failed a real wave: deploy approved, `bundle run` of the job refused.
    m = _deploy_m(scope="deploy examples/mv and bundle run register_metric_views -t dev")
    _, warnings = az.validate_authorizations(m)
    assert any("bundle.deploy only for the bundle at build_root" in w for w in warnings)
    assert any("no jobs.run_now authorization" in w for w in warnings)


def test_named_deploy_and_run_approvals_silence_the_warnings():
    m = _deploy_m(scope="deploy examples/mv and bundle run register_metric_views -t dev", authorizations=[
        {"action": "bundle.deploy", "target": "bundle:examples/mv"},
        {"action": "jobs.run_now", "target": "register_metric_views (dev)"}])
    errors, warnings = az.validate_authorizations(m)
    assert errors == [] and az.deploy_approval_warnings(m, m["waves"][0]["sessions"][0]) == []
    assert not [w for w in warnings if "session 12" in w]


def test_run_words_in_owned_assets_or_notes_count_and_non_deploy_sessions_are_ignored():
    m = _deploy_m(owned_assets=["dev job register_metric_views (run-now)"],
                  authorizations=[{"action": "bundle.deploy", "target": "bundle:examples/mv"}])
    assert [w for w in az.deploy_approval_warnings(m, m["waves"][0]["sessions"][0]) if "jobs.run_now" in w]
    s = {"session_id": "13", "mode": "edit", "scope": "bundle run something"}  # no allow_deploy
    assert az.deploy_approval_warnings(m, s) == []


def test_converge_session_with_its_own_job_target_needs_nothing_more():
    m = _m()
    s = _session(m, "06")
    s["scope"] = "deploy and bundle run setup_demo"
    assert az.deploy_approval_warnings(m, s) == []


def test_scope_run_of_a_snake_case_job_counts():
    m = _deploy_m(scope="deploy examples/mv to dev, run register_metric_views, fix until it passes")
    assert [w for w in az.deploy_approval_warnings(m, m["waves"][0]["sessions"][0]) if "jobs.run_now" in w]


def test_plan_text_finds_a_run_the_manifest_does_not_mention():
    m = _deploy_m(scope="tune the metric views with re-registration",
                  authorizations=[{"action": "bundle.deploy", "target": "bundle:examples/mv"}])
    assert az.deploy_approval_warnings(m, m["waves"][0]["sessions"][0]) == []
    plans = {"12.md": "Re-register with `bundle run register_metric_views -t dev`."}
    warnings = az.plan_deploy_warnings(m, lambda s: plans.get(s["plan_file"]))
    assert len(warnings) == 1 and "jobs.run_now" in warnings[0] and "(found in plan 12.md)" in warnings[0]
    # Missing or unreadable plans are skipped, and manifest-level warnings are not repeated.
    assert az.plan_deploy_warnings(m, lambda s: None) == []
    assert az.plan_deploy_warnings(m, lambda s: (_ for _ in ()).throw(OSError("x"))) == []
    m2 = _deploy_m(scope="bundle run register_metric_views",
                   authorizations=[{"action": "bundle.deploy", "target": "bundle:examples/mv"}])
    assert az.plan_deploy_warnings(m2, lambda s: plans.get(s["plan_file"])) == []


def test_archived_waves_skip_deploy_approval_warnings():
    m = _deploy_m(scope="bundle run register_metric_views")
    m["waves"][0]["archived"] = True
    assert not [w for w in az.validate_authorizations(m)[1] if "session 12" in w]
