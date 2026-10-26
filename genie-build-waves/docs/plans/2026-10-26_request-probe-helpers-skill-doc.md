# Request: document what the probe helpers return in the session runner skill

**Status:** done 2026-10-26 on branch `mg-genie-probe-helpers-skill-doc` (commit `2a3317b`; UC skill republish pending the next setup run) · **From:** Semantic Ground Truth build 4, session 36 (raised in runs `110489694161084` and `655172288447819`) · **Date:** 2026-10-26 · **Size:** small doc fix (one bullet in `SKILL.md`), no code change

## Problem

`src/skills/genie-build-session-runner/SKILL.md` line 121 (converge mode, "Apps with `probes`") says:

> `probe_client(w, probe_auth, dbutils.secrets.get)` then `run_app_probes(w, app_name, probes, probe_w=...)`

It does not say what either call returns. Reading it, a session assumes `probe_client` returns a client and passes the whole result as `probe_w`. But `src/notebooks/app_probes.py` (checked on `main` at `fc3f292`) returns tuples:

| Function | Line | Returns |
| --- | --- | --- |
| `probe_client(w, auth, get_secret)` | 36 | `(client, identity_label)`; the label names the secret, never its value |
| `run_app_probes(w, app_name, probes, ..., probe_w=None)` | 188 | `(results, problems)` |

The gate already unpacks both correctly (`wave_gate_check.ipynb` line 426: `pw, info["probe_identity"] = probe_client(...)`; `app_probe_check.ipynb` line 167: `pw, probe_identity = probe_client(...)`). Only the skill text is wrong.

Impact: session 36 hit this in both build 4 runs and recorded it as a request each time (`.build-status/<run>/36.json` `requests`, copied into `wave_4-4_gate.json`). The status files do not say how many steps it cost. Converge sessions are already close to the step limit, so every misleading line matters.

## Requested change

In `src/skills/genie-build-session-runner/SKILL.md` line 121, replace

`probe_client(w, probe_auth, dbutils.secrets.get)` then `run_app_probes(w, app_name, probes, probe_w=...)`

with

`pw, probe_identity = probe_client(w, probe_auth, dbutils.secrets.get)` (returns `(client, identity_label)`), then `results, problems = run_app_probes(w, app_name, probes, probe_w=pw)` (returns `(results, problems)`; pass when `problems` is empty). `probe_client` raises `ValueError` when `probe_auth` is missing or a secret cannot be read; wrap both calls in `try/except` the way the gate does and treat that as `blocked` (an access problem). `run_app_probes` does not raise on bad credentials; it reports them in `problems`.

`docs/manifest-schema.md` does not name the helpers, so it needs no change. `docs/design/` and `docs/sessions/` mention them as historical records and stay as they are.

## Done when

* `SKILL.md` shows both calls unpacked as above and says how to handle the `ValueError` from `probe_client`.

## Rollout

* When it takes effect: automations that point at the workspace `SKILL.md` pick it up as soon as the change is on the branch checked out in `mbp/genie-build-waves`. The Semantic Ground Truth default instance does this today, because its 2026-10-26 setup reported `skills_published: false` (a finalize timeout, although the skills did finalize). Automations that load the UC skill need setup to republish `genie_build_session_runner`, and setup must not run while a build is in progress (it resets the build job).
* Sessions read `SKILL.md` when they start, so a change merged during a build applies to later waves only. Semantic Ground Truth build 4 (run `655172288447819`) is running; waves 4-5 to 4-9 have not all started. A doc-only change is safe for it.

## Not in scope

No change to `app_probes.py`; its docstrings are already correct.
