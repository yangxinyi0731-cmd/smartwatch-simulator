from __future__ import annotations

import hashlib
import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPORT_PATH = PROJECT_ROOT / "reports" / "models" / "fall_detector_tcn_100_cases.json"


def test_committed_fall_report_is_traceable_and_not_presented_as_external_validation() -> None:
    payload = json.loads(REPORT_PATH.read_text(encoding="utf-8"))
    catalog_path = PROJECT_ROOT / payload["dataset"]["catalog_relative_path"]
    assert hashlib.sha256(catalog_path.read_bytes()).hexdigest() == payload["dataset"]["catalog_sha256"]
    assert payload["dataset"]["case_count"] == 100
    assert payload["dataset"]["distribution"] == {
        "OLDER_ADULT__REAL_LAB_ACTIVITY": 30,
        "YOUNG_ADULT__REAL_LAB_ACTIVITY": 30,
        "YOUNG_ADULT__SIMULATED_FALL": 40,
    }
    assert payload["model"]["deployment_approved"] is False
    assert "不是独立泛化评估" in payload["dataset"]["relationship_to_training"]
    assert "没有老人跌倒样本" in payload["older_adl_false_alarm_analysis"]["meaning"]
    assert any("不能作为外部测试准确率" in item for item in payload["limitations"])
    assert len(payload["cases"]) == 100
