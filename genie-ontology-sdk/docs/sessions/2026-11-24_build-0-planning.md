# 2026-11-24 — Build-0 Planning

## Goal
Create a fresh build-0 genie-build-waves plan set, using the initial design (L100, L200-A..H) and the original L300 plans as the guide.

## Decisions (owner, in conversation)
| Topic | Decision |
|---|---|
| Scope | Build the reusable SDK first, then dogfood it in the final waves on a sample domain |
| Original plans | Move `docs/plans/01-10`, `INDEX.md`, `waves.json` to `docs/design/l300-pipeline/` as reference |
| Dogfood data | `samples.tpch` (readable in this workspace: `orders` 7,500,000 rows, `lineitem` 29,999,795 rows), registered into a dev schema |
| Branch | Continue on `mg-genie-ontology-modeled-knowledge-sdk` |

Defaults I chose (recorded in PROJECT_MEMORY "Build-0 open decisions"):
* `allow_deploy` + `required_checks` instead of `converge` + `runtime_targets`, because the latter need dev-prefixed names or ids in a committed mbp file.
* The tuning gate does not fail below 70% accuracy.
* The UC Pages session may stop `blocked`.
* No external monitor.

## Problems and root causes
* **Original manifest unusable** (from the design review): wave id `5.5` was invalid; waves 1-3 were serial; plan 01 ran Git; `owned_paths` and `allow_deploy` were missing. Root cause: written before checking the genie-build-waves schema. Fixed in the new manifest (and planned for the run kit, session 08).
* **Dev values vs mbp genericity:** runtime ids, catalogs and dev-prefixed names must not be committed. The fix is gitignored `.databricks/bundle/dev/variable-overrides.json` per dogfood bundle (documented Declarative Automation Bundles mechanism, precedence after `--var` and `BUNDLE_VAR_*`), plus tokenized `.geniespace.json` files with a render step (session 03/07).
* **Git working tree glitch:** after `git mv` moved `docs/plans/INDEX.md` and `waves.json`, new files created at the same paths through the workspace API existed as workspace objects (ids `975815647682162`, `975815647682165`) but were invisible in the Git folder's working tree (`git status` showed ` D`, `ls` showed nothing, for several minutes and after re-upload). Workaround: wrote the identical bytes (sha256 match) to the working-tree paths; the object ids stayed the same. A side effect: an accidental partial commit `3228980` (local) holds the 10 plan moves plus the copies of INDEX/waves in `l300-pipeline/`. The final commit completes the move.

## Changes
* `docs/design/l300-pipeline/`: the 12 original files moved there + `README.md` (reference-only note, list of known issues).
* Hygiene: L100 (Declarative Automation Bundles wording, customer proof point genericized, cross-references relinked or marked external, build status pointer), `docs/research/genie-agent-api-deployment.md` wording, README line 5 + removed the missing Genie Artifact row.
* `docs/plans/waves.json` (build-0 manifest), `docs/plans/INDEX.md` (wave map, shared files, cross-session contracts, dependency graph), and 19 plans in `docs/plans/build-0/`.
* `.gitignore` (`.build-status/`, `.databricks/`, `**/.rendered/`, Python caches).
* `PROJECT_MEMORY.md` (status, layout, finding resolutions, prerequisite, next steps, open decisions), README build-plans table, this summary + sessions INDEX.

## Build-0 shape
| Wave | Sessions | Notes |
|---|---|---|
| 0-0 | 01 | package, input contract, pytest |
| 0-1 | 02, 03, 04, 05a, 05b | libs + 6 skills, parallel |
| 0-2 | 06, 07, 08 | 2 bundle templates + run kit |
| 0-3 | 09 | init tool + `examples/tpch` scaffold; manual prereq P1 |
| 0-4 | 10a, 10b | TPC-H research / EDA |
| 0-5 | 11 | MV YAMLs |
| 0-6 | 12 | deploy + register (deployer) |
| 0-7 | 13, 14 | UC Pages / agent curation |
| 0-8 | 15 | deploy agent (deployer) |
| 0-9 | 16 | benchmark + tuning (deployer) |
| 0-10 | 17 | docs + observations |

## Verification
* `waves_manifest.validate_manifest` (genie-build-waves `src/notebooks`) on `docs/plans/waves.json`: **0 errors, 0 warnings**. Summary: 11 waves, 19 sessions, 0 runtime targets, continuation passes 1 per wave, **100 job tasks**.
* All 19 `plan_file`s exist. The owned-path prefix-overlap check (self-tested on a known overlap and a known non-overlap) found 0 overlaps in every wave, with at most one `allow_deploy` session per wave (12, 15, 16).
* grep for "Asset Bundles", the customer name, internal program names and the missing artifact path (md/json/yml/html outside `docs/sessions/` and `PROJECT_MEMORY.md`): 0 hits.
* Not verified: the plans' technical assumptions that sessions must check themselves (`genie_spaces` `file_path` interpolation, Pages API availability to job tasks, metric view YAML keys).

## Follow-ups
- [ ] Owner: write both `variable-overrides.json` files (see PROJECT_MEMORY).
- [ ] Deploy a genie-build-waves instance for this project (`deploy_instance.py`, own `instance_suffix`), run setup + smoke, start build-0.
- [ ] Open the PR for `mg-genie-ontology-modeled-knowledge-sdk` when the owner is ready.
