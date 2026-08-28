from __future__ import annotations

import json
import zipfile
from pathlib import Path

from backend.scripts.recover_capture24_prefix import (
    recover_prefix_archive,
    scan_complete_local_entries,
)


def test_recovery_keeps_only_complete_crc_verified_local_entries(tmp_path: Path) -> None:
    complete = tmp_path / "complete.zip"
    with zipfile.ZipFile(complete, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("capture24/", b"")
        archive.writestr("capture24/metadata.csv", b"pid,age\nP001,UNKNOWN\n")
        archive.writestr("capture24/P001.csv.gz", b"participant-one" * 200)
        archive.writestr("capture24/P002.csv.gz", b"participant-two" * 200)

    entries, _ = scan_complete_local_entries(complete)
    truncated_entry = next(item for item in entries if item.name.endswith("P002.csv.gz"))
    prefix = tmp_path / "prefix.zip"
    prefix.write_bytes(complete.read_bytes()[: truncated_entry.data_offset + 19])

    recovered = tmp_path / "recovered.zip"
    catalog = tmp_path / "catalog.json"
    result = recover_prefix_archive(
        source_path=prefix,
        output_path=recovered,
        catalog_path=catalog,
        project_root=tmp_path,
    )

    assert result["participant_count"] == 1
    assert result["participants"] == ["P001"]
    assert result["truncated_member_excluded"]["name"] == "capture24/P002.csv.gz"
    with zipfile.ZipFile(recovered) as archive:
        assert archive.testzip() is None
        assert archive.namelist() == [
            "capture24/",
            "capture24/metadata.csv",
            "capture24/P001.csv.gz",
        ]
        assert archive.read("capture24/P001.csv.gz") == b"participant-one" * 200
    saved = json.loads(catalog.read_text(encoding="utf-8"))
    assert saved["recovered_zip_sha256"] == result["recovered_zip_sha256"]
    assert "不是完整 151 人数据包" in saved["limitations"][0]
