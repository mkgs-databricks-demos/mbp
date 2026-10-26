"""Converge files_changed consistency, including files inherited from an earlier build run."""

import json
import os
import time

import session_status as ss

SESSION = {
    "session_id": "35a",
    "mode": "converge",
    "owned_paths": ["app/**"],
    "exclude_paths": ["app/server/mcp/**"],
}


def _status(files_changed, attempts):
    return {
        "session_id": "35a",
        "status": "pass",
        "files_changed": files_changed,
        "attempts": [{"n": i + 1, "result": r, "files_changed": f} for i, (r, f) in enumerate(attempts)],
    }


def _write(root, run_id, session_id, payload, mtime=None):
    d = os.path.join(root, run_id)
    os.makedirs(d, exist_ok=True)
    p = os.path.join(d, f"{session_id}.json")
    with open(p, "w") as f:
        json.dump(payload, f)
    if mtime is not None:
        os.utime(p, (mtime, mtime))
    return p


def test_glob_matching():
    assert ss.matches_any("app/server/x.ts", ["app/**"])
    assert ss.matches_any("./app/a.ts", ["app/*.ts"])
    assert not ss.matches_any("app/server/x.ts", ["app/*.ts"])
    assert ss.matches_any("app/x/y/z.json", ["app/**/*.json"])
    assert ss.matches_any("app/z.json", ["app/**/*.json"])
    assert ss.matches_any("app/server/x.ts", ["app/"])
    assert not ss.is_owned("app/server/mcp/tool.ts", SESSION)
    assert ss.is_owned("app/server/server.ts", SESSION)


def test_inherits_files_from_failed_prior_run(tmp_path):
    root = str(tmp_path)
    # Earlier run: session blocked after editing databricks.yml and a dashboard.
    _write(root, "111", "35a", {"status": "blocked", "files_changed": ["app/databricks.yml", "app/dash.lvdash.json"],
                                "attempts": [{"n": 1, "result": "deploy_failed", "files_changed": ["app/databricks.yml"]}]})
    # This run: one stable attempt touching only server.ts; it keeps the inherited files.
    st = _status(["app/server.ts", "app/databricks.yml", "app/dash.lvdash.json"], [("stable", ["app/server.ts"])])
    _write(root, "222", "35a", st)

    prior = ss.prior_run_files(root, "222", "35a")
    assert prior == {"app/databricks.yml": "111", "app/dash.lvdash.json": "111"}
    res = ss.check_files_changed(SESSION, st, prior)
    assert res["problems"] == []
    assert res["inherited"] == [{"path": "app/dash.lvdash.json", "run_id": "111"},
                                {"path": "app/databricks.yml", "run_id": "111"}]


def test_inherited_file_outside_owned_paths_fails(tmp_path):
    root = str(tmp_path)
    _write(root, "111", "35a", {"status": "blocked", "files_changed": ["shared/contracts/api.ts", "app/server/mcp/tool.ts"]})
    st = _status(["app/server.ts", "shared/contracts/api.ts", "app/server/mcp/tool.ts"], [("stable", ["app/server.ts"])])
    res = ss.check_files_changed(SESSION, st, ss.prior_run_files(root, "222", "35a"))
    assert len(res["problems"]) == 1
    assert "outside owned_paths or in exclude_paths" in res["problems"][0]
    assert "shared/contracts/api.ts" in res["problems"][0]
    assert "app/server/mcp/tool.ts" in res["problems"][0]  # exclude_paths overlap


def test_no_inherited_files_unchanged(tmp_path):
    root = str(tmp_path)
    st = _status(["app/a.ts", "app/b.ts"], [("build_failed", ["app/a.ts"]), ("stable", ["app/b.ts"])])
    prior = ss.prior_run_files(root, "222", "35a")
    assert prior == {}
    assert ss.check_files_changed(SESSION, st, prior) == {"inherited": [], "problems": []}


def test_unexplained_file_still_fails(tmp_path):
    """Edited before attempt 1 and not recorded in any attempt: no earlier run explains it."""
    st = _status(["app/a.ts", "app/app.yaml"], [("stable", ["app/a.ts"])])
    res = ss.check_files_changed(SESSION, st, ss.prior_run_files(str(tmp_path), "222", "35a"))
    assert res["inherited"] == []
    assert len(res["problems"]) == 1 and "app/app.yaml" in res["problems"][0]


