"""Gate result / run verdict, required checks, and Genie space content matching for freshness."""

import json
import os

import gate_helpers as gh


# --- gate failure message --------------------------------------------------------------

def test_gate_failure_message_is_tagged_and_bounded():
    probs = [f"p{i}" for i in range(25)]
    msg = gh.gate_failure_message("4-1", probs)
    assert msg.startswith("GATE_FAILED: wave 4-1: 25 problem(s)")
    assert "  - p19" in msg and "  - p20" not in msg
    assert "and 5 more (see wave_4-1_gate_result.json)" in msg
    assert gh.gate_result_path("/s/123", "4-1") == "/s/123/wave_4-1_gate_result.json"


# --- run verdict -------------------------------------------------------------------------

def test_latest_task_states_keeps_latest_attempt():
    tasks = [
        {"task_key": "w1_gate", "attempt_number": 0, "state": {"result_state": "SUCCESS"}},
        {"task_key": "w1_gate", "attempt_number": 2, "state": {"result_state": "FAILED"}},
        {"task_key": "w1_gate", "attempt_number": 1, "state": {"result_state": "SUCCESS"}},
        {"task_key": "w2_gate", "attempt_number": 0, "state": {"result_state": "EXCLUDED"}},
    ]
    assert gh.latest_task_states(tasks) == {"w1_gate": "FAILED", "w2_gate": "EXCLUDED"}


def test_verdict_passes_when_every_run_gate_passed():
    states = {"w1_gate": "SUCCESS", "w2_gate": "SUCCESS"}
    v = gh.build_verdict(["1", "2"], states, {"1": {"status": "pass"}, "2": {"status": "pass"}})
    assert v["passed"] and v["checked"] == 2 and not v["warning"]
    assert gh.verdict_message(v) == "BUILD_PASSED: 2 wave gate(s) passed"


def test_verdict_fails_on_failed_gate_and_ignores_excluded_waves():
    states = {"w1_gate": "SUCCESS", "w2_gate": "SUCCESS", "w3_gate": "EXCLUDED"}
    results = {"1": {"status": "pass"}, "2": {"status": "fail", "problems": ["session 33 hit the step limit"]}}
    v = gh.build_verdict(["1", "2", "3"], states, results)
    assert not v["passed"] and v["failed"] == ["2"]
    assert [e["result"] for e in v["waves"]] == ["pass", "fail", "excluded"]
    msg = gh.verdict_message(v)
    assert msg.startswith("BUILD_FAILED: 1 wave gate(s) failed: 2")
    assert "  - session 33 hit the step limit" in msg
    assert "repair from w2_integrate" in msg


def test_verdict_fails_on_crashed_gate_or_missing_result():
    v = gh.build_verdict(["1", "2"], {"w1_gate": "FAILED", "w2_gate": "SUCCESS"}, {})
    assert v["failed"] == ["1", "2"]
    assert "gate task ended FAILED" in v["waves"][0]["problems"][0]
    assert "wrote no result file" in v["waves"][1]["problems"][0]
    v = gh.build_verdict(["1"], {"w1_gate": "UPSTREAM_FAILED"}, {"1": {"status": "pass"}})
    assert not v["passed"]  # a stale pass file never overrides the task state


def test_verdict_only_subset_and_api_fallback():
    # `only` run: earlier waves are not in the run at all.
    v = gh.build_verdict(["1", "2"], {"w2_gate": "SUCCESS"}, {"2": {"status": "pass"}})
    assert v["passed"] and [e["result"] for e in v["waves"]] == ["not_in_run", "pass"]
    # Jobs API unavailable: result files alone.
    v = gh.build_verdict(["1", "2"], None, {"1": {"status": "fail", "problems": ["x"]}})
    assert not v["passed"] and not v["api_used"]
    assert [e["result"] for e in v["waves"]] == ["fail", "no_result"]


