# SDK skills in Unity Catalog (build-1 R1)

The six `skills/ontology-*` folders are published to the Unity Gateway skills library as `<skills_catalog>.<skills_schema>.<skill_id>`. The skills schema is the **SDK schema** (the SDK bundle's `resources.schemas.sdk`; read it with `databricks bundle summary -t <target>`). Ids are snake_case; each `SKILL.md` keeps its kebab-case `name`.

| Folder | Skill id |
|---|---|
| `skills/ontology-domain-research` | `ontology_domain_research` |
| `skills/ontology-context-extraction` | `ontology_context_extraction` |
| `skills/ontology-deep-eda` | `ontology_deep_eda` |
| `skills/ontology-mv-synthesis` | `ontology_mv_synthesis` |
| `skills/ontology-agent-curation` | `ontology_agent_curation` |
| `skills/ontology-tuning` | `ontology_tuning` |

## Files

| File | Purpose |
|---|---|
| `ci/skills.yaml` | Mapping folder -> `${SKILLS_CATALOG}.${SKILLS_SCHEMA}.<id>`. Staged; the owner moves it to `<repo root>/skills.yaml` |
| `ci/github/workflows/publish-genie-ontology-skills.yml` | GitHub publishing (Unity Gateway `publish-skills` action, `production` environment, OIDC, path filter, `workflow_dispatch` dry run). Staged; moves to `<repo root>/.github/workflows/`. **Owner:** pin the action to a reviewed SHA (`TODO(owner)` in the file) and check its input names |
| `src/genie_ontology_modeled_knowledge_sdk/skills_publish.py` | `load_mapping`, `skill_limit_errors`, `check_schema`, `plan_publish`, `publish`, `list_published`; CLI `python -m genie_ontology_modeled_knowledge_sdk.skills_publish --mapping ... --skills-dir ... --catalog ... --schema ... [--dry-run|--check-only]` |
| `notebooks/publish_skills.ipynb` | Workspace publishing without GitHub. Widgets `skills_catalog`, `skills_schema`, `sdk_version`, `dry_run` (default `true`); installs the SDK wheel from `<sdk_volume_path>/.internal/` |
| `tests/test_skills.py`, `tests/test_skills_publish.py` | Skill hygiene limits; fake-client publish (second run is a no-op) |

## Publishing flow

Per skill: `ai_gateway.get_skill("skills/<fqn>")`, `create_skill(parent="schemas/<catalog>.<schema>", skill_id=...)` if missing, `files.upload` of **changed** files only under `/Skills/<catalog>/<schema>/<id>/`, then `finalize_skill`. A skill whose files all match the published version is not uploaded or finalized, so a rerun reports 0 changes. Files present only in the published version are reported as `stale` and left in place. The schema must exist; `check_schema` reports and creates only with `create_schema=True`. Needs `databricks-sdk` with the `ai_gateway` skills API (0.171.0 verified; the serverless default image lacked it, so the notebook upgrades the SDK).

## Grants (not applied by the SDK; owner action)

* Publisher: `USE CATALOG`, `USE SCHEMA`, `CREATE VOLUME` on the skills schema; plus `READ VOLUME`, `WRITE VOLUME` to update existing skills.
* Consumers: `USE CATALOG`, `USE SCHEMA`, and `READ VOLUME` on each skill (least privilege) rather than the whole schema.

## Loading skills in sessions, and the workspace-folder fallback

* A Genie Code session's skill list is fixed when it starts. A Unity Catalog skill published **before** a session (or job task) starts appears in its list; one published during the session does not (R1 spike, build-1 session 27).
* How a session can tell: the skill id `<catalog>.<schema>.<id>` appears in its skill registry, and `readSkillFile("skills/<catalog>.<schema>.<id>/SKILL.md")` succeeds.
* **Fallback:** if the id is not in the list (preview off, no `READ VOLUME`, or published after start), read the workspace copy `<sdk checkout>/skills/<folder>/SKILL.md` (and its `references/`) with the file tools and follow it. The content is identical to the published version after a publish run. Session summaries from wave 1-4 on say which source they used.
* Scaffolded projects record the location in `sdk_config.json` (`skills: {catalog, schema, ids}`) and in a `## SDK skills` section of `PROJECT_MEMORY.md`.
