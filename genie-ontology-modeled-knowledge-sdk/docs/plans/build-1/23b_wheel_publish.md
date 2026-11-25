# Session 23b: Publish the SDK Wheel to the UC Volume (R7a)

## Scope
Deploy the SDK bundle (`databricks.yml` at `build_root`) to dev, which builds the 0.1.0 wheel and uploads it to the UC volume, prove it installs with the `sdk_smoke` job, and record the stable wheel path every project bundle pins to. Deploy only the SDK bundle.

## Context
* [REQUESTS R7a](REQUESTS.md#r7a-sdk-wheel-distribution); session 23 wrote the bundle, the smoke job and the template variables.
* Owner prerequisite P1-8 is done: the volume exists (or the owner approved it as a bundle resource; then session 23 declared it and this deploy creates it), grants are in place (`WRITE VOLUME` for the build identity, `READ VOLUME` for project run-as principals and the genie-build-waves run-as user), and `.databricks/bundle/dev/variable-overrides.json` at `build_root` has `sdk_volume_path`. Never print or commit that value; in committed files write `<sdk_volume_path>`.
* Authorized: `bundle.deploy` of the SDK bundle (target dev), `jobs.run_now` of its `sdk_smoke` job, `volume.write` to a `releases/` folder in that volume. No grants (owner-only).
* Open questions this session answers (R7a "not yet verified"): the sub-path the CLI uploads to under `artifact_path`; whether that path is stable across deploys of the same version; whether the version string is changed by dynamic versioning.

## Tasks
1. `databricks -v`; `bundle validate --strict -t dev`; `bundle deploy -t dev` (max 3 attempts; fixes only in `databricks.yml`, `resources/**`, `notebooks/sdk_smoke.ipynb`).
2. List the volume (`databricks fs ls dbfs:<sdk_volume_path>` recursively, or the Files API): find the uploaded wheel(s). Exactly one file named `genie_ontology_modeled_knowledge_sdk-0.1.0-py3-none-any.whl` must exist for this version; a second deploy must not add another (deploy again and list).
3. If the upload path contains a hash, timestamp or other per-deploy segment, copy the wheel to `<sdk_volume_path>/releases/0.1.0/genie_ontology_modeled_knowledge_sdk-0.1.0-py3-none-any.whl` and use that as the stable path; otherwise the CLI path is the stable path. Either way the template variable `sdk_wheel_subpath` must match; if it does not, record a request for session 28 (run kit) and session 30 (TPC-H overrides) with the right value, and set it in your summary.
4. `bundle run sdk_smoke -t dev`: SUCCESS and output `0.1.0`.
5. `docs/distribution/wheel_publish.md`: CLI version, upload sub-path pattern, stable path pattern (placeholders), whether the copy was needed, how a new version is published (bump `pyproject.toml`, `CHANGELOG.md`, deploy, smoke), and how a project pins it (`sdk_version`).

## Acceptance Criteria
- [ ] Gate checks `wheel_published` and `sdk_smoke` pass; `validate_bundles` for `.` passes.
- [ ] No volume, catalog or schema name in committed files.

## Owned Paths / Assets
- `databricks.yml`, `resources/**`, `notebooks/sdk_smoke.ipynb`, `docs/distribution/**`
- Dev deployment of the SDK bundle, its `sdk_smoke` job, the `releases/` folder in the SDK volume.

## Dependencies
- Session 23; owner prerequisite P1-8.
