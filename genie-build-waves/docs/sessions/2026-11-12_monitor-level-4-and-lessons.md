# 2026-11-12: Monitor level 4 and lessons from the first external-monitor test

## Problem

The first end-to-end test of an external monitor (a coding agent watching a build job) passed at levels 1-3 with no repairs, then the agent made owner-requested changes between builds and reviewed the PR. The owner wants the monitor to act on their behalf (start the build, push small fixes, repair from `w<wave>_sync` without approval), which the skill did not allow. The test also surfaced setup and bundle-planning lessons. Source: an owner request in the test project ("let the build monitor act on the owner's behalf", rows A1-A6) and that project's session history.

## Changes

* `src/skills/genie-build-monitor/SKILL.md`:
  * level 4 "act for the owner" and `max_repairs` input (default 3) (A1);
  * guardrail 3 split by level, level 4: `max_repairs` total and 2 attempts at the same failure (A2);
  * decision table gains a level 4 column: start the first run when told to complete the build, fix the failed session's own files when the cause is quotable (A3), one fresh run after a refused repair (A4);
  * guardrail 9 stop conditions (A5); guardrail 7 read only the build job and `build_root`; guardrail 8 commit prefix, trailer, second commit for SHA references;
  * section 6 covers levels 3-4: `git push --dry-run` first, `--ff-only`, report scope-only validate failures;
  * section 7: report the review when posting fails; new section 8 (level 4 loop and final report).
* `docs/plans/2026-11-03_devin-monitor-requirements.md` (A6): status line, level 4 row (no new grants), CLI profile `scopes = jobs,workspace`, `sql` scope note for lookups, dev deploy folders instead of the shared `/Workspace/.bundle`, run-creator audit-log check, `users` baseline, IP allow list (narrow range, a few minutes to apply), minimum Git token and own Git identity, enforced network policy, driver rules (read messages before re-asking, verify review claims), acceptance check 3 rewritten, check 6 push dry-run, open questions.
* `docs/prompts/repair-failed-wave.md` (A6): "External monitor" section for levels up to 3 and level 4.
* `src/skills/genie-build-planner/SKILL.md`: Genie space users need `USE CATALOG`, `USE SCHEMA`, `SELECT`; tips for shared `root_path` on non-dev targets only (destroy before moving it), cross-bundle dev names from `${workspace.current_user.short_name}`, on-deploy job runs, owner-only destroy/delete steps, repo-root strays.
* `README.md` "External monitor (optional)": levels 1-4, no shared `.bundle` grant, IP list, CLI profile scopes, Git token and push dry-run, "Between builds" pattern.

## Decisions (owner)

* New level 4; levels 1-3 unchanged.
* Level 4 may start the build's first run when told to complete the build, and one fresh run after a refused repair; nothing else.
* Limits: `max_repairs` 3, 2 attempts at the same failure. Unchanged: never setup, deploy, permissions, manifest, `main`, force-push; one writer at a time.

## Verification

* 173 tests pass; `bundle validate --strict --target dev` OK.
* Grep of the edited files' added lines: no internal identifiers.
* Monitor decision table: every row has 5 columns.
* Not yet run: a build at level 4 (next test: the project re-runs setup to republish the skill, then the agent completes a build with one fix and repair from the skill alone).

## Follow-up: monitor skill not published

The project's setup run after `a6b6c35` ended SUCCESS but did not publish the monitor skill: `SKILL.md frontmatter is invalid: Invalid YAML: mapping values are not allowed here ... (level 4: starts the build ...`. The new `description` had an unquoted `: `. Setup uploads the files before the publish step, so the stored file already had the new text, and it skipped the monitor grants ("monitor skill not published"). Fix: `level 4 - starts ...`. New `tests/test_skill_frontmatter.py` parses every `SKILL.md` frontmatter with `yaml.safe_load` (the `a6b6c35` file fails with the same error). 179 pass.

## Files

`src/skills/genie-build-monitor/SKILL.md`, `src/skills/genie-build-planner/SKILL.md`, `docs/plans/2026-11-03_devin-monitor-requirements.md`, `docs/prompts/repair-failed-wave.md`, `README.md`, `tests/test_skill_frontmatter.py`, `docs/sessions/INDEX.md`.
