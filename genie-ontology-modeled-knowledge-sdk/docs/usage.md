# Using the Genie Ontology Modeled Knowledge SDK

This guide runs the SDK pipeline end to end for one domain: scaffold a project, set the workspace overrides, run the pipeline with a genie-build-waves instance and the run kit, and check the outputs of each wave. The [TPC-H example](../examples/tpch/README.md) is a complete project produced this way by build-0.

Build-0 dogfooded the SDK through its own manifest ([docs/plans/waves.json](plans/waves.json)), not through the run kit. Known run-kit gaps are listed in [build-1 request R3](plans/build-1/REQUESTS.md) and in [build-0 observations](build-0-observations.md); read them before a customer run.

## 0. Set up the SDK (once per workspace)

Before any project, choose where the SDK lives and deploy it as a bundle. Open `notebooks/setup_sdk` from the SDK folder on serverless and fill its widgets:

| Widget | Meaning |
|---|---|
| `sdk_catalog` | Existing catalog for the SDK schema (required) |
| `sdk_schema` | SDK schema. A **new** schema the SDK bundle creates is recommended (default `ontology_sdk`; the `dev` target prefixes it `dev_<user>_`) |
| `schema_mode` | `new` (recommended; targets `dev` or `prod`) or `existing` (the schema must exist; target `prod_existing_schema` creates only the `sdk_wheels` volume) |
| `consumer_group` | Group granted `USE_SCHEMA` and `READ_VOLUME` (required for `prod` targets) |
| `warehouse_id` | SQL warehouse (required) |

The notebook calls `setup_project.setup_sdk`: it checks that the catalog exists and that you can create the schema (or that the existing schema exists and you can create a volume in it), then writes the SDK bundle's gitignored `.databricks/bundle/<target>/variable-overrides.json` and prints the exact steps. Nothing is deployed, granted or created by the notebook; a missing catalog writes nothing. Then, from a terminal at the SDK root:

1. `databricks bundle validate --strict -t <target>`
2. `databricks bundle deploy -t <target>`: creates the schema (new mode) and the `sdk_wheels` volume, builds the wheel and uploads it to `<sdk_volume_path>/.internal/` ([wheel publishing](distribution/wheel_publish.md)).
3. `databricks bundle run sdk_smoke -t <target>`: proves the wheel installs and prints its version.
4. `databricks bundle summary -t <target>`: note the resolved SDK schema and the `sdk_wheels` volume path; projects need both.
5. Publish the six skills into the same schema with `notebooks/publish_skills` ([skills publishing](skills/README.md)).

## Getting the SDK

| Way | When | How |
|---|---|---|
| **Wheel** (default) | Every project | The SDK bundle publishes `genie_ontology_modeled_knowledge_sdk-<version>-py3-none-any.whl` to its `sdk_wheels` volume. Readers need `READ VOLUME` on it (`consumer_group`; project run-as principals and the genie-build-waves run-as user must be members). Projects pin `sdk_version` in the metric-views overrides; the job environment installs `<sdk_volume_path>/.internal/genie_ontology_modeled_knowledge_sdk-<sdk_version>-py3-none-any.whl`. In notebooks: `%pip install --upgrade databricks-sdk <wheel path>` then `dbutils.library.restartPython()` |
| **Vendored** (opt-in) | No package egress or locked-down workspaces | `vendor` = `true` in the init notebook, `scaffold_project(..., vendor=True)` or `gos-scaffold --vendor`: copies the SDK modules the project notebooks import into `ontology-metric-views/src/genie_ontology_modeled_knowledge_sdk_vendored/` plus a `VENDORED_VERSION` file. No wheel prerequisite |
| **Editable install** | SDK development | `pip install -e .` at the SDK root (add `.[dev]` for pytest, ruff, mypy). The init notebook falls back to `<sdk>/src` only when the package is not installed and it runs from an SDK checkout |

## 1. Prerequisites

* A Unity Catalog workspace with serverless compute (jobs and notebooks) and a SQL warehouse.
* Genie (Genie Agents) enabled, and Discover domains if you want UC Pages.
* A target catalog where you can create a schema and views. Source tables need `SELECT` only; they are never written.
* Databricks CLI with Declarative Automation Bundles support for `genie_spaces` and `engine: direct` (build-0 used v1.27.0).
* Python 3.10+ with `pyyaml` and `jsonschema` for the local CLIs and tests (`pip install pyyaml jsonschema pytest`).
* A Git folder for the project, on a feature branch (never `main`).
* A [genie-build-waves](../../genie-build-waves/README.md) checkout, to deploy a build instance for the run.
* SDK setup done (step 0): the SDK bundle deployed, the wheel published and the six SDK skills published in the SDK schema.

## 2. Set up a project with the guided notebook

Open the `notebooks/init_ontology_project` notebook from the SDK folder on serverless and run it top to bottom. It takes a project from inputs to ready to run:

