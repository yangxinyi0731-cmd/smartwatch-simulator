from __future__ import annotations

import json

from backend.app.main import create_app
from backend.scripts.export_contracts import (
    DOMAIN_SCHEMA_PATH,
    OPENAPI_PATH,
    build_domain_schema,
)


def test_committed_openapi_snapshot_matches_application() -> None:
    committed = json.loads(OPENAPI_PATH.read_text(encoding="utf-8"))

    assert committed == create_app().openapi()


def test_committed_domain_schema_matches_pydantic_contracts() -> None:
    committed = json.loads(DOMAIN_SCHEMA_PATH.read_text(encoding="utf-8"))

    assert committed == build_domain_schema()
