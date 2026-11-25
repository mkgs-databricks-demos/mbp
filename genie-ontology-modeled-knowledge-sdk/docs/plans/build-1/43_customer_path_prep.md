# Session 43: Customer Path — Second Domain Run Plan & Dry Scaffold (R9)

## Scope
Prepare the customer-path proof: choose a second sample dataset, write the run plan and intervention log, write the example inputs, and dry-scaffold them in `/tmp` only. The child build itself is owner prerequisite P1-6 before wave 1-16.

## Context
* [REQUESTS R9](REQUESTS.md#r9-prove-the-customer-path-on-a-second-domain): follow only the published instructions (`docs/usage.md`, the guided notebook), published skills (R1) and the wheel (R2); no hand edits to generated plans or the manifest; log every intervention.
* Sessions cannot write outside `build_root`, create Git folders or deploy genie-build-waves instances; those are P1-6 steps (owner, or Devin with the owner's hand-off approval).
* The child run kit includes the exhaustive tuning protocol, so the child build also tunes until the asymptote.
* The child project gets the SDK the default way (R7a): the published wheel pinned by `sdk_version`, scaffolded with `vendor=False`. Vendoring is not exercised here (its tests cover it).

## Tasks
1. Choose the dataset: list `samples` schemas readable by the build identity; prefer `samples.bakehouse` (retail franchise sales) if readable, otherwise another multi-table schema; record why.
2. `docs/customer-path/sdk_config.example.json`: inputs for that dataset with placeholder catalog/schema/warehouse (`<target_catalog>` style); passes `config.validate_config` after placeholders are filled in a `/tmp` copy.
3. Dry scaffold into `/tmp/customer-path-dry/` with `vendor=False` (no vendored files; the metric-views bundle pins `sdk_version`): run kit renders; `validate_manifest` and `validate_authorizations` 0 errors; print task count.
4. `docs/customer-path/run_plan.md`: numbered steps exactly as `docs/usage.md` and the notebook describe them (Git folder on a feature branch, guided notebook, overrides, skills reference, vars file, `deploy_instance.py`, setup, run, monitor), who does each, and the expected evidence; an intervention log table (`# | step | who | what happened | why | fix or prerequisite | link`), empty.
5. Record in the summary any step in `docs/usage.md` that is unclear or contradicts the notebook (do not edit usage.md; session 44 owns it later).

## Acceptance Criteria
- [ ] Gate checks `run_plan` and `dry_scaffold` pass.
- [ ] Nothing written outside `docs/customer-path/` and `/tmp`.

## Owned Paths
- `docs/customer-path/**`

## Dependencies
- Sessions 23b, 27, 28, 29 (published wheel and skills, run kit, guided notebook); 42 (TPC-H done first).
