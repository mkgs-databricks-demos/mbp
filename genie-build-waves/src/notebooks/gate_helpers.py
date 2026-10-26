"""Pure helpers for wave_gate_check and build_verdict, shared with the unit tests.

* Gate result files and the run-level verdict. A failed wave gate does not raise: raising would
  mark the next wave UPSTREAM_FAILED, and its `run_if: ALL_DONE` integrator and gate would then
  run anyway (Jobs treats Upstream failed as failed, and ALL_DONE runs regardless). The gate
  writes `wave_<wave>_gate_result.json` and sets `gate_passed`, so later waves are Excluded
  (zero compute). The final `build_verdict` task reads every gate's task state and result file
  and raises, so the run ends FAILED.
* Wave `required_checks` against the integrator's gate file.
* Genie space content matching for the runtime freshness check: a no-op deploy leaves the
  space's `update_time` before the run start, but the space still matches its bundle source.

Plain Python (no Spark / dbutils / SDK imports). PyYAML is imported only when a bundle's
resource YAML must be read.
"""

import copy
import glob
import json
import os

# --- Gate result files ------------------------------------------------------------


def gate_result_path(status_dir: str, wave) -> str:
    """The gate notebook's own result for one wave (the integrator writes wave_<wave>_gate.json)."""
    return os.path.join(status_dir, f"wave_{wave}_gate_result.json")


def gate_failure_message(wave, problems, limit: int = 20) -> str:
    """Printed by the gate when it fails; the fixed GATE_FAILED tag tells a rejected wave apart
    from a gate notebook that crashed."""
    problems = list(problems or [])
    lines = [f"GATE_FAILED: wave {wave}: {len(problems)} problem(s)"]
    lines += [f"  - {p}" for p in problems[:limit]]
    if len(problems) > limit:
        lines.append(f"  ... and {len(problems) - limit} more (see wave_{wave}_gate_result.json)")
    return "\n".join(lines)


# --- Run-level verdict ------------------------------------------------------------

VERDICT_TASK_KEY = "build_verdict"


def latest_task_states(run_tasks) -> dict:
    """{task_key: result_state} from jobs/runs/get `tasks`, keeping the latest attempt of each task.

    A repaired run lists every attempt of a task (attempt_number 0, 1, ...).
    """
    best = {}
    for t in run_tasks or []:
        key = t.get("task_key")
        if not key:
            continue
        rank = (int(t.get("attempt_number") or 0), int(t.get("start_time") or 0))
        if key not in best or rank >= best[key][0]:
            best[key] = (rank, (t.get("state") or {}).get("result_state"))
    return {k: v[1] for k, v in best.items()}


def build_verdict(wave_ids, task_states, results) -> dict:
    """Run verdict from every runnable wave's gate.

    wave_ids: runnable wave ids in manifest order.
    task_states: {task_key: result_state} for this run (latest attempts), or None when the Jobs
        API could not be read; then only the result files decide.
    results: {wave_id: gate result dict (wave_<w>_gate_result.json) or None}.

    Per wave: gate task not in this run (`only` subset) -> not_in_run; EXCLUDED (an earlier wave
    failed) -> excluded; SUCCESS -> the result file decides (missing file = fail); any other
    state (FAILED, TIMEDOUT, UPSTREAM_FAILED, CANCELED, ...) -> fail.
    """
    waves, failed = [], []
    for wid in wave_ids:
        wid = str(wid)
        key = f"w{wid}_gate"
        res = results.get(wid)
        entry = {"wave": wid, "gate_task": key}
        if task_states is not None:
            state = task_states.get(key)
            entry["task_state"] = state
            if state is None:
                entry["result"] = "not_in_run"
            elif state == "EXCLUDED":
                entry["result"] = "excluded"
            elif state != "SUCCESS":
                entry.update(result="fail", problems=[f"gate task ended {state} (the gate notebook did not finish)"])
            elif res is None:
                entry.update(result="fail", problems=["gate task succeeded but wrote no result file"])
            else:
                entry.update(result="pass" if res.get("status") == "pass" else "fail",
                             problems=list(res.get("problems") or []))
        elif res is None:
            entry["result"] = "no_result"
        else:
            entry.update(result="pass" if res.get("status") == "pass" else "fail",
                         problems=list(res.get("problems") or []))
        if entry["result"] == "fail":
            failed.append(entry)
        waves.append(entry)
    checked = [e for e in waves if e["result"] in ("pass", "fail")]
    return {"passed": not failed, "waves": waves, "failed": [e["wave"] for e in failed],
            "checked": len(checked), "api_used": task_states is not None}


