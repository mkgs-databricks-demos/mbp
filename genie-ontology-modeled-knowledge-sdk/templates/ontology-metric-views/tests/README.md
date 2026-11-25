# Tests

The bundle's runtime tests are job tasks, not files in this folder:

| Task | Notebook | Fails when |
|---|---|---|
| `smoke_test` | `notebooks/smoke_test.ipynb` | a registered metric view does not resolve, or `SELECT MEASURE(...) ... LIMIT 1` over its measures errors |
| `cardinality_test` | `notebooks/cardinality_test.ipynb` | adding a join to the fact grain (`source`) increases `COUNT(*)` (the join fans out and would inflate measures) |

Both run after `register_each_mv` in the `register_metric_views` job and report a JSON summary (task value `summary` and the notebook exit value).

Static checks run before deploy:

* `python -m genie_ontology_modeled_knowledge_sdk.mv_yaml validate metric_views` (rules MV001-MV007; `generate_manifest` runs the same validation and fails on errors)
* `databricks bundle validate --strict --target <target>`

The SDK repository tests this template's structure in `tests/test_template_mv_bundle.py`.

Put project-specific SQL or pytest checks here if you need them; nothing in the bundle reads this folder.
