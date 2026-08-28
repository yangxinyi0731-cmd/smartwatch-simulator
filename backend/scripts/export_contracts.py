from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import TypeAdapter

from backend.app.contracts import (
    CaseContract,
    ModelManifest,
    ModelOutput,
    ReplayEvent,
    SensorWindow,
    contract_catalog,
)
from backend.app.main import create_app


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONTRACT_DIRECTORY = PROJECT_ROOT / "docs" / "contracts"
OPENAPI_PATH = CONTRACT_DIRECTORY / "openapi.json"
DOMAIN_SCHEMA_PATH = CONTRACT_DIRECTORY / "domain-contract.schema.json"


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def build_domain_schema() -> dict[str, Any]:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "模拟智能手表统一领域合同",
        "contract_version": contract_catalog().contract_version,
        "schemas": {
            "CaseContract": CaseContract.model_json_schema(),
            "SensorWindow": SensorWindow.model_json_schema(),
            "ModelManifest": ModelManifest.model_json_schema(),
            "ModelOutput": TypeAdapter(ModelOutput).json_schema(),
            "ReplayEvent": TypeAdapter(ReplayEvent).json_schema(),
        },
    }


def main() -> None:
    app = create_app()
    _write_json(OPENAPI_PATH, app.openapi())
    _write_json(DOMAIN_SCHEMA_PATH, build_domain_schema())
    print(OPENAPI_PATH.relative_to(PROJECT_ROOT))
    print(DOMAIN_SCHEMA_PATH.relative_to(PROJECT_ROOT))


if __name__ == "__main__":
    main()
