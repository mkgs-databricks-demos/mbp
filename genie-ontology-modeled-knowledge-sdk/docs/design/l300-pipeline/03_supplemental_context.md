# Session 03 — Supplemental Context Parser

**Wave:** 2 — Supplemental Context Extraction
**Mode:** execute
**Depends on:** 01
**Estimated effort:** Medium (~30 min)

## Goal

Extract business context from all supplemental materials provided via volume directories and dashboard inputs.

## Context

Read `sdk_config.json` for `supplemental_volume_dirs` and `dashboard_inputs`. If either is empty, write a minimal context doc noting no supplemental materials were provided.

## Tasks

### 1. Inventory Supplemental Files

List all files in each volume directory. Classify by type (md, pdf, docx, csv, json, xlsx, pbix, twb/tds). Write inventory to `docs/context/00_source_inventory.md`.

### 2. Extract from Each File

For each file, extract: business rules, KPI definitions, join criteria, dimension hierarchies, filter logic. Write one context doc per source file: `docs/context/<filename>_context.md`.

### 3. Dashboard-Specific Extraction

For PowerBI/Tableau files: extract DAX measures / calculated fields (candidate MV measures), relationship definitions (candidate join specs), report filters (candidate MV filters), visual groupings (candidate dimensions).

### 4. Merge into Glossary

Any new terms discovered go to `docs/semantics/` following the UC Pages format.

## Pass Criteria

- [ ] `docs/context/00_source_inventory.md` lists all supplemental files
- [ ] One context doc per supplemental file processed
- [ ] Dashboard measures extracted (if dashboard inputs provided)
- [ ] New glossary candidates added to `docs/semantics/`