1. The first cells install the dependencies and, when `sdk_wheel` is set, the published SDK wheel, then restart Python.
2. Fill the widgets. They start **empty** and the notebook does nothing until the required inputs are set (`domain_name`, `domain_context`, `target_catalog`, `target_schema`, a source input). The `example` dropdown (`none`, `tpch`) prefills them from `examples/tpch/sdk_config.json`; non-empty widgets win. For the setup step also set `warehouse_id`, `consumer_group`, `curator_group`, `sdk_volume_path` (from step 0's bundle summary), `skills_catalog` / `skills_schema` (the SDK schema), `branch` and optionally `pages_domain_id`, `vars_file` and `genie_build_waves_dir`. `sdk_version` defaults to the installed SDK version; `vendor` defaults to `false` (see [Getting the SDK](#getting-the-sdk)).
3. The notebook runs `config.validate_config` and `config.check_access`, then `setup_project.check_prereqs`, which reports each prerequisite as `pass` or `action`: target catalog access and CREATE SCHEMA, the warehouse, the project folder is a Git folder on a feature branch (not `main`), the skills schema and the six skills, the Pages domain (if set) and, in wheel mode, the SDK wheel for `sdk_version` at its stable path.
4. With `target_dir` set it scaffolds the project (`scaffold.scaffold_project`, `vendor` passed through), writes both gitignored `variable-overrides.json` files from the same inputs (`setup_project.write_overrides`, see step 3), and writes the genie-build-waves vars file when `vars_file` is set (`setup_project.write_vars_file`; it must be outside the project because it holds workspace paths).
5. It ends with a checklist of what is done and what you still have to do, and the exact deploy, setup and run commands.

Re-running with the same inputs changes nothing. Edited files (scaffold files, overrides, vars file) are kept unless `force` is `true`.

The scaffold is also available from a terminal with the installed SDK:

```bash
gos-scaffold --config <project>/sdk_config.json --target <project> --project-name <name> --sdk-root <sdk checkout>
```

The scaffold writes:

| Path in the project | Contents |
|---|---|
| `sdk_config.json` | validated inputs |
| `PROJECT_MEMORY.md` | run memory starter |
| `ontology-metric-views/` | metric view bundle (DAB 1); installs the SDK wheel (with `vendor=True`, vendored SDK modules under `src/genie_ontology_modeled_knowledge_sdk_vendored/`) |
| `ontology-genie-agents/` | Genie Agent bundle (DAB 2) |
| `docs/plans/` | run kit: `waves.json`, `INDEX.md`, `README.md`, `plans/*.md` |
| `docs/{research,semantics,context,data_profiles,registration,pages,deployment,tuning,sessions}/` | empty output folders |

Re-running the scaffold writes nothing unless `force` is set, and it never touches `.databricks/` or `.rendered/`.

## 3. The overrides files

Both bundles read workspace-specific values from gitignored files. The guided notebook writes them from the same inputs (never commit them):

| File | Keys |
|---|---|
| `ontology-metric-views/.databricks/bundle/<target>/variable-overrides.json` | `catalog`, `schema_name`, `warehouse_id`, `consumer_group`, `source_catalog`, `source_schema`; wheel mode adds `sdk_volume_path`, `sdk_version` |
| `ontology-genie-agents/.databricks/bundle/<target>/variable-overrides.json` | `catalog`, `schema`, `warehouse_id`, `consumer_group`, `curator_group` |

The agents bundle `schema` must be the schema DAB 1 actually registers into. In the `dev` target that is the dev-prefixed schema (`dev_<user>_<schema_name>`, where `schema_name` is the scaffolded `target_schema`); `write_overrides` resolves it from the current user. A mismatch blocked build-0 wave 0-8 once; check it with `information_schema.tables` after registration. Variable details are in the [metric views template README](../templates/ontology-metric-views/README.md) and the [Genie Agents template README](../templates/ontology-genie-agents/README.md).

Check both bundles before the run:

```bash
cd <project>/ontology-metric-views && databricks bundle validate --strict --target dev
cd ../ontology-genie-agents
gos-render-agents render agents .rendered --params .databricks/bundle/dev/variable-overrides.json
databricks bundle validate --strict --target dev
```

The render step is needed because the bundle CLI does not interpolate `${...}` inside `genie_spaces` space files. Agent files stay tokenized (`${target_catalog}.${target_schema}.<view>`); `.rendered/` is gitignored.

## 4. Deploy genie-build-waves for the run

Commit the scaffolded files on the feature branch, then follow the [run kit README](../templates/run/README.md):

1. Deploy a genie-build-waves instance for the project ([genie-build-waves README](../../genie-build-waves/README.md)) with:
   * `build_root` = the project root (the folder with `sdk_config.json`)
   * `manifest_path` = `<build_root>/docs/plans/waves.json`
   * `branch` = the feature branch
   The guided notebook writes this vars file (`vars_file` widget) and prints the `scripts/deploy_instance.py` commands.
2. The SDK skills are loaded by Unity Catalog id from the SDK schema (step 0); sessions fall back to `<sdk>/skills/<folder>/SKILL.md` if a skill is not in their skill list.
3. Run setup and check that `validate_manifest` reports 0 errors. Review the rendered session authorizations. Deploying sessions need `bundle.deploy` on their bundle, and the registration and tuning sessions also need a run of `register_metric_views` (in build-0, deploy approval alone was not enough).
4. UC Pages need an existing Discover domain. If there is none, the pages session ends `blocked` and **its wave gate fails**, which stops the build: later waves do not run until a domain exists, or the owner defers publishing (marks the session `pass` with a note and repairs the wave from its integrate task). Create or choose a domain before the build, or plan to defer and publish later from the owner cell in `docs/pages/pages_registration.md`. Build-1 request [R3 item 3](plans/build-1/REQUESTS.md#r3-fix-the-run-kit) adds a domain prerequisite and a deferred path so the wave passes.
5. Start the build job and watch each wave gate. Review and merge the feature branch PR yourself; sessions never push to `main`.

To redo part of a run, start the job with `only` set to the wave task keys you need (for example the deployment and tuning waves after a metric view fix).

## 5. Expected outputs per wave

Wave ids and sessions are those of the run kit ([run kit INDEX](../templates/run/INDEX.md)). The last column links the matching TPC-H output from build-0.

| Wave | Session(s) | Outputs | Gate evidence | TPC-H example |
|---|---|---|---|---|
| `0` Inputs check | 01 | `docs/inputs_report.md` | config valid, sources readable | `examples/tpch/sdk_config.json` |
| `1` Discovery | 02, 03, 04 | `docs/research/*.md`, `docs/semantics/<term>.md`, `docs/context/**`, `docs/data_profiles/*.md` + `data_model_summary.md` | research sources, glossary parses, verified join cardinalities | [data model summary](../examples/tpch/docs/data_profiles/data_model_summary.md) |
| `2` Metric view synthesis | 05 | `ontology-metric-views/metric_views/<domain>/*.yml` + `manifest.json` | `mv_yaml validate` exit 0, no literal source names | [manifest.json](../examples/tpch/ontology-metric-views/metric_views/manifest.json) |
| `3` Registration | 06 | registered metric views; `docs/registration/registration_results.md` | `registration_job`, `mv_smoke` | [registration results](../examples/tpch/docs/registration/registration_results.md) |
| `4` Pages + curation | 07, 08 | UC Pages; `docs/pages/pages_registration.md`; `ontology-genie-agents/agents/*.geniespace.json`, `resources/genie_agents.yml`, `docs/domain_manifest.yml` | `validate_space` 0 errors, tokenized agent files | [pages registration](../examples/tpch/docs/pages/pages_registration.md), [domain manifest](../examples/tpch/docs/domain_manifest.yml) |
| `5` Agent deployment | 09 | deployed Genie Agents; deployment results with probe answers | `agent_probe` | [agent validation](../examples/tpch/docs/deployment/agent_validation.md) |
| `6` Tuning | 10 | `docs/tuning/benchmark_questions.yml`, `benchmark_results.md`, `tuning_plan.md`; re-registered views if changed | `benchmark_results` (>= 70% accuracy) | [benchmark results](../examples/tpch/docs/tuning/benchmark_results.md), [tuning plan](../examples/tpch/docs/tuning/tuning_plan.md) |

Build-0 TPC-H results: 23 glossary terms, 8 table profiles with 10 verified joins, 7 metric views registered with smoke and cardinality pass, 1 Genie Agent with 3/3 probes, baseline benchmark 93.3% on 15 questions. UC Pages were not written (no Discover domain; dry run only).

## 6. Promote

Only `catalog`, `warehouse_id` and the deployment target change between environments. Add a target to each bundle, write its overrides file, and deploy with `--target <env>`. Users other than the owner need `USE CATALOG`, `USE SCHEMA` and `SELECT` on the metric views to use an agent.

## Appendix: manual setup

Without the notebooks, the same steps by hand:

1. **SDK bundle overrides**: `<sdk>/.databricks/bundle/<target>/variable-overrides.json` with `sdk_catalog`, `sdk_schema`, `warehouse_id` and (prod targets) `sdk_consumer_group`; then the deploy steps in step 0.
2. **Scaffold**: `gos-scaffold` as in step 2 (add `--vendor` for the vendored copy).
3. **Project overrides**: write the two files in step 3 by hand. Keep `catalog` identical and set the agents `schema` to the resolved metric-view schema; after registration, confirm it with `information_schema.tables`.
4. **Vars file**: a JSON file outside the repository with `project_name`, `instance_suffix`, `build_root` (project root), `build_branch`, `manifest_path` (`<build_root>/docs/plans/waves.json`), `skills_catalog`, `skills_schema` ([genie-build-waves README](../../genie-build-waves/README.md)).
5. Validate both bundles, commit on the feature branch, deploy the genie-build-waves instance, run setup and start the build (step 4).
