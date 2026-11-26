# Publishing the SDK wheel

Verified by build-1 session 23b (wave 1-2b) with **Databricks CLI v1.27.0** (`databricks version`) on target `dev`. Committed files never name the real catalog, schema or volume; this document writes the SDK bundle's `sdk_wheels` volume as `<sdk_volume_path>` (`/Volumes/<sdk_catalog>/<sdk_schema>/sdk_wheels`; read the resolved value from `databricks bundle summary -t <target>`).

## What the CLI does on deploy

`databricks bundle deploy -t <target>` at the SDK root:

1. builds the wheel with `artifacts.sdk_wheel.build` (`python -m pip wheel --no-deps --no-build-isolation -w dist .`) into the gitignored `dist/`,
2. uploads every wheel the bundle references (`resources/sdk_smoke.job.yml` depends on `../dist/*.whl`) to `workspace.artifact_path` (`${resources.volumes.sdk_wheels.volume_path}`),
3. rewrites the job dependency to the uploaded volume path.

## Upload sub-path (checked)

| Question | Answer |
|---|---|
| Sub-path under `artifact_path` | `.internal/` (no hash, timestamp or deploy id). The volume root holds only `.internal/`. |
| Uploaded file | `<sdk_volume_path>/.internal/genie_ontology_modeled_knowledge_sdk-<version>-py3-none-any.whl` |
| Stable across deploys of the same version | Yes. A second `bundle deploy` re-uploaded the same file name in place (same size, newer modification time); the folder still held exactly one wheel. |
| Version changed by dynamic versioning | No. The file name carries the static `pyproject.toml` version (`0.1.0`); the installed package reports `__version__` `0.1.0`. |
| Deployed job dependency | `<sdk_volume_path>/.internal/genie_ontology_modeled_knowledge_sdk-0.1.0-py3-none-any.whl` (from `jobs get`) |

**Copy to `releases/<version>/` was not needed.** The CLI upload path is stable, so it is the stable path:

```
<sdk_volume_path>/.internal/genie_ontology_modeled_knowledge_sdk-<sdk_version>-py3-none-any.whl
```

The metric-views template already defaults `sdk_wheel_subpath` to `.internal`, so `sdk_wheel` composes to this path with no override.

Caveats:

* Redeploying the **same** version overwrites the wheel in place. Bump the version for any change consumers should see; never change code under a published version.
* `.internal/` is a CLI-managed folder. If a later CLI version changes the upload sub-path, re-check with the listing below and either update `sdk_wheel_subpath` or publish a copy under `releases/<version>/` and point `sdk_wheel_subpath` at `releases/<version>`.

## Smoke test

`databricks bundle run sdk_smoke -t <target>` runs the serverless `sdk_smoke` job, which installs the wheel from the volume through the job environment and exits with `{"__version__": "<version>", "file": "<site-packages path>"}`. In session 23b it ended `TERMINATED SUCCESS` with `__version__` `0.1.0` and `__init__.py` under the job environment's `site-packages`.

## Check the volume

```bash
databricks bundle summary -t dev                       # volume_path of resources.volumes.sdk_wheels
databricks fs ls dbfs:<sdk_volume_path> -l             # expect only .internal
databricks fs ls dbfs:<sdk_volume_path>/.internal -l   # one wheel per published version
```

## Publishing a new version

1. Bump `[project] version` in `pyproject.toml` (the single source; `__version__` reads it).
2. Add the release to `CHANGELOG.md`.
3. `databricks bundle validate --strict -t <target>` and `databricks bundle deploy -t <target>` at the SDK root.
4. `databricks bundle run sdk_smoke -t <target>`: must end SUCCESS and print the new `__version__`.
5. List `<sdk_volume_path>/.internal/`. Earlier versions are not removed by this check; confirm the new wheel is present.

## Pinning the SDK in a project

A project bundle (from `templates/ontology-metric-views`) installs the wheel through its job environment (`dependencies: [${var.sdk_wheel}]`). Set in the project's gitignored `.databricks/bundle/<target>/variable-overrides.json`:

| Variable | Value |
|---|---|
| `sdk_volume_path` | `<sdk_volume_path>` (required, no default) |
| `sdk_version` | the SDK version to pin, e.g. `0.1.0` (rendered by the scaffold) |
| `sdk_wheel_subpath` | `.internal` (template default; change only if the upload path changes) |

Consumers need `USE_CATALOG` on `<sdk_catalog>`, `USE_SCHEMA` on the SDK schema and `READ_VOLUME` on `sdk_wheels` (see [README.md](README.md#grants)).
