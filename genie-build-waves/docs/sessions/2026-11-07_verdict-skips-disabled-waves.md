# build_verdict skips disabled waves (2026-11-07)

Branch `mg-genie-build-waves-verdict-disabled` (from `mg-genie-build-waves-continuation` at cef6884, because the jobs run the live Git folder and depend on the continuation code).

## Problem

AgenticTrading Build 5 run C (604746454289722) has waves 5-0 to 5-7 disabled in the job, because they finished in earlier runs. Their `w<wave>_gate` tasks end with result state `DISABLED`. `build_verdict` treated every state other than `SUCCESS` and `EXCLUDED` as a crashed gate, so the run failed with `BUILD_FAILED: 9 wave gate(s) failed: 5-0, ..., 5-7, 5-10`, even though only 5-10 had failed.

## Change

* `src/notebooks/gate_helpers.py`: new `SKIPPED_GATE_STATES` (`EXCLUDED` -> `excluded`, `DISABLED` -> `disabled`). `build_verdict` ignores both, even when an older result file exists. The verdict gains a `disabled` list, and `verdict_message` appends `(N disabled wave(s) skipped: ...)` to both `BUILD_PASSED` and `BUILD_FAILED`.
* `tests/test_gate_helpers.py`: `test_verdict_ignores_disabled_waves` (disabled + stale fail result ignored, disabled before a real failure still fails and names only that wave).
* `src/notebooks/build_verdict.ipynb` (markdown) and `README.md`: document `DISABLED`.

## Verification

* pytest on a /tmp copy: 137 passed (baseline 136). The new test fails on the old `gate_helpers.py`.
* Replay of run C's real task states and gate result files: before `BUILD_FAILED: 9 ...`; now `BUILD_FAILED: 1 wave gate(s) failed: 5-10 (8 disabled wave(s) skipped: 5-0, ..., 5-7)` (5-10's result file is from before its owner fixes).

## Notes

* No bundle redeploy or setup run needed: the job runs the notebooks from the live Git folder.
* `wave_gate_check` needs no change: a disabled wave's `gate_check` is disabled too.
