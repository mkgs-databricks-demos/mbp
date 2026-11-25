# Databricks notebook source
# MAGIC %md
# MAGIC # Register Single Metric View
# MAGIC
# MAGIC Called by the `for_each_task` — one iteration per metric view.
# MAGIC Reads the YAML definition, substitutes environment parameters,
# MAGIC and executes `CREATE OR REPLACE VIEW ... WITH METRICS LANGUAGE YAML`.
# MAGIC
# MAGIC **Parameters (from forEach {{input}}):**
# MAGIC - `yaml_path`: Absolute path to the metric view YAML file
# MAGIC - `mv_name`: Name for the metric view (used in the CREATE statement)
# MAGIC - `source_catalog`: Catalog where source tables live
# MAGIC - `source_schema`: Schema where source tables live
# MAGIC - `target_catalog`: Catalog for metric view registration
# MAGIC - `target_schema`: Schema for metric view registration

# COMMAND ----------

import re

# COMMAND ----------

# Read parameters
dbutils.widgets.text("yaml_path", "")
dbutils.widgets.text("mv_name", "")
dbutils.widgets.text("source_catalog", "")
dbutils.widgets.text("source_schema", "")
dbutils.widgets.text("target_catalog", "")
dbutils.widgets.text("target_schema", "")

yaml_path = dbutils.widgets.get("yaml_path")
mv_name = dbutils.widgets.get("mv_name")
source_catalog = dbutils.widgets.get("source_catalog")
source_schema = dbutils.widgets.get("source_schema")
target_catalog = dbutils.widgets.get("target_catalog")
target_schema = dbutils.widgets.get("target_schema")

print(f"Registering: {target_catalog}.{target_schema}.{mv_name}")
print(f"  YAML: {yaml_path}")
print(f"  Source: {source_catalog}.{source_schema}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Read and parameterize the YAML

# COMMAND ----------

with open(yaml_path, "r") as f:
    yaml_content = f.read()

# Substitute environment parameters
# These are the parameterized references in the YAML source: and joins: blocks
yaml_content = yaml_content.replace("${source_catalog}", source_catalog)
yaml_content = yaml_content.replace("${source_schema}", source_schema)

# Also handle the ${var.*} format if present (from DAB variable references)
yaml_content = yaml_content.replace("${var.source_catalog}", source_catalog)
yaml_content = yaml_content.replace("${var.source_schema}", source_schema)
yaml_content = yaml_content.replace("${var.target_catalog}", target_catalog)
yaml_content = yaml_content.replace("${var.target_schema}", target_schema)

# Strip any YAML comments that start with # at the top of the file
# (these are documentation comments, not part of the metric view definition)
lines = yaml_content.split("\n")
yaml_lines = []
in_header = True
for line in lines:
    if in_header and line.strip().startswith("#"):
        continue  # Skip header comments
    else:
        in_header = False
        yaml_lines.append(line)

yaml_content = "\n".join(yaml_lines)

print("Parameterized YAML (first 500 chars):")
print(yaml_content[:500])

# COMMAND ----------

# MAGIC %md
# MAGIC ## Register the metric view

# COMMAND ----------

# Build the CREATE OR REPLACE VIEW statement
# The $$ delimiters wrap the YAML content
sql = f"""
CREATE OR REPLACE VIEW `{target_catalog}`.`{target_schema}`.`{mv_name}`
WITH METRICS
LANGUAGE YAML
AS
$$
{yaml_content}
$$
"""

print(f"Executing CREATE OR REPLACE VIEW for {mv_name}...")

try:
    spark.sql(sql)
    print(f"✅ Successfully registered: {target_catalog}.{target_schema}.{mv_name}")
except Exception as e:
    print(f"❌ Failed to register {mv_name}: {e}")
    raise

# COMMAND ----------

# MAGIC %md
# MAGIC ## Validate the metric view exists and is queryable

# COMMAND ----------

try:
    # Basic existence check
    result = spark.sql(f"""
        DESCRIBE TABLE `{target_catalog}`.`{target_schema}`.`{mv_name}`
    """)
    col_count = result.count()
    print(f"✅ View exists with {col_count} columns")

    # Quick query test (just check it doesn't error)
    spark.sql(f"""
        SELECT * FROM `{target_catalog}`.`{target_schema}`.`{mv_name}` LIMIT 1
    """)
    print(f"✅ View is queryable")

except Exception as e:
    print(f"⚠️ Validation warning for {mv_name}: {e}")
    # Don't fail the task on validation warnings — the smoke test task
    # will do comprehensive validation after all MVs are registered
