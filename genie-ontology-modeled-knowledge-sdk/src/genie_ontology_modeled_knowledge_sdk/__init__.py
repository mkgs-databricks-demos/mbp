"""Genie Ontology Modeled Knowledge SDK.

Automates the standup of modeled knowledge for Genie Ontology: Unity Catalog
source assets + supplemental business context -> parameterized metric views ->
UC Pages -> curated Genie Agents -> an initial tuning plan.

Modules (import them directly; nothing is imported eagerly here):

* ``config``     - input contract: ``SdkConfig``, ``load_config``, ``config_from_dict``,
                   ``validate_config``, ``check_access``, ``expand_tables``
* ``mv_yaml``    - metric view YAML load / substitute / validate / render DDL (+ CLI)
* ``manifest``   - ``manifest.json`` (forEach registration input) build / write / validate
* ``geniespace`` - Genie Agent planning and ``.geniespace.json`` builder (+ CLI)
* ``pages``      - glossary term files -> UC Pages payloads and upsert
* ``benchmark``  - Genie Agent benchmark questions, run and scoring
* ``scaffold``   - ``scaffold_project`` for a new run project

Library modules are pure Python (no Spark imports). Databricks access goes
through an injected ``WorkspaceClient`` so tests can pass a fake.
"""

__version__ = "0.0.1"

__all__ = ["__version__"]
