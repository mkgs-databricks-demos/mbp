# Vendored Genie Ontology Modeled Knowledge SDK library

The template ships only this README. When a run project is scaffolded, `genie_ontology_modeled_knowledge_sdk.scaffold.scaffold_project` copies the SDK modules the notebooks need into this folder, verbatim:

* `mv_yaml.py` - load, substitute, validate (MV001-MV007), `render_ddl`
* `manifest.py` - `build_manifest`, `validate_manifest_json`
* `geniespace.py`

The copies are not edited: they still import each other as `genie_ontology_modeled_knowledge_sdk.*`. Each notebook's `load_sdk(bundle_root)` cell registers this folder as the `genie_ontology_modeled_knowledge_sdk` package before importing, so no `pip install` of the SDK is needed on serverless. If the folder has no `mv_yaml.py`, the notebooks fall back to an installed `genie_ontology_modeled_knowledge_sdk` and fail with a clear `ImportError` if there is none.

To refresh the copies after an SDK upgrade, re-run the scaffold for the project (or copy the three files from the SDK's `src/genie_ontology_modeled_knowledge_sdk/`).

`bundle validate` does not need these files.
