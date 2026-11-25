# Genie Ontology Modeled Knowledge SDK — Glossary

Matthew Giglia | Databricks Field Engineering
Version: 1.0 | Date: 2026-11-24

Terms and definitions used throughout the SDK design. Structured for potential UC Pages registration.

---

## Genie Ontology

**Definition:** Unity Catalog Semantics (metric views, Pages, domains/subdomains, descriptions, certification) + certified domain Genie Agents.

**Business Context:** The governed, versioned knowledge layer that makes Genie One, Genie Code, and Genie Agents accurate and trustworthy for enterprise use.

**Related Terms:** UC Semantics, Metric View, Genie Agent, UC Pages, Domain

---

## Metric View

**Definition:** A Unity Catalog object that centralizes business metric definitions. Unlike standard views that lock in aggregations at creation time, metric views separate measure definitions from dimension groupings, enabling flexible analysis at query time.

**Business Context:** Governed, versioned enterprise assets deployed only with DABs. Deterministic and testable like standard ETL.

**Data Usage:** Queried with `MEASURE()` syntax. Consumed by dashboards, Genie Agents, notebooks, and downstream applications.

**Related Terms:** Genie Ontology, YAML, Dimension, Measure

---

## Genie Build Wave

**Definition:** A logical phase in the SDK pipeline, implemented as a Genie Code job task deployed via DABs using the `genie_task` swap pattern. Each wave produces artifacts in the repo.

**Business Context:** Waves execute sequentially (0 through 8), with each wave depending on the outputs of previous waves.

**Related Terms:** Genie Ontology Modeled Knowledge SDK, DAB, Genie Code

---

## forEach Registration

**Definition:** A Lakeflow Jobs `for_each_task` that iterates over a manifest of metric view definitions, registering each one via `CREATE OR REPLACE VIEW ... WITH METRICS LANGUAGE YAML`.

**Business Context:** Adding a new metric view = adding a YAML file. No code changes to the registration pipeline.

**Related Terms:** Metric View, DAB 1, Manifest

---

## Serialized Space

**Definition:** The JSON configuration of a Genie Agent, stored as a `.geniespace.json` file. Contains data sources, instructions, example SQLs, join specs, and sample questions.

**Business Context:** The source-of-truth for a Genie Agent's configuration, version-controlled in Git and deployed via DABs.

**Related Terms:** Genie Agent, DAB 2, `.geniespace.json`

---

## Domain Context

**Definition:** A free-text description of the business domain, use case, or function being modeled. Provided as an SDK input.

**Business Context:** Drives Wave 1 (Domain Research) — the SDK uses this to search for industry-standard terminology, KPIs, regulatory context, and competitive landscape.

**Related Terms:** Genie Ontology Modeled Knowledge SDK, Wave 1, UC Domain

---

## Materialization

**Definition:** Pre-computation of metric view results using materialized views with automatic incremental refresh. Accelerates query performance and reduces cost.

**Business Context:** The SDK auto-detects metric views that would benefit from materialization based on source table volume, join complexity, and estimated query frequency.

**Related Terms:** Metric View, Wave 4, `refresh_policy`

---

## Zero Hardcoding Rule

**Definition:** Nothing in the bundle is hardcoded — catalog names, schema names, table references, everything is parameterized. The catalog is the environment discriminator.

**Business Context:** Enables the same YAML to deploy to dev, tst, uat, and prd by changing only `target_catalog` and `source_catalog_for_reads`.

**Related Terms:** DAB, CI/CD, Target Portability
