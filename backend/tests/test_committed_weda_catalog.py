from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from backend.app.contracts import (
    AgeGroup,
    CaseContract,
    CaseSourceFile,
    GroundTruthEvent,
    SensorQualityContract,
    SensorStreamContract,
    SourceLicenseStatus,
    TruthCategory,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CATALOG_PATH = PROJECT_ROOT / "data" / "catalog" / "weda_fall_100_v1.json"


def test_committed_weda_catalog_preserves_provenance_and_truth_boundaries() -> None:
    payload = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    assert payload["case_count"] == 100
    assert payload["data_handling"] == {
        "raw_and_processed_files_committed": False,
        "redistribution_allowed": None,
        "reason": "来源许可证未核验；传感器文件只保留在本机 Git 忽略目录。",
    }

    cases = [CaseContract.model_validate(item["case"]) for item in payload["cases"]]
    streams = [
        SensorStreamContract.model_validate(item["stream"])
        for item in payload["cases"]
    ]
    qualities = [
        SensorQualityContract.model_validate(item["quality"])
        for item in payload["cases"]
    ]
    source_files = [
        CaseSourceFile.model_validate(source_file)
        for item in payload["cases"]
        for source_file in item["source_files"]
    ]
    events = [
        GroundTruthEvent.model_validate(event)
        for item in payload["cases"]
        for event in item["ground_truth_events"]
    ]

    assert len(cases) == len(streams) == len(qualities) == len(events) == 100
    assert len(source_files) == 240
    assert len({case.case_id for case in cases}) == 100
    assert len({case.source_sha256 for case in cases}) == 100
    assert all(case.source.license_status is SourceLicenseStatus.UNVERIFIED for case in cases)
    assert all(case.source.redistribution_allowed is None for case in cases)
    assert all(tuple(stream.channels) == ("ax", "ay", "az", "gx", "gy", "gz") for stream in streams)
    assert all(stream.sample_count >= 200 for stream in streams)

    distribution = Counter((case.age_group, case.truth_category) for case in cases)
    assert distribution == {
        (AgeGroup.YOUNG_ADULT, TruthCategory.SIMULATED_FALL): 40,
        (AgeGroup.OLDER_ADULT, TruthCategory.REAL_LAB_ACTIVITY): 30,
        (AgeGroup.YOUNG_ADULT, TruthCategory.REAL_LAB_ACTIVITY): 30,
    }
    simulated_falls = [
        case for case in cases if case.truth_category is TruthCategory.SIMULATED_FALL
    ]
    assert all(case.age_group is AgeGroup.YOUNG_ADULT for case in simulated_falls)
    assert all("年轻参与者" in case.title and "模拟跌倒" in case.title for case in simulated_falls)
    older_cases = [case for case in cases if case.age_group is AgeGroup.OLDER_ADULT]
    assert all(case.truth_category is TruthCategory.REAL_LAB_ACTIVITY for case in older_cases)
    assert all("日常活动" in case.title and "跌倒" not in case.title for case in older_cases)
