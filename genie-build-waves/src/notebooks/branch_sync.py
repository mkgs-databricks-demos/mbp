"""Pure helpers for the sync_branch notebook (task w<wave>_sync), shared with the unit tests.

The integrator commits and pushes from the build_root Git folder and never pulls. A fix pushed
to the build branch from elsewhere (a person, an external monitor) is not in the folder until it
is pulled, and the integrator's next push would be rejected as non-fast-forward. w<wave>_sync
pulls the branch (Repos API update to the folder's current branch, as the job's run_as) before
the wave's sessions, so a repair from w<wave>_sync picks the fix up.

Repos API behaviour this relies on (checked 2026-11-08 on a CLI-enabled Git folder):
* update(branch=<current branch>) pulls; uncommitted files the incoming commits do not touch are
  kept (carryover from non-passing sessions stays).
* An uncommitted file the incoming commits change fails the call with
  "Conflict pulling from remote. Conflicting files: <a>, <b>." and leaves the folder unchanged.

Plain Python (no SDK / dbutils imports).
"""

import os
import re

PROTECTED_BRANCHES = {"main", "master"}

_CONFLICT_RE = re.compile(r"Conflicting files:\s*(.+)")


def sync_result_path(status_dir: str, wave) -> str:
    """w<wave>_sync's result for one wave in the run's status directory."""
    return os.path.join(status_dir, f"wave_{wave}_sync.json")


def git_folder_candidates(build_root: str) -> list[str]:
    """build_root and its parents, nearest first, for finding the Git folder root.

    build_root can be a bundle inside a monorepo Git folder. Stops above /Workspace/Users/<user>
    (or /Workspace/<top>/...): a Git folder is never that shallow.
    """
    path = os.path.normpath(build_root or "")
    out = []
    while path and path not in ("/", "."):
        parts = [p for p in path.split("/") if p]
        if len(parts) < 3 or (parts[0] == "Workspace" and len(parts) < 4 and parts[1] in ("Users", "Repos")):
            break
        out.append(path)
        path = os.path.dirname(path)
    return out


def branch_problem(folder_branch, branch) -> str | None:
    """Why the folder must not be synced to `branch`, or None.

    The sync never switches branches: a Git folder on another branch means someone checked out
    something else, and the integrator would refuse to commit anyway.
    """
    branch = (branch or "").strip()
    if not branch:
        return "the branch parameter is empty"
    if branch in PROTECTED_BRANCHES:
        return f"the build branch is {branch!r}; builds never run on {'/'.join(sorted(PROTECTED_BRANCHES))}"
    if not folder_branch:
        return "the Git folder reports no current branch (detached HEAD?)"
    if folder_branch != branch:
        return (f"the Git folder is on {folder_branch!r}, the build branch is {branch!r}; the sync does not "
                f"switch branches. Check out {branch!r} in the Git folder, then repair from this task")
    return None


def conflicting_files(message) -> list[str]:
    """Files listed in a Repos API pull conflict error (empty when it is another error)."""
    m = _CONFLICT_RE.search(str(message or ""))
    if not m:
        return []
    line = m.group(1).splitlines()[0].strip().rstrip(".")
    return [f.strip() for f in line.split(",") if f.strip()]


def first_line(message, limit: int = 500) -> str:
    """First non-empty line of an API error, without the trailing request id block."""
    for line in str(message or "").splitlines():
        if line.strip():
            return line.strip()[:limit]
    return ""


def parse_git_log(text) -> list[dict]:
    """`git log --format=%H%x09%an%x09%s` output -> [{sha, author, subject}]."""
    commits = []
    for line in str(text or "").splitlines():
        if not line.strip():
            continue
        sha, author, subject = (line.split("\t", 2) + ["", ""])[:3]
        commits.append({"sha": sha.strip(), "author": author.strip(), "subject": subject.strip()})
    return commits


def pull_failure(message) -> dict:
    """error / conflicts fields for a failed pull, with the next step."""
    files = conflicting_files(message)
    if files:
        return {"error": (f"pull conflicts with uncommitted files in the Git folder: {', '.join(files)}. "
                          f"These are usually carryover from a session that did not pass; a fix pushed to "
                          f"the branch should not touch the owned paths of sessions that will re-run"),
                "conflicts": files}
    return {"error": f"pull failed: {first_line(message)}", "conflicts": []}


def sync_result(wave, run_id, branch, ok: bool, before=None, after=None, error=None,
                conflicts=None, commits=None, files=None, git_folder=None) -> dict:
    """The wave_<wave>_sync.json record."""
    return {
        "wave": str(wave),
        "run_id": str(run_id),
        "branch": branch,
        "git_folder": git_folder,
        "ok": bool(ok),
        "before": before,
        "after": after,
        "pulled": bool(ok and before and after and before != after),
        "commits": list(commits or []),
        "files": list(files or []),
        "conflicts": list(conflicts or []),
        "error": error,
    }


def sync_message(result: dict) -> str:
    """One-line summary for the task output."""
    w = result.get("wave")
    if not result.get("ok"):
        return f"SYNC_FAILED: wave {w}: {result.get('error')}"
    if result.get("pulled"):
        n = len(result.get("commits") or [])
        detail = f"{n} commit(s), {len(result.get('files') or [])} file(s)" if n else "commit list unavailable"
        return (f"SYNC_PULLED: wave {w}: {result.get('branch')} {str(result.get('before'))[:12]} -> "
                f"{str(result.get('after'))[:12]} ({detail})")
    return f"SYNC_UP_TO_DATE: wave {w}: {result.get('branch')} at {str(result.get('after'))[:12]}"
