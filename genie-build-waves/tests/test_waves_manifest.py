"""Manifest validation and task generation, including wave-level "archived": true and continuation passes."""

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


def _by_key(tasks):
    return {t["task_key"]: t for t in tasks}


def _deps(task):
    return [d["task_key"] for d in task.get("depends_on") or []]


BASE_KEYS = ["w2-0_sessions", "w2-0_integrate", "w2-0_gate", "w2-0_gate_check", "build_verdict"]
PASS1_KEYS = ["w2-0_sessions", "w2-0_find_incomplete", "w2-0_has_incomplete", "w2-0_continue",
              "w2-0_integrate", "w2-0_gate", "w2-0_gate_check", "build_verdict"]


def test_archived_wave_generates_no_tasks():
    tasks = wm.generate_wave_tasks(_manifest(), CFG, GATE)
    keys = [t["task_key"] for t in tasks]
    assert keys == PASS1_KEYS
    by = _by_key(tasks)
    # First runnable wave has no upstream dependency on the archived wave.
    assert "depends_on" not in tasks[0]
    # Session-level depends_on never becomes a task dependency.
    inputs = json.loads(tasks[0]["for_each_task"]["inputs"])
    assert [i["session_id"] for i in inputs] == ["b1", "b2"]
    assert by["w2-0_gate"]["notebook_task"]["base_parameters"]["wave"] == "2-0"
    # Hyphenated task keys must be backtick-escaped inside dynamic value references.
    assert by["w2-0_gate_check"]["condition_task"]["left"] == "{{tasks.`w2-0_gate`.values.gate_passed}}"


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
        "Manifest OK: 2 waves (1 archived, 1 runnable), 4 sessions, 1 runtime targets, "
        "1 continuation pass(es) per wave, 8 job tasks")


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
    assert len(tasks) == 7 * len(m["waves"]) + 1  # 4 wave tasks + 3 for one continuation pass, + build_verdict
    # continuation_passes 0 gives the graph from before continuation passes.
    assert len(wm.generate_wave_tasks({**m, "continuation_passes": 0}, CFG, GATE)) == 4 * len(m["waves"]) + 1
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
    by = _by_key(wm.generate_wave_tasks(m, CFG, GATE))
    for fe in ("w2-0_sessions", "w2-0_continue"):
        inner = by[fe]["for_each_task"]["task"]
        assert inner["max_retries"] == 3 and inner["min_retry_interval_millis"] == 5000
    assert by["w2-0_integrate"]["max_retries"] == 3
    assert "max_retries" not in by["w2-0_gate"]  # gate notebook
    assert "max_retries" not in by["w2-0_find_incomplete"]  # find notebook


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
    """30 runnable waves after 22 archived ones: 210 wave tasks + build_verdict, chained from the first runnable wave."""
    waves = [{"wave_id": f"{b}-{n}", "archived": True, "sessions": [{"session_id": f"old{b}{n}", "owned_paths": ["x"]}]}
             for b in (1, 2, 3) for n in range(8)][:22]
    waves += [{"wave_id": f"4-{n}", "sessions": [{"session_id": f"s{n}", "owned_paths": [f"p{n}/**"]}]}
              for n in range(30)]
    m = {"waves": waves}
    assert wm.validate_manifest(m)[0] == []
    tasks = wm.generate_wave_tasks(m, CFG, GATE)
    assert len(tasks) == 211  # 30 waves x (4 + 3 continuation) + build_verdict
    assert all(t["task_key"].startswith("w4-") for t in tasks[:-1])
    assert tasks[-1]["task_key"] == "build_verdict"
    assert len(tasks[-1]["depends_on"]) == 30
    assert "depends_on" not in tasks[0]
    assert wm.manifest_summary(m) == ("Manifest OK: 52 waves (22 archived, 30 runnable), 52 sessions, "
                                      "0 runtime targets, 1 continuation pass(es) per wave, 211 job tasks")


# --- continuation passes -----------------------------------------------------------

