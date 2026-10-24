"""Jobs API 2.2 helpers shared by the setup notebook (and its tests).

Jobs API 2.1 rejects jobs with more than 100 tasks. API 2.2 accepts them, but
`jobs/get` and `jobs/runs/get` return at most 100 elements per array field and a
root-level `next_page_token`. A read that stops at the first page silently loses
tasks (and job clusters, environments, parameters), and a `jobs/reset` built from
such a read would drop them from the job. Every read here follows the token.

`api` is anything with `do(method, path, query=None, body=None) -> dict`, e.g.
`WorkspaceClient().api_client`. No other dependencies, so tests can pass a fake.
"""

JOBS_API = "/api/2.2/jobs"

# Array fields that 2.2 paginates (docs: "Updating from Jobs API 2.1 to 2.2").
# Fields with fewer than 100 elements are empty or absent on later pages.
PAGED_JOB_SETTINGS_FIELDS = ("tasks", "job_clusters", "environments", "parameters")
PAGED_RUN_FIELDS = ("tasks", "job_clusters", "job_parameters", "iterations")

MAX_PAGES = 1000  # safety stop: 100k tasks is far beyond any real job

# Fields jobs/get returns in settings that jobs/reset does not accept.
RESET_DROP_KEYS = ("format", "deployment", "edit_mode", "source")


def _paged_get(api, path: str, query: dict, merge_into, fields) -> dict:
    """GET `path` and follow next_page_token, appending each page's `fields` lists.

    `merge_into(page)` returns the dict holding the paged lists (e.g. page["settings"]).
    """
    first = api.do("GET", path, query=dict(query))
    target = merge_into(first)
    token = first.get("next_page_token")
    seen = set()
    pages = 1
    while token:
        if token in seen:
            raise RuntimeError(f"{path}: next_page_token repeated after {pages} pages; refusing to loop")
        if pages >= MAX_PAGES:
            raise RuntimeError(f"{path}: more than {MAX_PAGES} pages; refusing to continue")
        seen.add(token)
        page = api.do("GET", path, query={**query, "page_token": token})
        src = merge_into(page)
        for f in fields:
            more = src.get(f) or []
            if more:
                target.setdefault(f, []).extend(more)
        token = page.get("next_page_token")
        pages += 1
    first.pop("next_page_token", None)
    return first


def get_job(api, job_id) -> dict:
    """jobs/get with every page of settings.tasks / job_clusters / environments / parameters."""
    return _paged_get(
        api, f"{JOBS_API}/get", {"job_id": str(job_id)},
        lambda page: page.setdefault("settings", {}), PAGED_JOB_SETTINGS_FIELDS,
    )


def get_job_tasks(api, job_id) -> list[dict]:
    return get_job(api, job_id).get("settings", {}).get("tasks", []) or []


def get_run(api, run_id, **query) -> dict:
    """jobs/runs/get with every page of tasks / job_clusters / job_parameters / iterations."""
    return _paged_get(
        api, f"{JOBS_API}/runs/get", {"run_id": str(run_id), **{k: str(v).lower() if isinstance(v, bool) else v for k, v in query.items()}},
        lambda page: page, PAGED_RUN_FIELDS,
    )


def get_run_output(api, run_id) -> dict:
    return api.do("GET", f"{JOBS_API}/runs/get-output", query={"run_id": str(run_id)})


def run_now(api, job_id, **body) -> dict:
    return api.do("POST", f"{JOBS_API}/run-now", body={"job_id": int(job_id), **body})


def build_reset_settings(job: dict, new_tasks: list[dict], parameters: list[dict] | None = None) -> dict:
    """new_settings for jobs/reset: the job's full settings with tasks (and optionally parameters) replaced."""
    settings = dict(job.get("settings", {}))
    settings["tasks"] = list(new_tasks)
    if parameters is not None:
        settings["parameters"] = list(parameters)
    for k in RESET_DROP_KEYS:
        settings.pop(k, None)
    return settings


def reset_job_tasks(api, job_id, new_tasks: list[dict], parameters: list[dict] | None = None) -> dict:
    """Replace a job's tasks via jobs/reset (2.2, so > 100 tasks work), preserving all other settings.

    The current settings come from a fully paged jobs/get, so job clusters, environments
    and parameters beyond the first 100 are kept.
    """
    settings = build_reset_settings(get_job(api, job_id), new_tasks, parameters)
    api.do("POST", f"{JOBS_API}/reset", body={"job_id": int(job_id), "new_settings": settings})
    return settings


def iter_genie_configuration_ids(tasks: list[dict]):
    """configuration_id of every genie_task, including for_each inner tasks."""
    for task in tasks or []:
        cid = (task.get("genie_task") or {}).get("configuration_id")
        if cid:
            yield cid
        inner = ((task.get("for_each_task") or {}).get("task") or {})
        cid = (inner.get("genie_task") or {}).get("configuration_id")
        if cid:
            yield cid
