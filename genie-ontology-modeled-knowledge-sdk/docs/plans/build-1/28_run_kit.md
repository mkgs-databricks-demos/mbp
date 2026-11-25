# Session 28: Run Kit Fixes & Exhaustive Tuning Waves (R3)

## Scope
Make `templates/run/` a manifest a customer can run unchanged under genie-build-waves, including the build-0 lessons and the exhaustive tuning protocol.

## Context
* [REQUESTS R3](REQUESTS.md#r3-fix-the-run-kit) items 1-7, owner item "run approvals" (build-0 session 12), build-0 note "09: gate grep matches the test fixture".
* Framework rules from build 0 (genie-build-waves planner skill): top-level `branch`; tier 1 for an `allow_deploy` session covers only `bundle:build_root`, so each deploying session needs `bundle.deploy` naming its project bundle and `jobs.run_now` for any job it runs; `owned_assets` text must equal the authorization target for monitor grants; `manual_prereqs` for owner steps; deploying waves have one session.
* Use this build's manifest (`docs/plans/waves.json`, waves 1-5..1-14) as the reference shape for the dogfood-equivalent waves.

## Tasks
1. `{{branch}}` token rendered by `scaffold.RUN_TOKENS` into the top-level `branch`.
2. `authorization_policy.monitor_may_authorize` (`jobs.run_now`, `bundle.deploy`, `volume.write`, `workspace.write` on `owned_assets`); explicit `authorizations` and matching `owned_assets` for: registration (`bundle.deploy` metric-views bundle, `jobs.run_now` registration job, `volume.write` wheel), Pages (`workspace.write` draft pages in the project domain), agent deployment and every tuning wave (both bundles + registration job).
3. Pages wave: `manual_prereqs` (a Discover domain id in `sdk_config.pages_domain_id`, new optional schema key, or owner approval to create one); without it the session runs the dry run only and ends `pass` with "publishing deferred". Live upserts always pass `domain_id`, `status=DRAFT` unless `sdk_config.pages_status` says otherwise.
4. Tuning: replace the single tuning session with: benchmark authoring wave (parallel sessions by view group + cross-view), baseline wave, three mandatory iteration waves, three conditional iteration waves (converged -> pass without change), asymptote gate on the last, then the independent report-simulation wave. Gates mirror waves 1-6..1-14 here; accuracy targets are recorded, the asymptote and coverage are required checks.
5. Skills: session scopes load skills by Unity Catalog id from `sdk_config.skills` with the workspace folder as fallback.
6. Agents session renders with `geniespace render --params docs/registration/resolved_target.json --check`.
7. Gate text: pytest commands set `GENIE_BUILD_WAVES_DIR`; the overrides-file grep is scoped to `.databricks/` paths.
7b. **SDK wheel (R7a).** `{{sdk_version}}` token rendered from the SDK's `__version__`; the registration wave gets a `manual_prereqs` entry for the SDK wheel volume (`sdk_volume_path` in the metric-views overrides, `READ VOLUME` for the project's run-as principals and the genie-build-waves run-as user); gates check the registration job imported the installed wheel. A project scaffolded with `vendor=True` drops that prerequisite (record the mode in `sdk_config.json` as `sdk_distribution: wheel|vendored`, a new optional schema key).
8. `tests/test_run_kit.py`: top-level `branch`; every `allow_deploy` session has `bundle.deploy` naming a project bundle; registration and tuning sessions have `jobs.run_now`; the Pages wave has its `manual_prereqs`; tuning has >= 3 mandatory iteration waves and an asymptote check; `validate_manifest` and `validate_authorizations` return 0 errors and 0 warnings on the rendered kit; a broken copy fails.
9. `templates/run/INDEX.md`, `PROJECT_MEMORY.md` starter and `README.md` updated to match.

## Acceptance Criteria
- [ ] Gate checks `run_kit_validate` and `run_kit_negative` pass.
- [ ] Rendered kit task count is under the 1,000-task Jobs limit (print `job_task_count`).

## Owned Paths
- `templates/run/**`, `src/genie_ontology_modeled_knowledge_sdk/{scaffold,config}.py`, `src/genie_ontology_modeled_knowledge_sdk/schemas/**`, `tests/test_run_kit.py`, `tests/test_config.py`

## Dependencies
- Session 27 (skill ids, `skills` key), 21 (resolved target), 22 (benchmark API), 23/23b (wheel variables and stable path), 26 (tuning protocol).
