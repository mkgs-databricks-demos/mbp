# Build-0 close-out (Genie Code session)

Date: 2026-11-25 | Branch: `mg-genie-ontology-modeled-knowledge-sdk`

The interactive Genie Code session that took build-0 from `BUILD_PASSED` to a mergeable PR.

## Problems
1. Devin's read-only review of the build-0 result (`cfbb4d0`) found 1 medium and 4 low findings.
2. Devin found two framework gaps that no genie-build-waves backlog item covered.
3. The owner wanted the project renamed before merge.

## Changes
* **Review fixes** (`71e9711`):
  * `docs/usage.md` and `README.md`: the Pages wave gate fails until a Discover domain exists or the owner defers.
  * `pages._first_sentence` skips abbreviations and lower-case continuations (+8 tests).
  * "0-0..0-10" status lines.
  * `examples/tpch/README.md`: one row per docs folder.
  * PROJECT_MEMORY genie-build-waves link.
* **mbp root README** (`5c62bf0`): the project row was outside the folder table.
* **genie-build-waves backlog** (separate branch `mg-genie-build-waves-backlog-verdict-repair-guide`):
  * item 12: no build-level verdict across runs
  * item 13: the repair guide still says a `w<w>_sessions` repair reruns a failed session
* **Rename** (`0a4edb8`): see [2026-11-25_rename-to-modeled-knowledge-sdk.md](2026-11-25_rename-to-modeled-knowledge-sdk.md).
* **Wrap-up:** [2026-11-25_build-0-wrap-up.md](2026-11-25_build-0-wrap-up.md) (build-level verdict and open items); PROJECT_MEMORY and README brought up to date.
* PR title and description drafted for the owner.

## Decisions (owner)
* Rename everything, including the Python package, with no alias; history files keep the old names.
* Leave the genie-build-waves instance on the old folder until build 1.
* Keep the "Genie Code Start Session - DO NOT EDIT" notebook in the project and the repo; moved from the pre-rename folder into the project root.
* Item 13 stays a backlog item instead of a direct edit to the repair guide.

## Verification
* pytest from a `/tmp` copy: 280 passed; vendored copies identical to `src/`.
* No old project name outside the history files (grep); relative links in the README, usage guide, PROJECT_MEMORY and the indexes resolve.
* The branch merges into `main` cleanly (`git merge-tree`).

## Files modified
* review fixes: `src/.../pages.py`, `tests/test_pages.py`, `docs/usage.md`, `README.md`, `PROJECT_MEMORY.md`, `docs/design/L100-*.md`, `examples/tpch/README.md`
* rename: every tracked file (see the rename summary)
* this summary, `2026-11-25_build-0-wrap-up.md`, `INDEX.md`, `PROJECT_MEMORY.md`, `README.md`
