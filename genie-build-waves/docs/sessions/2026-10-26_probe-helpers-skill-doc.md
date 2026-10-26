# 2026-10-26 — Probe helper return values in the session runner skill

**Branch:** `mg-genie-probe-helpers-skill-doc` (from `main` `fc3f292`) · **Request:** [docs/plans/2026-10-26_request-probe-helpers-skill-doc.md](../plans/2026-10-26_request-probe-helpers-skill-doc.md)

## Problem

Semantic Ground Truth build 4, session 36 (runs `110489694161084` and `655172288447819`) raised the same request twice: the session runner `SKILL.md` (converge mode, "Apps with `probes`") named `probe_client(...)` then `run_app_probes(..., probe_w=...)` without saying what they return. Sessions passed the whole `probe_client` result as `probe_w`.

## Root cause

Doc gap only. `src/notebooks/app_probes.py` returns tuples: `probe_client` -> `(client, identity_label)` (line 36), `run_app_probes` -> `(results, problems)` (line 188). Both gate notebooks already unpack them (`wave_gate_check.ipynb` line 426, `app_probe_check.ipynb` line 167) and wrap the calls in `try/except`, because `probe_client` raises `ValueError` for a missing `probe_auth` or an unreadable secret.

## Changes

* `SKILL.md` line 121: both calls shown unpacked, return values stated, pass = `problems` empty; `probe_client`'s `ValueError` is to be caught and treated as `blocked`; `run_app_probes` reports bad credentials in `problems` instead of raising.
* Request doc reviewed and tightened before the change (added the error case, dropped the optional `manifest-schema.md` edit, split rollout notes from done criteria), then marked done.

## Decisions

* No change to `app_probes.py` (docstrings already correct), `docs/manifest-schema.md` (does not name the helpers), `docs/design/` or `docs/sessions/` (historical).
* README reviewed: no change needed. It describes `app_probes.py` only at module level (line 72), and its skill-change guidance (line 284: edit `SKILL.md`, re-run setup to republish) already covers this.
* No tests reference `SKILL.md` or the probe helpers.

## Rollout

* `mbp` is checked out on this branch, so automations that read the workspace `SKILL.md` (the Semantic Ground Truth default instance) see the change in sessions that start from now on, including later waves of build 4 (run `655172288447819`). Doc-only, so safe mid-build.
* The UC-published `genie_build_session_runner` skill updates on the next setup run after merge; do not run setup while a build is in progress.

## Files modified

* `src/skills/genie-build-session-runner/SKILL.md`
* `docs/plans/2026-10-26_request-probe-helpers-skill-doc.md` (new)
* `docs/sessions/2026-10-26_probe-helpers-skill-doc.md` (new)
* `docs/sessions/INDEX.md`
