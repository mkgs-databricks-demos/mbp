# Session 17: Build-0 Documentation & Observations

## Scope
Bring the SDK docs in line with what build-0 actually produced:
* README: layout, quickstart via `notebooks/init_ontology_project`, links to `templates/`, `skills/`, `examples/tpch/`
* `docs/usage.md`: end-to-end run guide
* `PROJECT_MEMORY.md`: status, layout, observations
* L100 "Build status" note
* `docs/build-0-observations.md`: consolidated skill gaps and template fixes for build 1

## Context
* Read every build-0 session summary in `docs/sessions/` (sessions 01-16) and collect their "Skill gaps" and "Template fixes for build 1" sections.
* mbp rule: no workspace-specific identifiers outside `docs/sessions/`. Docs may point to session summaries for real ids.
* Terminology: Declarative Automation Bundles, Lakeflow Jobs, Genie Agents.

## Tasks
1. `README.md`:
   * sections: Quickstart, Layout, Library, Skills, Templates, Run kit, TPC-H example, Plans, Sessions
   * the plans table points to `docs/plans/INDEX.md` (build-0) and `docs/design/l300-pipeline/`
2. `docs/usage.md`:
   * prerequisites
   * init notebook
   * overrides files
   * deploying genie-build-waves for a run with the run kit
   * expected outputs per wave
3. `docs/build-0-observations.md`: a table of source session, observation, type (skill gap / template fix / platform limit), proposed build-1 change.
4. `PROJECT_MEMORY.md`:
   * status = build-0 complete (or which waves passed)
   * close resolved review findings
   * link observations
5. L100: replace the "Build status" sentence with the current state.

## Acceptance Criteria
- [ ] Every relative link in `README.md` and `docs/usage.md` resolves to an existing file (a script check, listed in the summary).
- [ ] `docs/build-0-observations.md` has one row per gap/fix reported in sessions 10a-16 (count matches).
- [ ] `grep` for user paths / workspace hosts / resolved dev schema names in the owned files returns nothing.

## Owned Paths / Assets
- `README.md`, `PROJECT_MEMORY.md`, `docs/usage.md`, `docs/build-0-observations.md`, `docs/design/L100-genie-ontology-sdk.md`

## Dependencies
- All earlier build-0 sessions (reads their summaries).
