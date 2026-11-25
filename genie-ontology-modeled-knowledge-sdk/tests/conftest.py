"""Shared pytest fixtures for the Genie Ontology Modeled Knowledge SDK.

``FakeWorkspaceClient`` is an in-memory stand-in for
``databricks.sdk.WorkspaceClient`` with the surface the SDK uses:
``catalogs.get/list``, ``schemas.get/list``, ``tables.get/list`` and
``files.list_directory_contents``. Unknown names raise ``FakeNotFound``
(like the SDK's ``NotFound``). Later sessions may extend it in their own test
files (subclass or monkeypatch); ask session 01 for changes here.
"""

from __future__ import annotations

import copy
from types import SimpleNamespace
from typing import Iterable, Iterator

import pytest

TPCH_TABLES = ["customer", "orders", "lineitem", "part", "partsupp", "supplier", "nation", "region"]

TPCH_CONFIG = {
    "domain_name": "tpch_supply_chain",
    "domain_context": "TPC-H supply chain: customers place orders for parts supplied by suppliers across nations and regions.",
    "source_tables": [f"samples.tpch.{t}" for t in TPCH_TABLES],
    "target_catalog": "main",
    "target_schema": "ontology_tpch",
    "max_metric_views_per_agent": 50,
}


class FakeNotFound(Exception):
    """Raised for unknown objects, like ``databricks.sdk.errors.NotFound``."""


class _Catalogs:
    def __init__(self, ws: "FakeWorkspaceClient"):
        self._ws = ws

    def get(self, name: str) -> SimpleNamespace:
        if name not in self._ws.catalog_names():
            raise FakeNotFound(f"Catalog '{name}' does not exist.")
        return SimpleNamespace(name=name, full_name=name)

    def list(self, **_: object) -> Iterator[SimpleNamespace]:
        for name in sorted(self._ws.catalog_names()):
            yield SimpleNamespace(name=name, full_name=name)


class _Schemas:
    def __init__(self, ws: "FakeWorkspaceClient"):
        self._ws = ws

    def get(self, full_name: str) -> SimpleNamespace:
        catalog, _, schema = full_name.partition(".")
        if schema not in self._ws.data.get(catalog, {}):
            raise FakeNotFound(f"Schema '{full_name}' does not exist.")
        return SimpleNamespace(name=schema, catalog_name=catalog, full_name=full_name)

    def list(self, catalog_name: str, **_: object) -> Iterator[SimpleNamespace]:
        if catalog_name not in self._ws.data:
            raise FakeNotFound(f"Catalog '{catalog_name}' does not exist.")
        for schema in sorted(self._ws.data[catalog_name]):
            yield SimpleNamespace(name=schema, catalog_name=catalog_name, full_name=f"{catalog_name}.{schema}")


class _Tables:
    def __init__(self, ws: "FakeWorkspaceClient"):
        self._ws = ws

    def get(self, full_name: str, **_: object) -> SimpleNamespace:
        parts = full_name.split(".")
        if len(parts) != 3 or parts[2] not in self._ws.data.get(parts[0], {}).get(parts[1], []):
            raise FakeNotFound(f"Table '{full_name}' does not exist.")
        return SimpleNamespace(name=parts[2], catalog_name=parts[0], schema_name=parts[1], full_name=full_name)

    def list(self, catalog_name: str, schema_name: str, **_: object) -> Iterator[SimpleNamespace]:
        if schema_name not in self._ws.data.get(catalog_name, {}):
            raise FakeNotFound(f"Schema '{catalog_name}.{schema_name}' does not exist.")
        for t in sorted(self._ws.data[catalog_name][schema_name]):
            yield SimpleNamespace(
                name=t, catalog_name=catalog_name, schema_name=schema_name,
                full_name=f"{catalog_name}.{schema_name}.{t}",
            )


class _Files:
    def __init__(self, ws: "FakeWorkspaceClient"):
        self._ws = ws

    def list_directory_contents(self, directory_path: str, **_: object) -> Iterator[SimpleNamespace]:
        key = directory_path.rstrip("/")
        if key not in self._ws.volume_dirs:
            raise FakeNotFound(f"Directory '{directory_path}' does not exist.")
        for entry in self._ws.volume_dirs[key]:
            yield SimpleNamespace(path=f"{key}/{entry}", name=entry, is_directory=False)


class FakeWorkspaceClient:
    """In-memory WorkspaceClient.

    ``data`` maps catalog -> schema -> list of table names. ``extra_catalogs``
    are catalogs with no schemas. ``volume_dirs`` maps a ``/Volumes/...``
    directory (no trailing slash) to its file names.
    """

    def __init__(
        self,
        data: dict[str, dict[str, list[str]]] | None = None,
        volume_dirs: dict[str, list[str]] | None = None,
        extra_catalogs: Iterable[str] = (),
    ):
        self.data = copy.deepcopy(data or {})
        self.volume_dirs = {k.rstrip("/"): list(v) for k, v in (volume_dirs or {}).items()}
        self.extra_catalogs = set(extra_catalogs)
        self.catalogs = _Catalogs(self)
        self.schemas = _Schemas(self)
        self.tables = _Tables(self)
        self.files = _Files(self)

    def catalog_names(self) -> set[str]:
        return set(self.data) | self.extra_catalogs


@pytest.fixture
def fake_ws() -> FakeWorkspaceClient:
    """Workspace with ``samples.tpch`` (8 tables), an ``information_schema``,
    a ``samples.nyctaxi`` schema, an empty ``main`` catalog and one volume dir."""
    return FakeWorkspaceClient(
        data={
            "samples": {
                "tpch": list(TPCH_TABLES),
                "nyctaxi": ["trips"],
                "information_schema": ["tables", "columns"],
            },
        },
        volume_dirs={"/Volumes/main/ontology_tpch/context": ["glossary.md", "kpis.csv"]},
        extra_catalogs=["main"],
    )


@pytest.fixture
def tpch_config() -> dict:
    """The TPC-H dogfood config from docs/plans/INDEX.md (a fresh copy)."""
    return copy.deepcopy(TPCH_CONFIG)
