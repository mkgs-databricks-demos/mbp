# Session 25: Synthesis & Curation Skills — Reconcile, Verify Patterns on the Platform (R8)

## Scope
Reconcile `ontology-mv-synthesis` and `ontology-agent-curation` with the platform `metric-views` skill and the workspace metric-view generation skill, fix build-0 observations 16-20, 23, 26 and 27, and verify the new YAML patterns by registering scratch metric views.

## Context
* [REQUESTS R8](REQUESTS.md#r8-reconcile-overlapping-skills). `ontology-mv-synthesis` keeps SDK rules only: tokens, manifest, `# verified:` joins, subdomain comments, materialization ranking, MV-first. Metric view syntax is referenced, not restated.
* Scratch location: the **SDK schema** (the SDK bundle's schema, deployed by session 18; resolve it with `databricks bundle summary -t dev` at `build_root`). You are authorized for `sql.ddl` there for views named `scratch_*` only: `CREATE OR REPLACE VIEW scratch_... WITH METRICS LANGUAGE YAML`; never `DROP`, never another name or schema. List every `scratch_*` view you created in your summary (cleanup is an owner step after the build). Source data: `samples.tpch` (read-only).
* Session 19 may send a request about the L200-G agent-size rule text: apply it (split at `min(max_metric_views_per_agent, 30)`).

## Tasks
1. Platform checks (record SQL, outcome and error text in `docs/research/platform-pattern-checks.md`, with no catalog or schema names: use `<sdk_schema>`):
   * obs 16: a share-of-total measure (national market share) in one view: try window measures / `MEASURE()` over a total and record what works;
   * obs 17: a snowflake dimension through a nested join path (`orders.customer.customer_nation.n_name`);
   * a `FILTER` measure and a `format` block on a ratio (for obs 30);
   * obs 20: an `EXPLAIN` of the rendered DDL as a cheaper dry run; record whether it catches the errors registration catches.
2. `ontology-mv-synthesis`: verified patterns into `references/yaml-patterns.md` (obs 16, 17); materialization candidates ranked and capped per domain (obs 18: rank by joins x rows, at most 3 per domain unless justified); two-formula KPIs get distinct measure names per basis plus an owner decision note (obs 19); optional platform dry run step (obs 20).
3. `ontology-agent-curation`: import-API path for writing `*.geniespace.json` from unattended sessions (obs 23); `information_schema` check that the overrides / `resolved_target.json` schema holds the registered views before `EXPLAIN` (obs 26); curation replaces the scaffold placeholder, and an existing placeholder is an owner deletion (obs 27); render with `--params resolved_target.json --check`.
4. Package wording (R2) and SDK-only descriptions (R8); record overlap notes for session 26's `skills/README.md` in your summary.

## Acceptance Criteria
- [ ] Gate check `skills_reconciled` passes for these two skills.
- [ ] `platform-pattern-checks.md` has one row per check with pass/fail and the error text; every pattern added to `yaml-patterns.md` is marked verified there.
- [ ] No DDL other than `CREATE OR REPLACE VIEW scratch_*` in the SDK schema (list every statement in the summary).

## Owned Paths / Assets
- `skills/ontology-mv-synthesis/**`, `skills/ontology-agent-curation/**`, `docs/research/platform-pattern-checks.md`
- `scratch_*` metric views in the SDK schema.

## Dependencies
- Sessions 18 (SDK schema), 19 (render flags, split rule).
