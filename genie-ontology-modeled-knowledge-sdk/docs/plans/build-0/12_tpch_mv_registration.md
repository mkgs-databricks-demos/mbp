# Session 12: TPC-H Dogfood — Metric View Registration

## Scope
Deploy `examples/tpch/ontology-metric-views` to the `dev` target, run its `register_metric_views` job, and confirm that every metric view registers, answers a `MEASURE()` query, and passes the cardinality test. Fix defects in the bundle, notebooks or YAMLs until it does (max 4 deploy/run attempts). Write results to `examples/tpch/docs/registration/`.

## Context
* This is the only deploying session in its wave (`allow_deploy: true`). Deploy and run with the runDatabricksCli tool and `workingDirectory` = the bundle folder (the CLI is blocked in executeCode shells): `bundle validate --strict -t dev`, `bundle deploy -t dev`, `bundle run register_metric_views -t dev`.
* Values come from the owner's gitignored `.databricks/bundle/dev/variable-overrides.json`. Never print them into committed files; refer to `<catalog>.<schema>` in docs. Real run ids and resolved names go only in the session summary.
* A defect in a template-derived file (notebooks, job YAML) means the template (session 06) has the same defect. Fix it here in `examples/tpch/` only, and list it under "Template fixes for build 1" in the summary with the exact diff. `templates/` is not owned in this wave.
* `bundle run` of jobs that change grants may be refused to unattended sessions. If the schema grant step is refused, stop `blocked` with the exact owner command.

## Tasks
1. Validate, deploy, run. On failure, read the task run output (forEach iteration errors), fix, and repeat (max 4 attempts).
2. Check: the registration job's last run in this build run is SUCCESS; every manifest entry exists as a metric view in the target schema; the smoke test ran `MEASURE()` for each; cardinality test passed.
3. `examples/tpch/docs/registration/registration_results.md`: a table of MV name, registered, smoke pass, cardinality pass, attempts; defects fixed.

## Acceptance Criteria
- [ ] Integrator check `registration_job`: the registration job run that started during this build run ended SUCCESS (run id in the session summary).
- [ ] Integrator check `mv_smoke`: every `manifest.json` entry answered a `MEASURE()` query (results file shows all pass).
- [ ] `bundle validate --strict -t dev` exits 0 at the end.

## Owned Paths / Assets
- `examples/tpch/ontology-metric-views/**`
- `examples/tpch/docs/registration/**`
- Workspace: the dev deployment of the dogfood metric-views bundle, its job, schema and metric views.

## Dependencies
- Session 11: YAMLs + manifest. Session 09: dogfood bundle. Manual prerequisite: overrides file.
