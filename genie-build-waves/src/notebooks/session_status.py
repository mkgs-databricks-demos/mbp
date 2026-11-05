"""Session status-file consistency rules, shared by wave_gate_check and the unit tests.

Inherited files. When a wave's gate fails, the integrator leaves the failing session's code
uncommitted. The usual recovery is a new build run from that wave, so the rerun session starts
with the earlier run's changes already in its owned_paths. It keeps them and lists them in its
top-level files_changed, but none of this run's attempts touched them.

The gate infers those files instead of trusting the runner to declare them: a file in
files_changed that no attempt lists is *inherited* when a status file of the same session from
another run (status_dir/<other_run_id>/<session_id>.json) lists it. For a converge session:

    files_changed == inherited files  UNION  every attempt's files_changed

An inherited file must still match the session's owned_paths and not its exclude_paths.
A file no attempt and no earlier run explains is still inconsistent.

Session outcome. A Genie Code session that stops at the step limit still ends its for_each
iteration SUCCESS. session_outcome combines the iteration's agent response (jobs/runs/get-output)
with the status file, so the gate can name the session, its conversation and the next step.

Continuation passes. incomplete_sessions lists the sessions of a wave with no final status
(FINAL_STATUSES): status file missing, unreadable (bad JSON or not an object) or any other
status. The build job re-runs them (runner continuation=k) before the integrator. The gate
uses the same session_outcome, so the find task and the gate cannot disagree. map_iterations
matches a for_each task's iterations to sessions and drops iterations kept from an earlier
attempt (repair), whose index no longer matches the current input list.

Plain Python (no Spark / dbutils imports), so the tests can import it directly.
"""

import json
import os
import re


def norm_path(p: str) -> str:
    """Normalise a build_root-relative path: forward slashes, no leading './'."""
    p = os.path.normpath(str(p).strip()).replace(os.sep, "/")
    return p[2:] if p.startswith("./") else p


def _glob_regex(pattern: str) -> re.Pattern:
    """Glob -> regex: '**/' any dirs (or none), '**' anything, '*' / '?' within one segment.

    A pattern ending in '/' matches everything below that directory.
    """
    pat = str(pattern).strip()
    if pat.startswith("./"):
        pat = pat[2:]
    if pat.endswith("/"):
        pat += "**"
    out, i = [], 0
    while i < len(pat):
        if pat.startswith("**/", i):
            out.append("(?:.*/)?")
            i += 3
        elif pat.startswith("**", i):
            out.append(".*")
            i += 2
        elif pat[i] == "*":
            out.append("[^/]*")
            i += 1
        elif pat[i] == "?":
            out.append("[^/]")
            i += 1
        else:
            out.append(re.escape(pat[i]))
            i += 1
    return re.compile("^" + "".join(out) + "$")


def matches_any(path: str, patterns) -> bool:
    p = norm_path(path)
    return any(_glob_regex(g).match(p) for g in (patterns or []))


def is_owned(path: str, session: dict) -> bool:
    """True when path matches the session's owned_paths and none of its exclude_paths."""
    return matches_any(path, session.get("owned_paths")) and not matches_any(path, session.get("exclude_paths"))


def attempt_files(status: dict) -> set:
    """Union of every attempt's files_changed."""
    return {norm_path(f) for a in (status.get("attempts") or []) for f in (a.get("files_changed") or [])}


def prior_run_files(status_root: str, run_id: str, session_id: str) -> dict:
    """Files the same session listed in other runs' status files: {path: run_id}.

    Reads status_root/<other_run_id>/<session_id>.json (top-level files_changed and every
    attempt's files_changed). The newest status file wins when several runs list a path.
    Unreadable or malformed files are skipped.
    """
    found = []
    if not status_root or not os.path.isdir(status_root):
        return {}
    for other in os.listdir(status_root):
        if other == str(run_id):
            continue
        p = os.path.join(status_root, other, f"{session_id}.json")
        if not os.path.isfile(p):
            continue
        try:
            with open(p) as f:
                st = json.load(f)
        except (OSError, ValueError):
            continue
        files = {norm_path(x) for x in (st.get("files_changed") or [])} | attempt_files(st)
        found.append((os.path.getmtime(p), other, files))
    result = {}
    for _, other, files in sorted(found, key=lambda t: t[0]):  # oldest first, newest overwrites
        for path in files:
            result[path] = other
    return result


