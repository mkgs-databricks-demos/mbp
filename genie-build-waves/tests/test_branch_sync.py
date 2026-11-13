"""Branch sync helpers (sync_branch notebook, task w<wave>_sync)."""

import pytest

import branch_sync as bs

# Error text returned by the Repos API (update to the current branch) when an uncommitted file
# in the Git folder is changed by an incoming commit (seen 2026-11-08).
CONFLICT = ("Conflict pulling from remote. Conflicting files: probe/b.txt.\n"
            "Please commit or discard the changes and try again.")


def test_sync_result_path():
    assert bs.sync_result_path("/s/123", "4-1") == "/s/123/wave_4-1_sync.json"


def test_git_folder_candidates_walk_up_to_user_folder():
    root = "/Workspace/Users/me@example.com/repo/bundles/app"
    assert bs.git_folder_candidates(root) == [
        "/Workspace/Users/me@example.com/repo/bundles/app",
        "/Workspace/Users/me@example.com/repo/bundles",
        "/Workspace/Users/me@example.com/repo"]
    assert bs.git_folder_candidates("/Workspace/Users/me@example.com/repo/") == [
        "/Workspace/Users/me@example.com/repo"]
    assert bs.git_folder_candidates("/Users/me@example.com/repo") == ["/Users/me@example.com/repo"]
    assert bs.git_folder_candidates("/Workspace/Shared/repo") == ["/Workspace/Shared/repo"]
    assert bs.git_folder_candidates("/Workspace/Users/me@example.com") == []
    assert bs.git_folder_candidates("") == []


@pytest.mark.parametrize("folder,branch,fragment", [
    ("b", "b", None),
    ("b", "", "branch parameter is empty"),
    ("main", "main", "never run on main/master"),
    ("master", "master", "never run on main/master"),
    (None, "b", "no current branch"),
    ("other", "b", "Git folder is on 'other', the build branch is 'b'"),
])
def test_branch_problem(folder, branch, fragment):
    p = bs.branch_problem(folder, branch)
    assert (p is None) if fragment is None else (fragment in p), p


def test_conflicting_files():
    assert bs.conflicting_files(CONFLICT) == ["probe/b.txt"]
    assert bs.conflicting_files("Conflict pulling from remote. Conflicting files: a.py, b/c.yml.") == ["a.py", "b/c.yml"]
    assert bs.conflicting_files("Permission denied") == []
    assert bs.conflicting_files(None) == []


def test_pull_failure():
    f = bs.pull_failure(Exception(CONFLICT))
    assert f["conflicts"] == ["probe/b.txt"]
    assert f["error"].startswith("pull conflicts with uncommitted files in the Git folder: probe/b.txt.")
    f = bs.pull_failure("Invalid Git credentials\nrequest id 123")
    assert f == {"error": "pull failed: Invalid Git credentials", "conflicts": []}


def test_parse_git_log():
    text = "abc123\tAda\tFix gate check\n\ndef456\tBob\tAdd: tabs\tin subject\n"
    assert bs.parse_git_log(text) == [
        {"sha": "abc123", "author": "Ada", "subject": "Fix gate check"},
        {"sha": "def456", "author": "Bob", "subject": "Add: tabs\tin subject"}]
    assert bs.parse_git_log(None) == []
    assert bs.parse_git_log("lonely") == [{"sha": "lonely", "author": "", "subject": ""}]


def test_sync_result_and_messages():
    up = bs.sync_result("1", 9, "b", ok=True, before="a" * 40, after="a" * 40)
    assert up["ok"] and not up["pulled"] and up["run_id"] == "9"
    assert bs.sync_message(up) == f"SYNC_UP_TO_DATE: wave 1: b at {'a' * 12}"

    pulled = bs.sync_result("1", 9, "b", ok=True, before="a" * 40, after="b" * 40,
                            commits=[{"sha": "b" * 40}], files=["x", "y"])
    assert pulled["pulled"]
    assert bs.sync_message(pulled) == f"SYNC_PULLED: wave 1: b {'a' * 12} -> {'b' * 12} (1 commit(s), 2 file(s))"
    no_log = bs.sync_result("1", 9, "b", ok=True, before="a", after="b")
    assert bs.sync_message(no_log).endswith("(commit list unavailable)")

    failed = bs.sync_result("1", 9, "b", ok=False, before="a", after="b", error="boom", conflicts=["x"])
    assert not failed["pulled"]  # a failed sync never reports a pull
    assert bs.sync_message(failed) == "SYNC_FAILED: wave 1: boom"
