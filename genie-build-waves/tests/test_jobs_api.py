"""Jobs API 2.2 paging and reset, against a fake Jobs service that behaves like 2.2.

The fake returns at most 100 elements per paged array and a root next_page_token,
and (like the real service) rejects 2.1 calls for jobs with more than 100 tasks.
"""

import copy

import pytest

import jobs_api

PAGE = 100


class FakeJobs:
    def __init__(self, job_id=42, n_tasks=128, n_clusters=0, n_params=3, settings_extra=None):
        self.job_id = job_id
        self.settings = {
            "name": "build",
            "format": "MULTI_TASK",
            "edit_mode": "EDITABLE",
            "deployment": {"kind": "BUNDLE"},
            "tags": {"purpose": "build-waves"},
            "tasks": [{"task_key": f"t{i:03d}"} for i in range(n_tasks)],
            "job_clusters": [{"job_cluster_key": f"c{i}"} for i in range(n_clusters)],
            "parameters": [{"name": f"p{i}", "default": ""} for i in range(n_params)],
            **(settings_extra or {}),
        }
        self.run = {
            "run_id": 7,
            "state": {"life_cycle_state": "TERMINATED", "result_state": "SUCCESS"},
            "tasks": [{"task_key": f"r{i:03d}", "run_id": 1000 + i} for i in range(n_tasks)],
        }
        self.calls = []

    @staticmethod
    def _page(obj: dict, fields, page: int) -> dict:
        out = copy.deepcopy(obj)
        more = False
        for f in fields:
            items = obj.get(f)
            if items is None:
                continue
            out[f] = items[page * PAGE:(page + 1) * PAGE]
            more = more or len(items) > (page + 1) * PAGE
        return out, more

    def do(self, method, path, query=None, body=None):
        self.calls.append((method, path, copy.deepcopy(query), copy.deepcopy(body)))
        if path.startswith("/api/2.1/") and len(self.settings["tasks"]) > PAGE:
            raise RuntimeError("InvalidParameterValue: Resources with more than 100 tasks can only be "
                               "handled by API 2.2 and above.")
        assert path.startswith("/api/2.2/jobs/"), path
        page = int((query or {}).get("page_token", "0").removeprefix("tok") or 0)
        if path.endswith("/jobs/get"):
            assert str(query["job_id"]) == str(self.job_id)
            settings, more = self._page(self.settings, jobs_api.PAGED_JOB_SETTINGS_FIELDS, page)
            resp = {"job_id": self.job_id, "settings": settings}
        elif path.endswith("/jobs/runs/get"):
            resp, more = self._page(self.run, jobs_api.PAGED_RUN_FIELDS, page)
        elif path.endswith("/jobs/reset"):
            assert body["job_id"] == self.job_id
            self.settings = copy.deepcopy(body["new_settings"])
            return {}
        else:
            raise AssertionError(f"unexpected {method} {path}")
        if more:
            resp["next_page_token"] = f"tok{page + 1}"
        return resp


def test_2_1_rejects_big_job():
    """The failure the setup job hit: 2.1 refuses a job with 128 tasks."""
    fake = FakeJobs(n_tasks=128)
    with pytest.raises(RuntimeError, match="more than 100 tasks"):
        fake.do("GET", "/api/2.1/jobs/get", query={"job_id": "42"})


def test_get_job_follows_next_page_token():
    fake = FakeJobs(n_tasks=250, n_clusters=130, n_params=3)
    job = jobs_api.get_job(fake, 42)
    s = job["settings"]
    assert [t["task_key"] for t in s["tasks"]] == [f"t{i:03d}" for i in range(250)]
    assert len(s["job_clusters"]) == 130
    assert len(s["parameters"]) == 3  # not duplicated by later (empty) pages
    assert "next_page_token" not in job
    gets = [c for c in fake.calls if c[1].endswith("/jobs/get")]
    assert [c[2].get("page_token") for c in gets] == [None, "tok1", "tok2"]
    assert all(c[1].startswith("/api/2.2/") for c in fake.calls)


def test_get_job_single_page_makes_one_call():
    fake = FakeJobs(n_tasks=28)
    assert len(jobs_api.get_job_tasks(fake, 42)) == 28
    assert len(fake.calls) == 1


def test_get_run_follows_next_page_token():
    fake = FakeJobs(n_tasks=128)
    run = jobs_api.get_run(fake, 7)
    assert len(run["tasks"]) == 128
    assert run["tasks"][-1]["task_key"] == "r127"


def test_repeated_page_token_raises():
    class Loop:
        def do(self, method, path, query=None, body=None):
            return {"settings": {"tasks": [{"task_key": "a"}]}, "next_page_token": "same"}

    with pytest.raises(RuntimeError, match="repeated"):
        jobs_api.get_job(Loop(), 1)


def test_reset_big_job_keeps_every_task_and_other_settings():
    """Reset a job that already has > 100 tasks (and > 100 job clusters) with a > 100 task graph."""
    fake = FakeJobs(n_tasks=128, n_clusters=120, n_params=2)
    new_tasks = [{"task_key": f"w4-{i}_x{j}"} for i in range(30) for j in range(4)]  # 120 tasks
    params = [{"name": "branch", "default": "b"}]
    sent = jobs_api.reset_job_tasks(fake, 42, new_tasks, parameters=params)

    reset_calls = [c for c in fake.calls if c[1].endswith("/jobs/reset")]
    assert len(reset_calls) == 1 and reset_calls[0][1] == "/api/2.2/jobs/reset"
    body = reset_calls[0][3]
    assert body["job_id"] == 42
    assert len(body["new_settings"]["tasks"]) == 120
    # Settings that were only complete after paging survive the reset.
    assert len(body["new_settings"]["job_clusters"]) == 120
    assert body["new_settings"]["parameters"] == params
    assert body["new_settings"]["tags"] == {"purpose": "build-waves"}
    for k in jobs_api.RESET_DROP_KEYS:
        assert k not in body["new_settings"]
    assert sent == body["new_settings"]

    # Paged read-back returns exactly the new graph.
    assert [t["task_key"] for t in jobs_api.get_job_tasks(fake, 42)] == [t["task_key"] for t in new_tasks]


def test_reset_without_parameters_keeps_existing_parameters():
    fake = FakeJobs(n_tasks=5, n_params=2)
    jobs_api.reset_job_tasks(fake, 42, [{"task_key": "a"}])
    assert [p["name"] for p in fake.settings["parameters"]] == ["p0", "p1"]


def test_iter_genie_configuration_ids_includes_for_each_and_late_tasks():
    fake = FakeJobs(n_tasks=0)
    fake.settings["tasks"] = [{"task_key": f"n{i}", "notebook_task": {}} for i in range(110)] + [
        {"task_key": "late_integrate", "genie_task": {"configuration_id": "cfg/integrator"}},
        {"task_key": "late_sessions", "for_each_task": {"task": {"genie_task": {"configuration_id": "cfg/runner"}}}},
    ]
    ids = set(jobs_api.iter_genie_configuration_ids(jobs_api.get_job_tasks(fake, 42)))
    assert ids == {"cfg/integrator", "cfg/runner"}