def test_verdict_ignores_disabled_waves():
    # Waves done in an earlier run are disabled in the job: their gate task ends DISABLED.
    # A stale result file from an older attempt must not count either.
    states = {"w1_gate": "DISABLED", "w2_gate": "DISABLED", "w3_gate": "SUCCESS", "w4_gate": "EXCLUDED"}
    results = {"1": {"status": "fail", "problems": ["old"]}, "3": {"status": "pass"}}
    v = gh.build_verdict(["1", "2", "3", "4"], states, results)
    assert v["passed"] and v["failed"] == [] and v["checked"] == 1
    assert [e["result"] for e in v["waves"]] == ["disabled", "disabled", "pass", "excluded"]
    assert v["disabled"] == ["1", "2"]
    assert gh.verdict_message(v) == "BUILD_PASSED: 1 wave gate(s) passed (2 disabled wave(s) skipped: 1, 2)"
    # A real failure after disabled waves still fails the run, and names only that wave.
    v = gh.build_verdict(["1", "2"], {"w1_gate": "DISABLED", "w2_gate": "SUCCESS"},
                         {"2": {"status": "fail", "problems": ["p"]}})
    assert not v["passed"] and v["failed"] == ["2"]
    msg = gh.verdict_message(v)
    assert msg.startswith("BUILD_FAILED: 1 wave gate(s) failed: 2 (1 disabled wave(s) skipped: 1)")
    assert "repair from w2_integrate" in msg


def test_verdict_warns_when_no_gate_was_checked():
    # Every wave disabled (even with stale result files): the run succeeds, but as a warning.
    v = gh.build_verdict(["1", "2"], {"w1_gate": "DISABLED", "w2_gate": "DISABLED"},
                         {"1": {"status": "pass"}, "2": {"status": "fail", "problems": ["old"]}})
    assert v["passed"] and v["warning"] and v["checked"] == 0
    assert gh.verdict_message(v) == "BUILD_WARNING: no wave gate was checked in this run (2 disabled: 1, 2)"
    # Disabled plus `only`-subset waves: the other results are counted.
    v = gh.build_verdict(["1", "2", "3"], {"w1_gate": "DISABLED"}, {})
    assert v["warning"]
    assert gh.verdict_message(v) == \
        "BUILD_WARNING: no wave gate was checked in this run (1 disabled: 1; 2 not in run)"
    # One checked gate is a normal pass, not a warning; a failure is never a warning.
    v = gh.build_verdict(["1", "2"], {"w1_gate": "DISABLED", "w2_gate": "SUCCESS"}, {"2": {"status": "pass"}})
    assert v["passed"] and not v["warning"]
    assert gh.verdict_message(v).startswith("BUILD_PASSED: 1 wave gate(s) passed")
    v = gh.build_verdict(["1"], {"w1_gate": "FAILED"}, {})
    assert not v["passed"] and not v["warning"]


# --- branch sync in the verdict -----------------------------------------------------------

def test_verdict_fails_on_failed_sync_even_though_the_gate_was_excluded():
    # Wave 1's sync failed: synced=false Excludes w1_sessions ... w1_gate, and every later wave.
    states = {"w1_sync": "SUCCESS", "w1_gate": "EXCLUDED", "w2_sync": "EXCLUDED", "w2_gate": "EXCLUDED"}
    syncs = {"1": {"ok": False, "error": "pull conflicts with uncommitted files in the Git folder: a.py"}}
    v = gh.build_verdict(["1", "2"], states, {}, syncs)
    assert not v["passed"] and v["failed"] == ["1"]
    assert [e["result"] for e in v["waves"]] == ["fail", "excluded"]
    assert v["waves"][0]["sync_failed"] and v["waves"][0]["sync_task_state"] == "SUCCESS"
    msg = gh.verdict_message(v)
    assert "  - branch sync failed: pull conflicts with uncommitted files in the Git folder: a.py" in msg
    assert "repair from w1_sync" in msg and "wave_1_sync.json" in msg


def test_verdict_fails_on_crashed_or_silent_sync():
    v = gh.build_verdict(["1"], {"w1_sync": "FAILED", "w1_gate": "UPSTREAM_FAILED"}, {})
    assert v["failed"] == ["1"] and "w1_sync ended FAILED" in v["waves"][0]["problems"][0]
    v = gh.build_verdict(["1"], {"w1_sync": "TIMEDOUT", "w1_gate": "SUCCESS"}, {"1": {"status": "pass"}})
    assert not v["passed"]  # the sync state wins over a gate result
    # Sync task succeeded but wrote nothing, and the wave did not run.
    v = gh.build_verdict(["1"], {"w1_sync": "SUCCESS", "w1_gate": "EXCLUDED"}, {}, {})
    assert not v["passed"] and "wrote no wave_1_sync.json" in v["waves"][0]["problems"][0]


