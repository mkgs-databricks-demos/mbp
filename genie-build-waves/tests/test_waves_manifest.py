"""Manifest validation and task generation, including wave-level "archived": true."""

import copy
import json
import os

import pytest

import waves_manifest as wm

EXAMPLES = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "examples")
CFG = {"runner": "cfg/runner", "integrator": "cfg/integrator"}
GATE = "/gate/wave_gate_check.ipynb"


def _manifest():
    """One archived build-1 wave (that would break rule 7 if it ran) and one runnable build-2 wave."""
    return {
        "workflow": {"mode": "git"},
        "branch": "feature-x",
        "status_dir": ".build-status",
        "runtime_targets": {"app": {"type": "app", "name": "my-app"}},
        "waves": [
            {
                "wave_id": "1-0",
                "build": "1",
                "archived": True,
                "runtime_gate": ["app"],
                "sessions": [
                    # converge sharing a wave + no owned_paths: rule 7 error and owned_paths
                    # warning if this wave were runnable; skipped because it is archived.
                    {"session_id": "a1", "mode": "converge", "runtime_targets": ["app"], "owned_paths": ["app/**"]},
                    {"session_id": "a2", "mode": "edit"},
                ],
                "concurrency": 2,
            },
            {
                "wave_id": "2-0",
                "build": "2",
                "sessions": [
                    {"session_id": "b1", "mode": "edit", "owned_paths": ["src/**"], "depends_on": ["a1", "a2"]},
                    {"session_id": "b2", "mode": "edit", "owned_paths": ["docs/**"]},
                ],
            },
        ],
    }


# --- archived + runnable -------------------------------------------------------

def test_archived_wave_is_validated_but_skips_rule_7():
    errors, warnings = wm.validate_manifest(_manifest())
    assert errors == []
    assert not any("1-0" in w or "a2" in w for w in warnings), warnings


def test_same_wave_would_fail_rule_7_if_runnable():
    m = _manifest()
    del m["waves"][0]["archived"]
    errors, warnings = wm.validate_manifest(m)
    assert any("must be alone in their wave" in e for e in errors)
    assert any("concurrency forced to 1" in w for w in warnings)
    assert any("a2: edit session has no owned_paths" in w for w in warnings)


def test_archived_wave_generates_no_tasks():
    tasks = wm.generate_wave_tasks(_manifest(), CFG, GATE)
    keys = [t["task_key"] for t in tasks]
    assert keys == ["w2-0_sessions", "w2-0_integrate", "w2-0_gate", "w2-0_gate_check", "build_verdict"]
    # First runnable wave has no upstream dependency on the archived wave.
    assert "depends_on" not in tasks[0]
    # Session-level depends_on never becomes a task dependency.
    inputs = json.loads(tasks[0]["for_each_task"]["inputs"])
    assert [i["session_id"] for i in inputs] == ["b1", "b2"]
    assert tasks[2]["notebook_task"]["base_parameters"]["wave"] == "2-0"
    # Hyphenated task keys must be backtick-escaped inside dynamic value references.
    assert tasks[3]["condition_task"]["left"] == "{{tasks.`w2-0_gate`.values.gate_passed}}"


def test_ref_ident_escapes_only_when_needed():
    assert wm.ref_ident("w0_gate") == "w0_gate"
    assert wm.ref_ident("w4a_gate") == "w4a_gate"
    assert wm.ref_ident("w4-1_gate") == "`w4-1_gate`"


def test_archived_dependencies_are_satisfied():
    m = _manifest()
    b1 = m["waves"][1]["sessions"][0]
    assert wm.archived_session_ids(m) == {"a1", "a2"}
    assert wm.unmet_dependencies(m, b1) == []
    b1["depends_on"].append("b2")
    assert wm.unmet_dependencies(m, b1) == ["b2"]


def test_first_and_last_runnable_wave():
    m = _manifest()
    assert wm.first_runnable_wave_id(m) == "2-0"
    assert wm.last_runnable_wave_id(m) == "2-0"
    m["waves"].append({"wave_id": "0-9", "archived": True, "sessions": [{"session_id": "z", "owned_paths": ["z"]}]})
    assert wm.last_runnable_wave_id(m) == "2-0"  # a trailing archived wave is not "last"


def test_summary_line():
    assert wm.manifest_summary(_manifest()) == (
        "Manifest OK: 2 waves (1 archived, 1 runnable), 4 sessions, 1 runtime targets")