def test_continuation_pass_graph():
    m = _manifest()
    m["waves"][1]["sessions"][0]["timeout_minutes"] = 90
    m["waves"][1]["concurrency"] = 2
    by = _by_key(wm.generate_wave_tasks(m, CFG, GATE))

    find = by["w2-0_find_incomplete"]
    assert _deps(find) == ["w2-0_sessions"] and find["run_if"] == "ALL_DONE"
    assert find["notebook_task"]["notebook_path"] == "/gate/find_incomplete_sessions.ipynb"
    assert find["notebook_task"]["base_parameters"] == {
        "wave": "2-0", "continuation": "1", "run_id": "{{job.run_id}}",
        "build_root": "{{job.parameters.build_root}}", "manifest_path": "{{job.parameters.manifest_path}}"}
    assert find["timeout_seconds"] == wm.FIND_INCOMPLETE_TIMEOUT_MIN * 60

    has = by["w2-0_has_incomplete"]
    assert _deps(has) == ["w2-0_find_incomplete"]
    assert has["condition_task"] == {"op": "EQUAL_TO", "right": "true",
                                     "left": "{{tasks.`w2-0_find_incomplete`.values.has_incomplete}}"}

    cont = by["w2-0_continue"]
    assert cont["depends_on"] == [{"task_key": "w2-0_has_incomplete", "outcome": "true"}]
    fe = cont["for_each_task"]
    assert fe["inputs"] == "{{tasks.`w2-0_find_incomplete`.values.incomplete}}"
    assert fe["concurrency"] == by["w2-0_sessions"]["for_each_task"]["concurrency"] == 2
    inner, first = fe["task"], by["w2-0_sessions"]["for_each_task"]["task"]
    assert inner["task_key"] == "w2-0_continue_session"
    assert inner["genie_task"]["configuration_id"] == CFG["runner"]
    assert inner["genie_task"]["parameters"] == {**first["genie_task"]["parameters"], "continuation": "1"}
    assert first["genie_task"]["parameters"]["continuation"] == "0"
    assert inner["timeout_seconds"] == first["timeout_seconds"] == 90 * 60
    assert inner["description"] == "{{input.session_id}}: {{input.title}} (continuation 1)"

    integ = by["w2-0_integrate"]
    # Depends on the find task too: if every dependency were Excluded, the integrator would be Excluded.
    assert _deps(integ) == ["w2-0_find_incomplete", "w2-0_continue"] and integ["run_if"] == "ALL_DONE"


def test_continuation_passes_zero_is_the_previous_graph():
    m = {**_manifest(), "continuation_passes": 0}
    tasks = wm.generate_wave_tasks(m, CFG, GATE)
    assert [t["task_key"] for t in tasks] == BASE_KEYS
    assert _deps(_by_key(tasks)["w2-0_integrate"]) == ["w2-0_sessions"]
    assert wm.manifest_summary(m).endswith("0 continuation pass(es) per wave, 5 job tasks")


def test_three_passes_chain_through_find_tasks():
    m = _manifest()
    m["waves"].append({"wave_id": "2-1", "sessions": [{"session_id": "c1", "owned_paths": ["c/**"]}]})
    m["continuation_passes"] = 3
    assert wm.validate_manifest(m)[0] == []
    tasks = wm.generate_wave_tasks(m, CFG, GATE)
    by = _by_key(tasks)
    assert [t["task_key"] for t in tasks][:11] == [
        "w2-0_sessions",
        "w2-0_find_incomplete", "w2-0_has_incomplete", "w2-0_continue",
        "w2-0_find_incomplete2", "w2-0_has_incomplete2", "w2-0_continue2",
        "w2-0_find_incomplete3", "w2-0_has_incomplete3", "w2-0_continue3",
        "w2-0_integrate"]
    # A pass that finds nothing Excludes its continue task; the next find still runs via the previous find.
    assert _deps(by["w2-0_find_incomplete2"]) == ["w2-0_find_incomplete", "w2-0_continue"]
    assert _deps(by["w2-0_find_incomplete3"]) == ["w2-0_find_incomplete2", "w2-0_continue2"]
    assert all(by[f"w2-0_find_incomplete{s}"]["run_if"] == "ALL_DONE" for s in ("", "2", "3"))
    assert _deps(by["w2-0_integrate"]) == ["w2-0_find_incomplete3", "w2-0_continue3"]
    assert by["w2-0_continue3"]["for_each_task"]["task"]["task_key"] == "w2-0_continue3_session"
    assert by["w2-0_continue3"]["for_each_task"]["task"]["genie_task"]["parameters"]["continuation"] == "3"
    assert by["w2-0_find_incomplete2"]["notebook_task"]["base_parameters"]["continuation"] == "2"
    # The next wave still chains on the gate check, and only notebook gates feed build_verdict.
    assert by["w2-1_sessions"]["depends_on"] == [{"task_key": "w2-0_gate_check", "outcome": "true"}]
    assert _deps(by["build_verdict"]) == ["w2-0_gate", "w2-1_gate"]
    assert len(tasks) == 2 * (4 + 3 * 3) + 1
    # Every key is unique and within the 100-character limit.
    assert len(by) == len(tasks) and all(len(k) <= 100 for k in by)