def verdict_message(verdict: dict, per_wave: int = 5) -> str:
    """BUILD_FAILED / BUILD_PASSED summary with the first problems of each failed wave and the repair step."""
    if verdict["passed"]:
        return f"BUILD_PASSED: {verdict['checked']} wave gate(s) passed"
    lines = [f"BUILD_FAILED: {len(verdict['failed'])} wave gate(s) failed: {', '.join(verdict['failed'])}"]
    for e in verdict["waves"]:
        if e["result"] != "fail":
            continue
        probs = e.get("problems") or ["(no problems recorded)"]
        lines.append(f"wave {e['wave']}:")
        lines += [f"  - {p}" for p in probs[:per_wave]]
        if len(probs) > per_wave:
            lines.append(f"  ... and {len(probs) - per_wave} more (see wave_{e['wave']}_gate_result.json)")
    first = verdict["failed"][0]
    lines.append(f"Fix the cause, then repair from w{first}_integrate (or w{first}_sessions / w{first}_gate) "
                 f"with rerun_dependent_tasks; see docs/prompts/repair-failed-wave.md")
    return "\n".join(lines)


# --- Required gate checks -----------------------------------------------------------


def required_check_problems(wave_cfg: dict, gate) -> list:
    """Every name in the wave's required_checks must be in the gate file's checks with result pass.

    A missing gate file is reported elsewhere, so nothing is added for it here.
    """
    required = wave_cfg.get("required_checks") or []
    if not required or gate is None:
        return []
    checks = {c.get("name"): c for c in (gate.get("checks") or []) if isinstance(c, dict)}
    probs = []
    for name in required:
        c = checks.get(name)
        if c is None:
            probs.append(f"required check {name!r} not reported in the gate file's checks")
        elif c.get("result") != "pass":
            detail = f": {c.get('detail')}" if c.get("detail") else ""
            probs.append(f"required check {name!r} result={c.get('result')!r}{detail}")
    return probs


# --- Genie space content matching ----------------------------------------------------

# Lists of objects are compared as sets, ordered by the first key every element has.
_SORT_KEYS = ("id", "identifier", "column_name", "name")


def _norm(v):
    if isinstance(v, dict):
        return {k: _norm(x) for k, x in v.items()}
    if isinstance(v, list):
        if v and all(isinstance(x, str) for x in v):
            return "".join(v)  # the server splits text into one list element per line
        items = [_norm(x) for x in v]
        if items and all(isinstance(x, dict) for x in items):
            key = next((k for k in _SORT_KEYS if all(k in x for x in items)), None)
            if key:
                items = sorted(items, key=lambda x: str(x[key]))
        return items
    return v


def normalise_genie_space(space: dict) -> dict:
    """Normalise a serialized Genie space (deployed or bundle source) for comparison.

    1. data_sources.metric_views is merged into data_sources.tables (the server lists both together).
    2. Lists of strings are joined (the server splits text into line arrays).
    3. Lists of objects are sorted by id / identifier / column_name / name.
    Confirmed on the Semantic Ground Truth space against ground_truth_ops.geniespace.json.
    """
    s = copy.deepcopy(space or {})
    ds = s.get("data_sources")
    if isinstance(ds, dict) and ds.get("metric_views"):
        ds["tables"] = list(ds.get("tables") or []) + list(ds.pop("metric_views"))
    elif isinstance(ds, dict):
        ds.pop("metric_views", None)
    return _norm(s)


def content_diff(source, deployed, limit: int = 10, path: str = "") -> list:
    """Paths where two normalised documents differ (at most `limit`)."""
    out = []

    def walk(a, b, p):
        if len(out) >= limit:
            return
        if isinstance(a, dict) and isinstance(b, dict):
            for k in sorted(set(a) | set(b)):
                q = f"{p}.{k}" if p else str(k)
                if k not in b:
                    out.append(f"{q}: only in source")
                elif k not in a:
                    out.append(f"{q}: only in deployed")
                else:
                    walk(a[k], b[k], q)
                if len(out) >= limit:
                    return
        elif isinstance(a, list) and isinstance(b, list):
            if len(a) != len(b):
                out.append(f"{p or '<root>'}: {len(a)} items in source, {len(b)} deployed")
                return
            for i, (x, y) in enumerate(zip(a, b)):
                walk(x, y, f"{p}[{i}]")
        elif a != b:
            out.append(f"{p or '<root>'}: differs")

    walk(source, deployed, path)
    return out


