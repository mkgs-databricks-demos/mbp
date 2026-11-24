# Databricks notebook source
# MAGIC %md
# MAGIC # Generate Metric View Manifest
# MAGIC
# MAGIC Scans the `metric_views/` directory in the bundle, builds a JSON array
# MAGIC of metric view definitions, and sets it as a task value for the downstream
# MAGIC `for_each_task` to iterate over.
# MAGIC
# MAGIC **Inputs (base_parameters):**
# MAGIC - `metric_views_dir`: Absolute workspace path to the `metric_views/` folder

# COMMAND ----------

import json
import os
import yaml

# COMMAND ----------

# Read the parameter
dbutils.widgets.text("metric_views_dir", "")
metric_views_dir = dbutils.widgets.get("metric_views_dir")

if not metric_views_dir:
    raise ValueError("metric_views_dir parameter is required")

print(f"Scanning: {metric_views_dir}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Scan for YAML files

# COMMAND ----------

manifest = []

for root, dirs, files in os.walk(metric_views_dir):
    for filename in sorted(files):
        if filename.endswith((".yml", ".yaml")) and not filename.startswith("_"):
            yaml_path = os.path.join(root, filename)
            rel_path = os.path.relpath(yaml_path, metric_views_dir)

            # Parse the YAML to extract the metric view name and domain
            with open(yaml_path, "r") as f:
                content = f.read()

            # Extract the name from the filename (strip extension)
            mv_name = os.path.splitext(filename)[0]

            # Extract the domain from the parent directory
            domain = os.path.basename(root)
            if domain == os.path.basename(metric_views_dir):
                domain = "default"

            entry = {
                "name": mv_name,
                "yaml_path": yaml_path,
                "rel_path": rel_path,
                "domain": domain,
            }

            manifest.append(entry)
            print(f"  Found: {mv_name} (domain: {domain})")

print(f"\nTotal metric views found: {len(manifest)}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Validate manifest

# COMMAND ----------

if len(manifest) == 0:
    raise ValueError(
        f"No metric view YAML files found in {metric_views_dir}. "
        "Expected .yml or .yaml files (not starting with _)."
    )

# Check for duplicate names
names = [m["name"] for m in manifest]
dupes = [n for n in names if names.count(n) > 1]
if dupes:
    raise ValueError(f"Duplicate metric view names found: {set(dupes)}")

print("Manifest validation passed.")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Set task value for forEach

# COMMAND ----------

# The forEach task reads this as its input array
# Each element becomes {{input}} in the nested task
dbutils.jobs.taskValues.set(key="metric_view_list", value=manifest)

print(f"Task value 'metric_view_list' set with {len(manifest)} entries.")
print(json.dumps(manifest, indent=2))