def test_plain_wave_id_keeps_unescaped_references():
    m = {"waves": [{"wave_id": "5", "sessions": [{"session_id": "s", "owned_paths": ["s/**"]}]}]}
    by = _by_key(wm.generate_wave_tasks(m, CFG, GATE))
    assert by["w5_has_incomplete"]["condition_task"]["left"] == "{{tasks.w5_find_incomplete.values.has_incomplete}}"
    assert by["w5_continue"]["for_each_task"]["inputs"] == "{{tasks.w5_find_incomplete.values.incomplete}}"


@pytest.mark.parametrize("value,ok", [(0, True), (1, True), (3, True), (4, False), (-1, False),
                                      (True, False), ("1", False), (1.5, False)])
def test_continuation_passes_validation(value, ok):
    m = {**_manifest(), "continuation_passes": value}
    errors, _ = wm.validate_manifest(m)
    assert (not any("continuation_passes" in e for e in errors)) == ok, errors


def _genie_tasks(tasks):
    for t in tasks:
        if "genie_task" in t:
            yield t
        inner = (t.get("for_each_task") or {}).get("task")
        if inner and "genie_task" in inner:
            yield inner


@pytest.mark.parametrize("name", ["waves.json", "workspace-waves.json", "converge-waves.json", None])
def test_every_genie_parameter_reaches_the_prompt(name):
    """setup puts a {{param}} placeholder in the prompt only for RUNNER_PARAMS / INTEGRATOR_PARAMS.

    Each generated parameter must be listed (or the agent never sees it), and each listed
    parameter must get a value (or the agent sees a literal {{param}}).
    """
    m = _manifest() if name is None else json.load(open(os.path.join(EXAMPLES, name)))
    m = {**m, "continuation_passes": 2}
    seen = 0
    for t in _genie_tasks(wm.generate_wave_tasks(m, CFG, GATE)):
        params = set(t["genie_task"]["parameters"])
        expected = wm.RUNNER_PARAMS if t["genie_task"]["configuration_id"] == CFG["runner"] else wm.INTEGRATOR_PARAMS
        assert params == set(expected), (t["task_key"], params ^ set(expected))
        seen += 1
    assert seen >= 3
    assert "continuation" in wm.RUNNER_PARAMS


def test_passes_in_run_reads_task_keys():
    tasks = wm.generate_wave_tasks({**_manifest(), "continuation_passes": 3}, CFG, GATE)
    keys = [t["task_key"] for t in tasks]
    assert wm.passes_in_run("w2-0", keys) == 3
    assert wm.passes_in_run("w2-0", [k for k in keys if not k.startswith("w2-0_continue3")]) == 2
    assert wm.passes_in_run("w2-0", ["w2-0_sessions", "w2-0_integrate"]) == 0
    assert wm.passes_in_run("w9", keys) == 0
    assert wm.passes_in_run("w2-0", None) == 0


