# 2026-11-24 — Wave 0-2 / Session 07: Genie Agent Bundle Template (DAB 2)

* Build run: job `419885870201924`, run `701596191246320`, task `w0-2_session`, continuation 0
* Mode: `edit` (`allow_execute: true`), workflow `hybrid`, branch `mg-genie-ontology-modeled-knowledge-sdk` (verified read-only with `git rev-parse`)
* Status: **pass**. No deploy.

## Interpolation experiment (task 1)

Scratch bundle under the gitignored `templates/ontology-genie-agents/.databricks/interp-exp/` (runDatabricksCli needs a `/Workspace` working directory, so `/tmp` was not usable; the folder was moved to Trash afterwards). Space file identifier `${var.catalog}.${var.schema}.mv_exp`; `bundle validate --output json` (Databricks CLI v1.27.0) showed `serialized_space` with the literal `${var.catalog}.${var.schema}` text.

**Result: `file_path` JSON is not interpolated.** Chosen approach: committed agent files stay tokenized (`${target_catalog}.${target_schema}`, session 03 contract) and are rendered into gitignored `.rendered/` with `python -m genie_ontology_sdk.geniespace render agents .rendered --params .databricks/bundle/<target>/variable-overrides.json`. Recorded in the template README.

## Changes

| File | What |
|---|---|
| `templates/ontology-genie-agents/databricks.yml` | `engine: direct`, `include: resources/*.yml`, variables `warehouse_id`, `catalog`, `schema`, `consumer_group` (default `account users`), `curator_group` (required), `genie_parent_path`; targets `dev` (development, default, `genie_parent_path: ${workspace.root_path}/genie`) and `prd` (production, parent path from overrides). No hosts, no user names |
| `templates/ontology-genie-agents/resources/genie_agents.yml` | `genie_spaces.ontology_agent`: title, description, `warehouse_id`, `parent_path`, `file_path: ../.rendered/ontology_agent.geniespace.json`, CAN_RUN consumer / CAN_EDIT curator |
| `templates/ontology-genie-agents/agents/ontology_agent.geniespace.json` | Minimal v2 space built with `geniespace.build_space` over placeholder `${target_catalog}.${target_schema}.mv_placeholder`; `validate_space` -> no errors |
| `templates/ontology-genie-agents/README.md` | Experiment result + CLI version, variables, overrides file, render step, validate/deploy, adding agents, `.geniespace.json` workspace-editor caveat |
| `templates/ontology-genie-agents/.gitignore` | `.databricks/`, `.rendered/` |
| `tests/test_template_agent_bundle.py` | 11 tests: YAML parses, `engine: direct`, targets, variables/defaults, no hosts/user names/e-mails, resource shape + permissions, every `file_path` pre-render source exists, one resource per agent file, agent files tokenized + valid + render, `.gitignore`, README records result |

Left in place for the gate (gitignored, not committed): `.databricks/bundle/dev/variable-overrides.json` with placeholder values (`0000000000000000`, `placeholder_catalog`, `placeholder_schema`, `placeholder-curators`) and `.rendered/ontology_agent.geniespace.json`.

## Findings and decisions

* `file_path` is resolved **relative to the YAML file that declares it** (`resources/`), not the bundle root: `./.rendered/...` failed with `failed to read serialized genie space from file_path resources/.rendered/...`; fixed to `../.rendered/...`.
* The workspace file API rejects creating `*.geniespace.json` (`Requested node type [UNKNOWN] is not supported`, also hit by session 03). `POST /api/2.0/workspace/import` with `format: RAW` works; the space file was created that way. The SDK render CLI (FUSE write) also works. Session 09 (scaffold copy) should copy these files the same way.
* Dev placeholders: the plan says "Dev target placeholders make validate pass". I did not put placeholder values in the committed `dev` target (a deploy would then create a space over a non-existent catalog and grant a fake group). Validate needs the overrides file and render step anyway, so placeholders live in the scratch `variable-overrides.json` the README documents, matching the wave gate wording.
* In `dev`, the title gets the development prefix (`[dev <user>] Ontology Agent`) and the deploying user gets CAN_MANAGE automatically (seen in validate output).

## Checks

| Check | Result |
|---|---|
| Interpolation experiment recorded in README with CLI version | pass (CLI v1.27.0) |
| Render step (`geniespace render agents .rendered --params ...`) | pass — exit 0, no `${` left |
| `bundle validate --strict --target dev --output json` (runDatabricksCli, `workingDirectory` = template root) | pass |
| pytest from a `/tmp` copy (`python -m pytest -q`) | pass — 221 passed (whole suite at run time); 11 in `test_template_agent_bundle.py` |
| Mutation check (missing file_path source + added `host:`) | the tests fail as expected (3 failed) |
| No deploy | pass — none run |

## Requests

None blocking. For session 09 (init/scaffold): copy `agents/*.geniespace.json` with a raw write (not the workspace file editor), and run the render step before `bundle validate` on `examples/tpch/ontology-genie-agents`.