def test_verdict_with_passing_sync_uses_the_gate():
    states = {"w1_sync": "SUCCESS", "w1_gate": "SUCCESS", "w2_sync": "SUCCESS", "w2_gate": "SUCCESS"}
    syncs = {"1": {"ok": True}, "2": {"ok": True}}
    v = gh.build_verdict(["1", "2"], states, {"1": {"status": "pass"}, "2": {"status": "pass"}}, syncs)
    assert v["passed"] and v["checked"] == 2
    assert gh.verdict_message(v) == "BUILD_PASSED: 2 wave gate(s) passed"
    # A gate failure after a good sync suggests the sync as one repair start.
    v = gh.build_verdict(["1"], {"w1_sync": "SUCCESS", "w1_gate": "SUCCESS"},
                         {"1": {"status": "fail", "problems": ["p"]}}, {"1": {"ok": True}})
    msg = gh.verdict_message(v)
    assert "repair from w1_integrate" in msg and "w1_sync if a fix was pushed to the branch" in msg
    # Missing sync file is fine when the gate ran: the gate decides.
    v = gh.build_verdict(["1"], {"w1_sync": "SUCCESS", "w1_gate": "SUCCESS"}, {"1": {"status": "pass"}}, {})
    assert v["passed"]


def test_verdict_ignores_skipped_or_absent_sync():
    # Disabled / Excluded sync, or a run without sync tasks (workspace mode, sync_branch false).
    for sync_state in ("DISABLED", "EXCLUDED", None):
        states = {"w1_gate": "SUCCESS"}
        if sync_state:
            states["w1_sync"] = sync_state
        v = gh.build_verdict(["1"], states, {"1": {"status": "pass"}}, {"1": {"ok": False, "error": "stale"}})
        assert v["passed"], sync_state
    # Jobs API unavailable: a failed sync file still fails the wave.
    v = gh.build_verdict(["1"], None, {}, {"1": {"ok": False, "error": "boom"}})
    assert not v["passed"] and v["waves"][0]["problems"] == ["branch sync failed: boom"]


# --- required checks -----------------------------------------------------------------------

def test_required_checks():
    gate = {"checks": [{"name": "tsc", "result": "skipped", "detail": "no node"},
                       {"name": "vitest", "result": "pass"},
                       {"name": "lint", "result": "skipped"}]}
    probs = gh.required_check_problems({"required_checks": ["tsc", "vitest", "bundle validate"]}, gate)
    assert probs == ["required check 'tsc' result='skipped': no node",
                     "required check 'bundle validate' not reported in the gate file's checks"]
    # Not required + skipped passes; no required_checks or no gate file adds nothing.
    assert gh.required_check_problems({"required_checks": ["vitest"]}, gate) == []
    assert gh.required_check_problems({}, gate) == []
    assert gh.required_check_problems({"required_checks": ["tsc"]}, None) == []
    assert gh.required_check_problems({"required_checks": ["tsc"]}, {"checks": [{"name": "tsc", "result": "fail"}]}) \
        == ["required check 'tsc' result='fail'"]


# --- Genie space content matching ------------------------------------------------------------

# Anonymised shape of a real Genie space compared on 2026-10-26.
SOURCE = {
    "version": 2,
    "config": {"sample_questions": [{"id": "b", "question": ["How many reviews?"]},
                                    {"id": "a", "question": ["Which campaigns are open?"]}]},
    "data_sources": {
        "tables": [{"identifier": "c.s.reviews", "column_configs": [{"column_name": "z"}, {"column_name": "a"}]}],
        "metric_views": [{"identifier": "c.s.coverage_metrics"}],
    },
    "instructions": {
        "text_instructions": [{"id": "t1", "content": ["Line one.\nLine two."]}],
        "example_question_sqls": [{"id": "e1", "question": ["Reviews per day"],
                                   "sql": ["SELECT date, count(*)\nFROM c.s.reviews\nGROUP BY date"]}],
    },
}


def _deployed():
    """What the server returns for SOURCE: text split into lines, metric views in tables, other order."""
    return {
        "version": 2,
        "config": {"sample_questions": [{"id": "a", "question": ["Which campaigns are open?"]},
                                        {"id": "b", "question": ["How many reviews?"]}]},
        "data_sources": {"tables": [
            {"identifier": "c.s.coverage_metrics"},
            {"identifier": "c.s.reviews", "column_configs": [{"column_name": "a"}, {"column_name": "z"}]},
        ]},
        "instructions": {
            "text_instructions": [{"id": "t1", "content": ["Line one.\n", "Line two."]}],
            "example_question_sqls": [{"id": "e1", "question": ["Reviews per day"],
                                       "sql": ["SELECT date, count(*)\n", "FROM c.s.reviews\n", "GROUP BY date"]}],
        },
    }


