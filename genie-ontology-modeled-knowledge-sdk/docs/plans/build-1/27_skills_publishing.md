# Session 27: Publish SDK Skills to the Unity Gateway Skills Library (R1)

## Scope
A mapping file, a staged GitHub publishing workflow, an idempotent workspace publisher (module + notebook), the `sdk_config` skills key, the scaffold recording the skills location, the skill hygiene test, and a live publish of the six reconciled skills (twice).

## Context
* [REQUESTS R1](REQUESTS.md#r1-publish-the-sdk-skills-to-the-unity-gateway-skills-library). Ids follow the Unity Catalog snake_case convention (`ontology_mv_synthesis`); `SKILL.md` keeps its `name`.
* Target schema: `skills_catalog`.`skills_schema` from `.local/build-1.json` (owner-created with grants, P1-3). You are authorized for `uc_skills.publish` on the six SDK skills there; no grants (owner-only).
* Publishing flow: create the skill if missing -> upload every file through the Files API under `/Skills/<catalog>/<schema>/<skill>/` -> finalize; the same flow genie-build-waves setup uses for its skills (read `genie-build-waves/src/notebooks/setup_build_waves_job` for the calls). Update an existing skill instead of creating a duplicate.
* Root files are staged under `ci/` ([INDEX](INDEX.md#repository-root-files)).

## Tasks
1. `ci/skills.yaml`: `genie-ontology-modeled-knowledge-sdk/skills/<folder>` -> `<catalog>.<skills_schema>.<skill_id>` with catalog and schema as placeholders (`${SKILLS_CATALOG}`, `${SKILLS_SCHEMA}`).
2. `ci/github/workflows/publish-genie-ontology-skills.yml`: `databricks/unity-gateway/actions/publish-skills` pinned to a commit SHA (leave a `# TODO(owner): pin reviewed SHA` if it cannot be verified), `production` environment, GitHub OIDC, path filter (skills, mapping, workflow), `workflow_dispatch` dry run.
3. `skills_publish.py`: `plan_publish(skills_dir, mapping)` (diff of files vs. the published version), `publish(ws, ...)` (idempotent; returns changed files per skill), `check_schema(ws, catalog, schema)` (report, never create unless `create_schema=True`).
4. `notebooks/publish_skills.ipynb`: widgets `skills_catalog`, `skills_schema` (empty defaults), `dry_run`; install the SDK wheel; calls the module.
5. `schemas/sdk_config.schema.json` + `config.py`: optional `skills: {catalog, schema, ids}`; `scaffold.py` writes it into the project's `sdk_config.json` and `PROJECT_MEMORY.md`.
6. `tests/test_skills.py`: each skill folder within platform limits (text files only, at most three folder levels and 50 files or folders), front matter `name` and `description`; `tests/test_skills_publish.py`: fake client, second publish is a no-op.
7. Live: publish twice with the module; list the schema's skills; write `docs/skills/publish_results.md` (ids, file counts, second run 0 changes; catalog/schema shown as placeholders).
8. R1 spike: record in your summary whether this unattended job task sees the published Unity Catalog skills in its skill list, and how later sessions can tell; document the workspace-folder fallback in `docs/skills/README.md`.

## Acceptance Criteria
- [ ] Gate checks `pytest` and `skills_published` pass.
- [ ] Spike outcome recorded; fallback documented.
- [ ] No grants or schema creation performed.

## Owned Paths / Assets
- `ci/skills.yaml`, `ci/github/workflows/publish-genie-ontology-skills.yml`, `notebooks/publish_skills.ipynb`
- `src/genie_ontology_modeled_knowledge_sdk/{skills_publish,config,scaffold}.py`, `src/genie_ontology_modeled_knowledge_sdk/schemas/**`
- `tests/test_skills.py`, `tests/test_skills_publish.py`, `docs/skills/**`
- The six SDK skills in the skills schema.

## Dependencies
- Sessions 23 (wheel), 24, 25, 26 (reconciled skills).