def check_files_changed(session: dict, status: dict, prior_files: dict) -> dict:
    """Check a converge session's files_changed against its attempts and earlier runs.

    Returns {"inherited": [{"path", "run_id"}], "problems": [str]}. Sessions in other modes have
    no attempts, so nothing is inferred and nothing is reported (behaviour unchanged).
    """
    sid = session.get("session_id")
    if session.get("mode") != "converge":
        return {"inherited": [], "problems": []}
    top = {norm_path(f) for f in (status.get("files_changed") or [])}
    att = attempt_files(status)
    problems, inherited, unexplained = [], [], []

    missing = sorted(att - top)
    if missing:
        problems.append(f"session {sid}: attempt files missing from files_changed: {missing}")

    for path in sorted(top - att):
        if path in prior_files:
            inherited.append({"path": path, "run_id": prior_files[path]})
        else:
            unexplained.append(path)
    if unexplained:
        problems.append(
            f"session {sid}: files_changed lists files no attempt changed and no earlier run of "
            f"this session lists: {unexplained}"
        )

    not_owned = [i["path"] for i in inherited if not is_owned(i["path"], session)]
    if not_owned:
        problems.append(f"session {sid}: inherited files outside owned_paths or in exclude_paths: {not_owned}")

    return {"inherited": inherited, "problems": problems}


# --- Session outcome (step limit / unfinished sessions) ------------------------------

# Genie Code's reply when a turn runs out of steps (genie_task_output.agent_output.response).
STEP_LIMIT_TEXT = "reached the maximum number of steps"


def is_step_limit(response) -> bool:
    return STEP_LIMIT_TEXT in str(response or "").lower()


FINAL_STATUSES = frozenset({"pass", "fail", "blocked", "error"})


def session_outcome(response, status, unreadable: bool = False) -> dict:
    """{"outcome": complete | step_limit | in_progress | unreadable | missing, "warning": str | None}.

    response: the iteration's agent response text (None when unknown).
    status: the parsed status file, or None when it does not exist or cannot be read.
    unreadable: True when the file exists but is not valid JSON (read_status_file).
    Only FINAL_STATUSES are complete; any other value (in_progress, null, a typo) is not.
    The final status write is the session's last step, so a step limit after it gets a
    warning but changes nothing.
    """
    hit = is_step_limit(response)
    if unreadable or (status is not None and not isinstance(status, dict)):
        return {"outcome": "unreadable", "warning": None}
    if status is not None and status.get("status") in FINAL_STATUSES:
        warn = "hit the step limit after writing its final status" if hit else None
        return {"outcome": "complete", "warning": warn}
    if hit:
        return {"outcome": "step_limit", "warning": None}
    return {"outcome": "in_progress" if status is not None else "missing", "warning": None}


def read_status_file(path):
    """(status, problem): the parsed status dict, or None with 'missing' / 'unreadable'."""
    if not os.path.isfile(path):
        return None, "missing"
    try:
        with open(path) as f:
            st = json.load(f)
    except (OSError, ValueError):
        return None, "unreadable"
    return (st, None) if isinstance(st, dict) else (None, "unreadable")


def incomplete_sessions(wave_cfg: dict, status_dir: str) -> list[dict]:
    """Sessions with no final status in status_dir, in manifest order.

    Returns [{"session_id", "title", "reason"}], reason = missing | unreadable | in_progress
    (in_progress = any status outside FINAL_STATUSES). This is session_outcome without an
    agent response, so it matches the gate. pass / fail / blocked / error are not re-run.
    """
    out = []
    for s in wave_cfg.get("sessions") or []:
        sid = s.get("session_id")
        st, problem = read_status_file(os.path.join(status_dir, f"{sid}.json"))
        oc = session_outcome(None, st, unreadable=problem == "unreadable")["outcome"]
        if oc != "complete":
            out.append({"session_id": sid, "title": s.get("title", sid), "reason": oc})
    return out