def test_normalised_deployed_space_equals_source():
    assert gh.normalise_genie_space(SOURCE) == gh.normalise_genie_space(_deployed())
    assert gh.content_diff(gh.normalise_genie_space(SOURCE), gh.normalise_genie_space(_deployed())) == []
    assert "metric_views" in SOURCE["data_sources"]  # input not mutated


def test_content_diff_reports_paths():
    dep = _deployed()
    dep["instructions"]["example_question_sqls"][0]["sql"] = ["SELECT 1"]
    dep["config"]["extra"] = True
    del dep["version"]
    diffs = gh.content_diff(gh.normalise_genie_space(SOURCE), gh.normalise_genie_space(dep))
    assert diffs == ["config.extra: only in deployed",
                     "instructions.example_question_sqls[0].sql: differs",
                     "version: only in source"]
    assert len(gh.content_diff({"a": list(range(5))}, {"a": list(range(6))})) == 1
    assert len(gh.content_diff({str(i): i for i in range(30)}, {}, limit=10)) == 10


def test_genie_freshness_rules():
    fresh = gh.genie_freshness(True, None, "n/a", {})
    assert fresh == {"result": "pass", "basis": "fresh: updated after run start"}
    cur = gh.genie_freshness(False, SOURCE, "source_file", _deployed())
    assert cur["result"] == "pass" and cur["basis"] == "current: content matches source"
    dep = _deployed()
    dep["instructions"]["text_instructions"][0]["content"] = ["changed"]
    stale = gh.genie_freshness(False, SOURCE, "source_file", dep)
    assert stale["result"] == "fail" and stale["basis"].startswith("stale: content differs (1 paths)")
    assert stale["differences"] == ["instructions.text_instructions[0].content: differs"]
    ts = gh.genie_freshness(False, None, "no source_file or resource_key on the runtime target", dep)
    assert ts["result"] == "fail" and ts["basis"].startswith("timestamp only:")
    assert "last updated before" in ts["detail"]
    assert "has no update_time" in gh.genie_freshness(None, None, "x", dep)["detail"]


def _bundle(tmp_path):
    root = tmp_path / "agent"
    (root / "resources" / "genie").mkdir(parents=True)
    (root / "src").mkdir()
    (root / "databricks.yml").write_text("bundle:\n  name: agent\ninclude:\n  - resources/**/*.yml\n")
    (root / "resources" / "genie" / "trade.genie.yml").write_text(
        "resources:\n  genie_spaces:\n    sales_analysis:\n      title: Trade\n"
        "      warehouse_id: ${var.warehouse_id}\n      file_path: ../../src/trade.geniespace.json\n")
    (root / "resources" / "other.job.yml").write_text("resources:\n  jobs:\n    j: {name: j}\n")
    (root / "src" / "trade.geniespace.json").write_text(json.dumps(SOURCE))
    return root


def test_find_bundle_source_follows_includes(tmp_path):
    root = _bundle(tmp_path)
    path, basis = gh.find_bundle_source(str(root), "genie_spaces", "sales_analysis")
    assert path == str(root / "src" / "trade.geniespace.json")
    assert basis == "resources/genie/trade.genie.yml: resources.genie_spaces.sales_analysis.file_path"
    path, basis = gh.find_bundle_source(str(root), "genie_spaces", "nope")
    assert path is None and "not found" in basis
    assert gh.find_bundle_source(str(tmp_path), "genie_spaces", "x")[0] is None  # no databricks.yml


def test_locate_genie_source(tmp_path):
    root = _bundle(tmp_path)
    build_root = str(tmp_path)
    # resource_key lookup, bundle_root relative to build_root
    p, _ = gh.locate_genie_source({"resource_key": "sales_analysis", "bundle_root": "agent"}, build_root)
    assert p == str(root / "src" / "trade.geniespace.json")
    # source_file wins over resource_key
    p, basis = gh.locate_genie_source({"source_file": "src/trade.geniespace.json", "resource_key": "nope",
                                       "bundle_root": str(root)}, build_root)
    assert p == str(root / "src" / "trade.geniespace.json") and basis == "source_file"
    # missing file / nothing to look up
    p, basis = gh.locate_genie_source({"source_file": "src/missing.json", "bundle_root": str(root)}, build_root)
    assert p is None and "not found" in basis
    assert gh.locate_genie_source({"bundle_root": str(root)}, build_root) == (
        None, "no source_file or resource_key on the runtime target")
    with open(os.path.join(root, "src", "trade.geniespace.json")) as f:
        assert gh.genie_freshness(False, json.load(f), "k", _deployed())["result"] == "pass"