def test_archived_wave_keeps_id_and_target_checks():
    m = _manifest()
    m["waves"][0]["runtime_gate"] = ["app", "missing_target"]
    m["waves"][1]["sessions"][1]["session_id"] = "a2"  # duplicate of an archived session
    m["waves"].append(copy.deepcopy(m["waves"][0]) | {"wave_id": "1-0", "sessions": [{"session_id": "c1"}]})
    errors, _ = wm.validate_manifest(m)
    assert "wave 1-0: runtime_gate target 'missing_target' not in runtime_targets" in errors
    assert "duplicate session_id 'a2'" in errors
    assert "duplicate wave_id '1-0'" in errors


def test_archived_converge_target_must_exist():
    m = _manifest()
    m["waves"][0]["sessions"][0]["runtime_targets"] = ["nope"]
    errors, _ = wm.validate_manifest(m)
    assert "session a1: runtime target 'nope' not in runtime_targets" in errors


@pytest.mark.parametrize("value", ["yes", 1, None])
def test_archived_must_be_boolean(value):
    m = _manifest()
    m["waves"][0]["archived"] = value
    errors, _ = wm.validate_manifest(m)
    assert any("archived must be true or false" in e for e in errors)


@pytest.mark.parametrize("value,ok", [("4", True), (4, True), (True, False), (["4"], False)])
def test_build_label(value, ok):
    m = _manifest()
    m["waves"][1]["build"] = value
    errors, _ = wm.validate_manifest(m)
    assert (not any("build is an informational label" in e for e in errors)) == ok


def test_every_wave_archived_is_an_error():
    m = _manifest()
    m["waves"][1]["archived"] = True
    errors, _ = wm.validate_manifest(m)
    assert any("every wave is archived" in e for e in errors)


def test_wave_id_must_be_a_valid_task_prefix():
    m = _manifest()
    m["waves"][1]["wave_id"] = "2 0"
    errors, _ = wm.validate_manifest(m)
    assert any("wave_id must be" in e for e in errors)


def test_unknown_or_same_wave_dependency_warns():
    m = _manifest()
    m["waves"][1]["sessions"][0]["depends_on"] = ["ghost", "b2"]
    _, warnings = wm.validate_manifest(m)
    assert "session b1: depends_on 'ghost' is not a session in the manifest" in warnings
    assert "session b1: depends_on 'b2' is not in an earlier wave" in warnings


# --- backwards compatibility ---------------------------------------------------

@pytest.mark.parametrize("name", ["waves.json", "workspace-waves.json", "converge-waves.json"])
def test_examples_unchanged_without_archived(name):
    with open(os.path.join(EXAMPLES, name)) as f:
        m = json.load(f)
    errors, _ = wm.validate_manifest(m)
    assert errors == []
    tasks = wm.generate_wave_tasks(m, CFG, GATE)
    assert len(tasks) == 4 * len(m["waves"]) + 1  # + build_verdict
    # Wave chain: each wave's sessions depend on the previous wave's gate_check (outcome true).
    sessions_tasks = [t for t in tasks if t["task_key"].endswith("_sessions")]
    assert "depends_on" not in sessions_tasks[0]
    for prev, cur in zip(m["waves"], m["waves"][1:]):
        t = next(x for x in sessions_tasks if x["task_key"] == f"w{cur['wave_id']}_sessions")
        assert t["depends_on"] == [{"task_key": f"w{prev['wave_id']}_gate_check", "outcome": "true"}]
    # Plain wave ids keep the unescaped reference used before.
    for t in tasks:
        if t["task_key"].endswith("_gate_check"):
            assert t["condition_task"]["left"] == "{{tasks." + t["task_key"][:-6] + ".values.gate_passed}}"
    # "archived": false is the same as no flag.
    m2 = copy.deepcopy(m)
    for wv in m2["waves"]:
        wv["archived"] = False
    assert wm.generate_wave_tasks(m2, CFG, GATE) == tasks
    assert wm.manifest_summary(m).startswith(f"Manifest OK: {len(m['waves'])} waves (0 archived, ")


def test_retries_applied_to_genie_tasks_only():
    m = _manifest()
    m["task_retries"] = {"max_retries": 3, "min_retry_interval_seconds": 5}
    tasks = wm.generate_wave_tasks(m, CFG, GATE)
    inner = tasks[0]["for_each_task"]["task"]
    assert inner["max_retries"] == 3 and inner["min_retry_interval_millis"] == 5000
    assert tasks[1]["max_retries"] == 3
    assert "max_retries" not in tasks[2]  # gate notebook


