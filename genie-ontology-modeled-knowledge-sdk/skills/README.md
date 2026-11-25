# Genie Ontology Modeled Knowledge SDK Skills

Six skills, one per stage of a Genie Ontology run. They hold only SDK-specific rules (registration tokens, the forEach manifest, `# verified:` joins, subdomain comments, MV-first tuning) and point to platform skills for general syntax. Each `SKILL.md` description names its SDK stage so it loads for Genie Ontology Modeled Knowledge SDK work, not for general requests.

## Skills

| Skill (folder = `name`) | SDK stage | Platform skills it relies on | Unity Catalog skill id (planned) |
|---|---|---|---|
| [`ontology-domain-research`](ontology-domain-research/SKILL.md) | wave 1: domain research, glossary term files | `discover-pages` (term files only; the SDK UC Pages stage publishes with `pages.upsert_pages`; term writes go through `pages.write_terms`); web search | `ontology_domain_research` |
| [`ontology-context-extraction`](ontology-context-extraction/SKILL.md) | wave 2: supplemental business context from UC volumes | `sql-functions` (`ai_parse_document` syntax and options); `bi-migration` (Power BI / Tableau file formats; extraction only, no migration); `writing-sql` (`read_files` / VARIANT) | `ontology_context_extraction` |
| [`ontology-deep-eda`](ontology-deep-eda/SKILL.md) | wave 3: table profiles, verified join cardinality | `data-sampling` (query hygiene, bounded results); `databricks-sql` (system table lineage and query history); `data-quality-rca` not used (lineage is a count only) | `ontology_deep_eda` |
| [`ontology-mv-synthesis`](ontology-mv-synthesis/SKILL.md) | wave 4: parameterized metric view YAML + `manifest.json` | `metric-views` (and its `joins-correctness.md`, `level-of-detail.md`, `materialization.md`, `semantic-metadata.md`) | `ontology_mv_synthesis` |
| [`ontology-agent-curation`](ontology-agent-curation/SKILL.md) | wave 6: Genie Agent configs (`.geniespace.json`, `domain_manifest.yml`) | `metric-views` (metric view semantics); SDK `geniespace` for the space file | `ontology_agent_curation` |
| [`ontology-tuning`](ontology-tuning/SKILL.md) | wave 8: exhaustive benchmark, MV-first tuning to the asymptote, report simulation method | `metric-views` (YAML syntax for fixes); Declarative Automation Bundles for redeploys; SDK `benchmark` for all thresholds | `ontology_tuning` |

The Unity Catalog ids follow the snake_case convention and are filled in by the skills publishing session (build-1 session 27, `ci/skills.yaml`); `SKILL.md` keeps its kebab-case `name`. The platform-skill column is taken from each skill's own `Platform skills and precedence` section (or its precedence paragraph); the skill files are authoritative, so update this column when a skill names a different platform skill.

## Precedence when both load

* **SDK skill for SDK rules:** what to build, file layout, tokens (`${target_catalog}.${target_schema}`), the manifest contract, verified joins, MV-first ordering, protocol thresholds (from the `benchmark` constants) and unattended-session rules.
* **Platform skill for syntax:** metric view YAML keys and semantics, SQL dialect, Discover/UC Page API shapes, bundle commands.
* When they conflict on syntax, the platform skill wins and the SDK skill should be fixed. When they conflict on an SDK rule (for example, the platform suggests an agent instruction where the SDK requires a metric view fix first), the SDK skill wins.

## Order in a run

`ontology-domain-research` and `ontology-context-extraction` and `ontology-deep-eda` (discovery, can run in parallel) -> `ontology-mv-synthesis` -> registration (bundle job, no skill) -> UC Pages -> `ontology-agent-curation` -> deployment -> `ontology-tuning`. The tuning protocol rationale is in [docs/design/tuning-protocol.md](../docs/design/tuning-protocol.md).