def session_problem(session_id, outcome: str, conversation_id, wave, progress=None, continued: int = 0) -> str:
    """Gate problem text for a session that is not complete: who, which conversation, what next.

    continued: the continuation pass that ran the session last (0 = only the first run).
    """
    conv = f"conversation {conversation_id}" if conversation_id else "conversation unknown"
    what = {
        "step_limit": "hit the Genie Code step limit",
        "in_progress": "stopped before finishing (status file has no final status)",
        "missing": "wrote no status file",
        "unreadable": "wrote a status file that is not a readable JSON object",
    }.get(outcome, outcome)
    if continued:
        what += f" after continuation pass {continued}"
    nxt = ""
    if isinstance(progress, dict) and progress.get("next"):
        nxt = f"; next step: {progress['next']}"
    return (f"session {session_id} {what} ({conv}{nxt}): resume that conversation, "
            f"then repair from w{wave}_integrate")


_ITER_RE = re.compile(r"iteration #(\d+)")


def iteration_index(run_name):
    """for_each iteration index from its run name ('w4-1_session iteration #0' -> 0), else None."""
    m = _ITER_RE.search(str(run_name or ""))
    return int(m.group(1)) if m else None


def latest_by_index(entries) -> dict:
    """{index: entry} keeping the highest attempt_number per iteration index (retries).

    entries: dicts with index, attempt_number and anything else.
    """
    best = {}
    for e in entries:
        i = e.get("index")
        if i is None:
            continue
        if i not in best or int(e.get("attempt_number") or 0) >= int(best[i].get("attempt_number") or 0):
            best[i] = e
    return best


SKIPPED_RESULTS = frozenset({"EXCLUDED", "SKIPPED"})


def latest_task_attempt(run_tasks, key):
    """The latest attempt of task key in a runs/get task list that actually ran (None if none did).

    A repair can leave a later Excluded attempt; reading it would drop the earlier iterations.
    """
    ran = [t for t in run_tasks or [] if t.get("task_key") == key
           and ((t.get("state") or {}).get("result_state") not in SKIPPED_RESULTS)]
    if not ran:
        return None
    return max(ran, key=lambda t: (int(t.get("attempt_number") or 0), int(t.get("start_time") or 0)))


def parse_inputs(raw):
    """A for_each task's inputs as a list, or None (e.g. an unresolved {{tasks...}} reference)."""
    if isinstance(raw, list):
        return raw
    if not isinstance(raw, str):
        return None
    try:
        v = json.loads(raw)
    except ValueError:
        return None
    return v if isinstance(v, list) else None


def map_iterations(inputs, entries, not_before=None):
    """({session_id: entry}, [warning]) for a for_each task's iterations.

    inputs: the input list the iterations ran on (iteration #i ran inputs[i]).
    entries: dicts with index, attempt_number, start_time (ms) and anything else.
    not_before: ms timestamp the input list was computed at (the find task's start). An iteration
    that started earlier was kept from an earlier attempt of the for_each (a repair keeps
    SUCCESS iterations), so its index may point at a different session: it is dropped.
    """
    warnings = []
    inputs = inputs if isinstance(inputs, list) else []
    fresh, stale = [], 0
    for e in entries or []:
        st = e.get("start_time")
        if not_before and st and int(st) < int(not_before):
            stale += 1
            continue
        fresh.append(e)
    if stale:
        warnings.append(f"{stale} iteration(s) started before their input list was computed "
                        f"(kept from an earlier attempt); not matched to a session")
    if fresh and not inputs:
        warnings.append(f"{len(fresh)} iteration(s) ran but their input list could not be read; "
                        f"not matched to a session")
        return {}, warnings
    out = {}
    for i, e in sorted(latest_by_index(fresh).items()):
        item = inputs[i] if 0 <= i < len(inputs) else None
        if isinstance(item, dict) and item.get("session_id") is not None:
            out[str(item["session_id"])] = e
        else:
            warnings.append(f"iteration #{i} has no matching input; not matched to a session")
    return out, warnings