def test_attempt_file_missing_from_top_level_fails():
    st = _status(["app/a.ts"], [("stable", ["app/a.ts", "app/b.ts"])])
    res = ss.check_files_changed(SESSION, st, {})
    assert len(res["problems"]) == 1 and "missing from files_changed" in res["problems"][0]


def test_inherited_and_edited_again_is_not_inherited(tmp_path):
    root = str(tmp_path)
    _write(root, "111", "35a", {"files_changed": ["app/a.ts"]})
    st = _status(["app/a.ts"], [("stable", ["app/a.ts"])])
    res = ss.check_files_changed(SESSION, st, ss.prior_run_files(root, "222", "35a"))
    assert res == {"inherited": [], "problems": []}


def test_newest_prior_run_wins_and_other_sessions_ignored(tmp_path):
    root = str(tmp_path)
    now = time.time()
    _write(root, "100", "35a", {"files_changed": ["app/x.ts"]}, mtime=now - 7200)
    _write(root, "200", "35a", {"files_changed": ["app/x.ts"]}, mtime=now - 60)
    _write(root, "200", "36", {"files_changed": ["app/y.ts"]})  # different session
    _write(root, "300", "35a", {"files_changed": ["app/z.ts"]})  # this run: ignored
    (tmp_path / "400").mkdir()
    (tmp_path / "400" / "35a.json").write_text("{not json")  # malformed: skipped
    assert ss.prior_run_files(root, "300", "35a") == {"app/x.ts": "200"}


def test_edit_mode_session_not_checked():
    edit = dict(SESSION, mode="edit")
    st = {"status": "pass", "files_changed": ["app/a.ts"]}
    assert ss.check_files_changed(edit, st, {}) == {"inherited": [], "problems": []}


# --- session outcome -------------------------------------------------------------------

# Verbatim genie_task_output.agent_output.response of iteration 861320051785964 (run 110489694161084).
STEP_LIMIT = "I've reached the maximum number of steps for this turn. Would you like me to continue?"
NORMAL = "session_id 33, mode edit, status pass, 4 files changed, no failed checks."


def test_session_outcome_cases():
    assert ss.session_outcome(STEP_LIMIT, {"status": "in_progress"}) == {"outcome": "step_limit", "warning": None}
    oc = ss.session_outcome(STEP_LIMIT, {"status": "pass"})
    assert oc["outcome"] == "complete" and "step limit" in oc["warning"]
    assert ss.session_outcome(NORMAL, {"status": "in_progress"}) == {"outcome": "in_progress", "warning": None}
    assert ss.session_outcome(NORMAL, None) == {"outcome": "missing", "warning": None}
    assert ss.session_outcome(NORMAL, {"status": "pass"}) == {"outcome": "complete", "warning": None}
    # A final non-pass status is complete here; the status check reports it.
    assert ss.session_outcome(NORMAL, {"status": "blocked"})["outcome"] == "complete"
    # Step limit and no status file at all: the step limit is the more useful diagnosis.
    assert ss.session_outcome(STEP_LIMIT, None)["outcome"] == "step_limit"
    # Jobs API unavailable (no response): decided by the status file alone.
    assert ss.session_outcome(None, {"status": "in_progress"})["outcome"] == "in_progress"


def test_session_problem_names_session_conversation_and_repair():
    msg = ss.session_problem("33", "step_limit", "3614498846438467", "4-1")
    assert msg == ("session 33 hit the Genie Code step limit (conversation 3614498846438467): "
                   "resume that conversation, then repair from w4-1_integrate")
    msg = ss.session_problem("35", "in_progress", None, "4-3", {"next": "attempt 2: fix TS2345"})
    assert "conversation unknown; next step: attempt 2: fix TS2345" in msg
    assert msg.endswith("repair from w4-3_integrate")
    assert "wrote no status file" in ss.session_problem("36", "missing", "1", "4-4")


def test_iteration_index_and_latest_attempt():
    assert ss.iteration_index("w4-1_session iteration #0") == 0
    assert ss.iteration_index("w4-1_session iteration #12") == 12
    assert ss.iteration_index(None) is None
    best = ss.latest_by_index([
        {"index": 0, "attempt_number": 0, "run_id": 1},
        {"index": 0, "attempt_number": 2, "run_id": 3},
        {"index": 0, "attempt_number": 1, "run_id": 2},
        {"index": 1, "attempt_number": 0, "run_id": 4},
        {"index": None, "attempt_number": 0, "run_id": 5},
    ])
    assert {i: e["run_id"] for i, e in best.items()} == {0: 3, 1: 4}
