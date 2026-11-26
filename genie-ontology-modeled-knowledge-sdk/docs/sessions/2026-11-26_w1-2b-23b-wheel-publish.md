# 2026-11-26 - Wave 1-2b, session 23b: publish the SDK wheel to the UC volume (R7a)

Run `288268071022101`, branch `mg-genie-ontology-build-1-plan` at `1e807bf` (checked read-only through the repos API), mode `edit` with `allow_deploy` / `allow_execute`, continuation 0. No Git writes. Status: **pass**.

## What was done

1. `databricks version`: **v1.27.0**. `bundle validate --strict -t dev` at build_root: OK.
2. `bundle deploy -t dev` (attempt 1): built `genie_ontology_modeled_knowledge_sdk-0.1.0-py3-none-any.whl`, uploaded it, created `jobs.sdk_smoke` (job id `359803391912441`, `[dev <user>] sdk_smoke`); schema and volume unchanged. Bundle deployment id `193178364631306`.
3. Volume listing (`fs ls`): the volume root holds only `.internal/`; `.internal/` holds exactly one file, the 0.1.0 wheel (72348 bytes).
4. Second `bundle deploy -t dev`: 0 created / 0 changed; the same file name was re-uploaded in place (same size, newer mtime). Still exactly one wheel.
5. `jobs get` on the deployed job: the environment dependency was rewritten to `<sdk_volume_path>/.internal/genie_ontology_modeled_knowledge_sdk-0.1.0-py3-none-any.whl`.
6. `bundle run sdk_smoke -t dev`: run `419305866754660`, `TERMINATED SUCCESS`, output `{"__version__": "0.1.0", "file": ".../site-packages/genie_ontology_modeled_knowledge_sdk/__init__.py"}`.
7. Docs: new `docs/distribution/wheel_publish.md`; `docs/distribution/README.md` volume-contract bullet updated from "to be confirmed" to confirmed.

## Decisions

* **Stable path = CLI upload path.** `<sdk_volume_path>/.internal/genie_ontology_modeled_knowledge_sdk-<version>-py3-none-any.whl` has no hash, timestamp or deploy segment and is stable across deploys, so the `releases/<version>/` copy was **not** made (no `volume.write` used).
* `sdk_wheel_subpath` default `.internal` in `templates/ontology-metric-views/databricks.yml` already matches. **No request needed** for sessions 28 or 30.
* No dynamic versioning: the static `pyproject.toml` version 0.1.0 is in the file name and `__version__`.
* Recorded caveat: redeploying the same version overwrites the wheel in place; bump the version for any change.

## Checks

| Check | Result |
|---|---|
| `bundle validate --strict -t dev` (SDK bundle, before deploy and again at end) | pass |
| `bundle deploy -t dev` x2 | pass |
| wheel_published: exactly one 0.1.0 wheel at `<sdk_volume_path>/.internal/`, unchanged count after second deploy | pass |
| sdk_smoke: run started after this build run started, SUCCESS, `__version__` 0.1.0 | pass |
| No catalog/schema/volume names in `docs/distribution/**` (grep for real names and `/Volumes/<x>/<y>/sdk_wheels`) | pass |

## Files modified

* `docs/distribution/wheel_publish.md` (new)
* `docs/distribution/README.md`

No YAML or notebook changes. Assets: SDK bundle dev deployment (created `sdk_smoke` job), wheel in the `sdk_wheels` volume `.internal/` folder.

## Requests

None.
