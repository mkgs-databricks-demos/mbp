# L300 Pipeline-Run Plans (reference)

These are the original L300 session plans, plan index and `waves.json` from the initial design. They describe **running** the SDK pipeline against one domain (Waves 0-8: scaffold, research, context, EDA, metric view synthesis, registration, UC Pages, agent curation, deployment, tuning).

They are **not** an active genie-build-waves manifest. Use them as design input:

* build-0 ([docs/plans/build-0/](../../plans/build-0/)) builds the reusable SDK from them, then dogfoods it on `samples.tpch`.
* build-0 session 08 turns them into the run kit under `templates/run/` (valid wave ids, parallel discovery wave, `owned_paths`, `allow_deploy`, no Git commands in sessions).

Known issues in these files (fixed in the run kit, not here): wave id `5.5` fails `validate_manifest`; waves 1-3 are separate waves, so they do not run in parallel; plan 01 runs `git checkout -b`; file-writing sessions use `execute` mode with only `owned_assets`; deploying sessions lack `allow_deploy`. See [PROJECT_MEMORY.md](../../../PROJECT_MEMORY.md).
