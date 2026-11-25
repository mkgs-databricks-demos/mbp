# 2026-11-25 - Wave 1-2, session 25: synthesis & curation skills reconciled, patterns verified (R8)

Run `109257611554257`, branch `mg-genie-ontology-build-1-plan` (checked read-only: clean, on branch), mode `edit` (allow_execute). No Git commands beyond `status`. Owner authorization used: `sql.ddl` for `CREATE OR REPLACE VIEW scratch_* ... WITH METRICS` in the SDK schema (resolved with `databricks bundle summary -t dev` at `build_root`). No DROP.

## Problems and root causes

* Obs 16/17: the skill had no tested share-of-total or nested-join pattern; synthesis only learned of path errors at registration.
* Obs 18: the materialization thresholds are met by nearly every star-schema view, so there was no ranking or cap.
* Obs 19: no rule for a KPI that has two candidate formulas.
* Obs 20: synthesis checks were static only. It was not known whether `EXPLAIN` of the DDL works as a cheaper dry run.
* Obs 23/26/27, plus the session 19 and 21 requests: the curation skill used the 50-view rule (the platform limit is 30 data sources). It said nothing about the import API for `*.geniespace.json`, the schema drift check or the placeholder agent, and it rendered from hand-written overrides.
* R2/R8: both skills used a `PYTHONPATH=<sdk src>` / vendored form, restated platform syntax rules, and had descriptions that could trigger on general metric view requests.

## Platform checks (task 1)

Full table with error text: `docs/research/platform-pattern-checks.md` (C1-C8). Every passing query was cross-checked against the same aggregate in plain SQL.

* C1 share of total via a window measure (`range: all`): **pass**, matches plain SQL.
* C2 fixed-LOD share: **pass** with a caveat (it ignores query filters).
* C3 naive `MEASURE(a)/MEASURE(total)`: registers but returns 1.0 at every grain (anti-pattern).
* C4 `FILTER` measure ratios: **pass**. C5 percentage `format` on ratios: **pass**; the value stays 0-1.
* C6 nested three-level join path: **pass**. C7 leaf-only path: fails at registration with `UNRESOLVED_COLUMN`.
* C8 `EXPLAIN` as a dry run: **does not work**. It returned a plan for all five broken definitions, while registration rejected each one (FIELD_NOT_FOUND, UNRESOLVED_COLUMN x2, invalid version, invalid materialization dimension).

## Changes

* `skills/ontology-mv-synthesis/SKILL.md`: description is SDK-stage-only. Platform `metric-views` skill referenced for syntax, with a precedence note. The rule list was reduced to SDK rules (wildcard ban, tokens, `# verified:`, nested-path rule, ratio unit comment, share-of-total pattern, two-formula rule). Materialization now ranks candidates by joins x rows, caps blocks at 3 per domain unless justified, and puts the ranking table in the summary. `gos-validate-mv` replaces the `PYTHONPATH` form. New step 6 is an optional platform dry run (register as `scratch_<view>` only when authorized, never `EXPLAIN`, never DROP).
* `skills/ontology-mv-synthesis/references/yaml-patterns.md`: added the verified nested-join (C6, C7), share-of-total (C1, C3) and FILTER + percentage format (C4, C5) patterns, a two-formula KPI pattern (convention only, not a platform check), and an "errors only registration catches" table (C7, C8).
* `skills/ontology-agent-curation/SKILL.md`: description is SDK-stage-only. Split at `min(max_metric_views_per_agent, 30)` via `effective_max_per_agent`. A single-agent manifest lists the real subdomains. `config_warnings` is noted. Agent files are written through the import API with a sha256 read-back (obs 23). The `ontology_agent` entry in `resources/genie_agents.yml` is replaced, and an old placeholder file becomes an owner deletion request (obs 27). The skill renders with `gos-render-agents render ... --params docs/registration/resolved_target.json --check`, which checks the schema and identifiers through information_schema before any EXPLAIN (obs 26).
* `docs/research/platform-pattern-checks.md` (new).

## DDL statements run (all in `<sdk_schema>`)

| Statement | Outcome |
|---|---|
| `CREATE OR REPLACE VIEW scratch_share_window` | created |
| `CREATE OR REPLACE VIEW scratch_share_fixed_lod` | created |
| `CREATE OR REPLACE VIEW scratch_filter_ratio` | created |
| `CREATE OR REPLACE VIEW scratch_nested_join` | created |
| `CREATE OR REPLACE VIEW scratch_share_naive` | created |
| `CREATE OR REPLACE VIEW scratch_broken_{column,path,filter_ref,version,materialization}` | 5 failed, nothing created |
| `EXPLAIN CREATE OR REPLACE VIEW` of the five broken ones and `scratch_explain_valid` | plan only, nothing created |

Afterwards, `information_schema.tables` for the schema listed exactly the five created views. **Owner cleanup:** drop those five `scratch_*` views after the build.

## Checks

| Check | Result |
|---|---|
| Front matter `name` equals folder name (both skills) | pass |
| Description names the Genie Ontology Modeled Knowledge SDK stage (both) | pass |
| No `PYTHONPATH`, `_vendored` or `sys.path` in either skill | pass (grep: none) |
| No stale 50-view agent rule in curation | pass (grep: none) |
| Every `verified Cn` in yaml-patterns has a row in platform-pattern-checks.md | pass (C1, C3-C8 cited; C1-C8 present) |
| SDK static validator on the verified patterns (tokenized, `# verified:` lines) | pass: 3 files, 0 errors, 0 warnings |
| Scratch query results vs plain SQL | pass (C1, C4, C6 values match) |
| bundle validate | skipped: no YAML touched |

Not checked: the import-API snippet in the curation skill (`w.workspace.import_` with `format=RAW`; session 14 used it successfully) was not re-run here, and the `w.workspace.download` read-back call was not executed in this session.

## Overlap notes for session 26 (`skills/README.md`)

* `ontology-mv-synthesis` relies on the platform `metric-views` skill (`using-metric-views`: joins-correctness, level-of-detail, window-measures, materialization, semantic-metadata). The platform skill wins on syntax; the SDK skill wins on tokens, `# verified:`, `# subdomain:`, the manifest, materialization ranking and cap, and MV-first.
* It overlaps the workspace `metric-view-generation` user skill (same trigger area). The SDK skill triggers only inside an SDK run project (`sdk_config.json`) or for a named build-waves stage.
* `ontology-agent-curation` relies on the SDK `geniespace` module and the agents bundle README. It overlaps any general Genie space authoring skill and is scoped to SDK run projects only.

## Requests

* Owner: drop the five `scratch_*` views listed above after the build.
* Owner: in older projects (e.g. `examples/tpch/`), delete `ontology-genie-agents/agents/ontology_agent.geniespace.json`; it is still an open build-0 item.

## Files modified

* `skills/ontology-mv-synthesis/SKILL.md`
* `skills/ontology-mv-synthesis/references/yaml-patterns.md`
* `skills/ontology-agent-curation/SKILL.md`
* `docs/research/platform-pattern-checks.md` (new)