def test_wave_level_continuation_passes_override():
    m = _manifest()
    m["continuation_passes"] = 2
    m["waves"].append({"wave_id": "2-1", "continuation_passes": 0,
                       "sessions": [{"session_id": "c1", "owned_paths": ["c/**"]}]})
    m["waves"].append({"wave_id": "2-2", "continuation_passes": 3,
                       "sessions": [{"session_id": "d1", "owned_paths": ["d/**"]}]})
    assert wm.validate_manifest(m)[0] == []
    tasks = wm.generate_wave_tasks(m, CFG, GATE)
    keys = [t["task_key"] for t in tasks]
    assert wm.passes_in_run("w2-0", keys) == 2
    assert wm.passes_in_run("w2-1", keys) == 0
    assert wm.passes_in_run("w2-2", keys) == 3
    assert _deps(_by_key(tasks)["w2-1_integrate"]) == ["w2-1_sessions"]
    assert len(tasks) == wm.job_task_count(m) == (4 + 6) + 4 + (4 + 9) + 1


@pytest.mark.parametrize("value", [4, -1, True, "1"])
def test_wave_level_continuation_passes_validation(value):
    m = _manifest()
    m["waves"][1]["continuation_passes"] = value
    errors, _ = wm.validate_manifest(m)
    assert any("wave 2-0: continuation_passes" in e for e in errors), errors


def test_invalid_continuation_passes_fall_back():
    wave = {"wave_id": "x", "continuation_passes": "2"}
    assert wm.continuation_passes({"continuation_passes": 9}) == wm.DEFAULT_CONTINUATION_PASSES
    assert wm.continuation_passes({"continuation_passes": 2}, wave) == 2  # bad wave value -> manifest
    assert wm.continuation_passes({}, {"continuation_passes": 0}) == 0
    assert wm.continuation_passes({}) == 1


def test_task_count_over_job_limit_is_an_error():
    m = {"continuation_passes": 3, "waves": [
        {"wave_id": f"{i}", "sessions": [{"session_id": f"s{i}", "owned_paths": [f"s{i}/**"]}]}
        for i in range(77)]}  # 77 x 13 + 1 = 1002
    errors, _ = wm.validate_manifest(m)
    assert wm.job_task_count(m) == 1002 == len(wm.generate_wave_tasks(m, CFG, GATE))
    assert any("1002 tasks" in e and "1000" in e for e in errors), errors
    m["continuation_passes"] = 2  # 77 x 10 + 1 = 771
    assert not any("tasks;" in e for e in wm.validate_manifest(m)[0])


def test_deploying_wave_continue_is_single_writer():
    m = {"runtime_targets": {"app": {"type": "app", "name": "a"}}, "waves": [
        {"wave_id": "c", "concurrency": 4, "runtime_gate": ["app"],
         "sessions": [{"session_id": "c1", "mode": "converge", "runtime_targets": ["app"],
                       "owned_paths": ["app/**"]}]}]}
    by = _by_key(wm.generate_wave_tasks(m, CFG, GATE))
    assert by["wc_sessions"]["for_each_task"]["concurrency"] == 1
    assert by["wc_continue"]["for_each_task"]["concurrency"] == 1
    assert by["wc_continue"]["for_each_task"]["task"]["timeout_seconds"] == 180 * 60


def test_longest_wave_id_keeps_keys_under_limit():
    wid = "a-" * 29 + "zz"  # 60 characters, needs backticks
    assert len(wid) == 60
    m = {"continuation_passes": 3, "waves": [{"wave_id": wid, "sessions": [{"session_id": "s", "owned_paths": ["s/**"]}]}]}
    assert wm.validate_manifest(m)[0] == []
    tasks = wm.generate_wave_tasks(m, CFG, GATE)
    keys = [t["task_key"] for t in tasks] + [t["for_each_task"]["task"]["task_key"] for t in tasks if "for_each_task" in t]
    assert max(len(k) for k in keys) <= 100
    by = _by_key(tasks)
    assert by[f"w{wid}_continue3"]["for_each_task"]["inputs"] == "{{tasks.`w" + wid + "_find_incomplete3`.values.incomplete}}"


def test_find_incomplete_path_override_and_extension():
    assert wm.find_incomplete_notebook_path("/a/b/wave_gate_check") == "/a/b/find_incomplete_sessions"
    by = _by_key(wm.generate_wave_tasks(_manifest(), CFG, GATE, find_incomplete_path="/x/f.ipynb"))
    assert by["w2-0_find_incomplete"]["notebook_task"]["notebook_path"] == "/x/f.ipynb"