def _load_yaml(path):
    import yaml  # PyYAML ships with Databricks runtimes / serverless

    with open(path) as f:
        return yaml.safe_load(f)


def bundle_yaml_files(bundle_root: str) -> list:
    """databricks.yml plus every file its `include` globs match (relative to bundle_root)."""
    root = next((os.path.join(bundle_root, n) for n in ("databricks.yml", "databricks.yaml")
                 if os.path.isfile(os.path.join(bundle_root, n))), None)
    if root is None:
        return []
    files = [root]
    try:
        includes = (_load_yaml(root) or {}).get("include") or []
    except Exception:
        includes = []
    for pat in includes:
        for f in sorted(glob.glob(os.path.join(bundle_root, str(pat)), recursive=True)):
            if os.path.isfile(f) and f not in files:
                files.append(f)
    return files


def find_bundle_source(bundle_root: str, resource_type: str, resource_key: str):
    """(absolute path | None, basis) of resources.<resource_type>.<resource_key>.file_path.

    file_path is relative to the YAML file that declares it. Target-level overrides
    (targets.<t>.resources...) are not read.
    """
    files = bundle_yaml_files(bundle_root)
    if not files:
        return None, f"no databricks.yml in {bundle_root}"
    for f in files:
        try:
            doc = _load_yaml(f) or {}
        except Exception:
            continue
        res = ((doc.get("resources") or {}).get(resource_type) or {}).get(resource_key)
        if isinstance(res, dict) and res.get("file_path"):
            p = os.path.normpath(os.path.join(os.path.dirname(f), str(res["file_path"])))
            return p, f"{os.path.relpath(f, bundle_root)}: resources.{resource_type}.{resource_key}.file_path"
    return None, f"resources.{resource_type}.{resource_key}.file_path not found in the bundle's YAML"


def locate_genie_source(tgt: dict, build_root: str):
    """(path | None, basis) of a genie_space target's bundle source file.

    source_file (relative to the target's bundle_root) wins; else resource_key is looked up in
    the bundle's resource YAML. bundle_root defaults to build_root (relative = under build_root).
    """
    broot = tgt.get("bundle_root") or build_root
    if not os.path.isabs(broot):
        broot = os.path.join(build_root, broot)
    if tgt.get("source_file"):
        p = os.path.normpath(os.path.join(broot, tgt["source_file"]))
        basis = "source_file"
    elif tgt.get("resource_key"):
        p, basis = find_bundle_source(broot, "genie_spaces", tgt["resource_key"])
        if p is None:
            return None, basis
    else:
        return None, "no source_file or resource_key on the runtime target"
    if not os.path.isfile(p):
        return None, f"source file {p} not found ({basis})"
    return p, basis


def genie_freshness(updated_after_start, source, source_basis: str, deployed: dict, limit: int = 10) -> dict:
    """Freshness entry for a Genie space.

    updated_after_start: True / False, or None when the space has no update_time.
    source: parsed bundle source (dict) or None (source_basis says why).
    fresh = updated after the run started; current = deployed content equals the source after
    normalisation; otherwise stale (differences listed) or timestamp only (no source to compare).
    """
    if updated_after_start:
        return {"result": "pass", "basis": "fresh: updated after run start"}
    when = "has no update_time" if updated_after_start is None else "was last updated before this build run"
    if source is None:
        return {"result": "fail", "basis": f"timestamp only: {source_basis}",
                "detail": f"space {when} and there is no bundle source to compare"}
    diffs = content_diff(normalise_genie_space(source), normalise_genie_space(deployed), limit=limit)
    if not diffs:
        return {"result": "pass", "basis": "current: content matches source", "source": source_basis}
    return {"result": "fail", "basis": f"stale: content differs ({len(diffs)}{'+' if len(diffs) >= limit else ''} paths)",
            "source": source_basis, "differences": diffs,
            "detail": f"space {when} and its content differs from the bundle source"}