# --- build_verdict ---------------------------------------------------------------

def test_verdict_task_depends_on_every_gate_all_done():
    m = _manifest()
    m["waves"].append({"wave_id": "2-1", "sessions": [{"session_id": "c1", "owned_paths": ["c/**"]}]})
    tasks = wm.generate_wave_tasks(m, CFG, GATE)
    v = tasks[-1]
    assert v["task_key"] == wm.VERDICT_TASK_KEY == "build_verdict"
    assert v["run_if"] == "ALL_DONE"
    # The notebook gates, not the If/else gate_check tasks: an EXCLUDED gate counts as done.
    assert v["depends_on"] == [{"task_key": "w2-0_gate"}, {"task_key": "w2-1_gate"}]
    assert v["notebook_task"]["notebook_path"] == "/gate/build_verdict.ipynb"
    assert v["notebook_task"]["base_parameters"] == {
        "run_id": "{{job.run_id}}", "build_root": "{{job.parameters.build_root}}",
        "manifest_path": "{{job.parameters.manifest_path}}"}
    assert "max_retries" not in v
    # The gate tasks themselves keep run_if ALL_DONE and the gate_check still reads gate_passed.
    assert next(t for t in tasks if t["task_key"] == "w2-1_gate")["run_if"] == "ALL_DONE"


def test_verdict_path_override_and_extension():
    assert wm.verdict_notebook_path("/a/b/wave_gate_check") == "/a/b/build_verdict"
    tasks = wm.generate_wave_tasks(_manifest(), CFG, GATE, verdict_path="/x/v.ipynb")
    assert tasks[-1]["notebook_task"]["notebook_path"] == "/x/v.ipynb"


# --- required_checks / source_file -------------------------------------------------

@pytest.mark.parametrize("value,ok", [(["tsc", "vitest"], True), ([], True), ("tsc", False),
                                      (["tsc", ""], False), (["tsc", "tsc"], False)])
def test_required_checks_validation(value, ok):
    m = _manifest()
    m["waves"][1]["required_checks"] = value
    errors, _ = wm.validate_manifest(m)
    assert (not any("required_checks" in e for e in errors)) == ok, errors


def _genie_manifest(**target):
    m = _manifest()
    m["runtime_targets"]["space"] = {"type": "genie_space", "id": "01f1", **target}
    return m


def test_source_file_validation():
    assert wm.validate_manifest(_genie_manifest(source_file="genie/x.geniespace.json"))[0] == []
    for bad in ("", "/abs/x.json", 3):
        errors, _ = wm.validate_manifest(_genie_manifest(source_file=bad))
        assert any("source_file must be a path relative to bundle_root" in e for e in errors), bad
    m = _manifest()
    m["runtime_targets"]["app"]["source_file"] = "x.json"
    assert any("source_file is only supported on genie_space" in e for e in wm.validate_manifest(m)[0])


def test_genie_space_without_source_warns_unless_freshness_off():
    _, warnings = wm.validate_manifest(_genie_manifest())
    assert any("without source_file or resource_key" in w for w in warnings)
    for t in ({"resource_key": "k"}, {"source_file": "x.json"}, {"require_fresh_deployment": False}):
        _, warnings = wm.validate_manifest(_genie_manifest(**t))
        assert not any("without source_file or resource_key" in w for w in warnings), t


def test_more_than_100_tasks_from_runnable_waves():
    """30 runnable waves after 22 archived ones: 120 wave tasks + build_verdict, chained from the first runnable wave."""
    waves = [{"wave_id": f"{b}-{n}", "archived": True, "sessions": [{"session_id": f"old{b}{n}", "owned_paths": ["x"]}]}
             for b in (1, 2, 3) for n in range(8)][:22]
    waves += [{"wave_id": f"4-{n}", "sessions": [{"session_id": f"s{n}", "owned_paths": [f"p{n}/**"]}]}
              for n in range(30)]
    m = {"waves": waves}
    assert wm.validate_manifest(m)[0] == []
    tasks = wm.generate_wave_tasks(m, CFG, GATE)
    assert len(tasks) == 121
    assert all(t["task_key"].startswith("w4-") for t in tasks[:-1])
    assert tasks[-1]["task_key"] == "build_verdict"
    assert len(tasks[-1]["depends_on"]) == 30
    assert "depends_on" not in tasks[0]
    assert wm.manifest_summary(m) == "Manifest OK: 52 waves (22 archived, 30 runnable), 52 sessions, 0 runtime targets"
