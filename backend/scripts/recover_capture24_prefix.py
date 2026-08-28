from __future__ import annotations

import argparse
import binascii
import hashlib
import json
import struct
import zipfile
import zlib
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path, PurePosixPath


PROJECT_ROOT = Path(__file__).resolve().parents[2]
OFFICIAL_SOURCE_URL = (
    "https://ora.ox.ac.uk/objects/"
    "uuid:99d7c092-d865-4a19-b096-cc16440cd001/files/rpr76f381b"
)
OFFICIAL_DECLARED_BYTES = 6_902_652_480
LOCAL_FILE_SIGNATURE = 0x04034B50
LOCAL_FILE_HEADER = struct.Struct("<IHHHHHIIIHH")


@dataclass(frozen=True, slots=True)
class LocalZipEntry:
    name: str
    header_offset: int
    data_offset: int
    data_end: int
    flags: int
    method: int
    dos_time: int
    dos_date: int
    crc32: int
    compressed_size: int
    uncompressed_size: int


@dataclass(frozen=True, slots=True)
class TruncatedEntry:
    name: str
    header_offset: int
    expected_compressed_size: int
    available_compressed_bytes: int


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _safe_member_name(name: str) -> None:
    member = PurePosixPath(name)
    if member.is_absolute() or ".." in member.parts or not member.parts:
        raise ValueError(f"ZIP 成员路径不安全：{name!r}")


def scan_complete_local_entries(
    source_path: Path,
) -> tuple[tuple[LocalZipEntry, ...], TruncatedEntry | None]:
    source_size = source_path.stat().st_size
    entries: list[LocalZipEntry] = []
    offset = 0
    truncated: TruncatedEntry | None = None
    with source_path.open("rb") as source:
        while offset + LOCAL_FILE_HEADER.size <= source_size:
            source.seek(offset)
            header = source.read(LOCAL_FILE_HEADER.size)
            (
                signature,
                _version,
                flags,
                method,
                dos_time,
                dos_date,
                crc32,
                compressed_size,
                uncompressed_size,
                name_length,
                extra_length,
            ) = LOCAL_FILE_HEADER.unpack(header)
            if signature != LOCAL_FILE_SIGNATURE:
                break
            if flags & 0x1:
                raise ValueError("不支持加密 ZIP 成员。")
            if flags & 0x8:
                raise ValueError("不支持使用数据描述符且头部不含尺寸的 ZIP 成员。")
            if method not in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED):
                raise ValueError(f"不支持的 ZIP 压缩方法：{method}")
            name_bytes = source.read(name_length)
            try:
                name = name_bytes.decode("utf-8" if flags & 0x800 else "cp437")
            except UnicodeDecodeError as error:
                raise ValueError("ZIP 成员名称无法解码。") from error
            _safe_member_name(name)
            data_offset = offset + LOCAL_FILE_HEADER.size + name_length + extra_length
            data_end = data_offset + compressed_size
            if data_end > source_size:
                truncated = TruncatedEntry(
                    name=name,
                    header_offset=offset,
                    expected_compressed_size=compressed_size,
                    available_compressed_bytes=max(0, source_size - data_offset),
                )
                break
            entries.append(
                LocalZipEntry(
                    name=name,
                    header_offset=offset,
                    data_offset=data_offset,
                    data_end=data_end,
                    flags=flags,
                    method=method,
                    dos_time=dos_time,
                    dos_date=dos_date,
                    crc32=crc32,
                    compressed_size=compressed_size,
                    uncompressed_size=uncompressed_size,
                )
            )
            offset = data_end
    return tuple(entries), truncated


def _date_time(entry: LocalZipEntry) -> tuple[int, int, int, int, int, int]:
    year = ((entry.dos_date >> 9) & 0x7F) + 1980
    month = (entry.dos_date >> 5) & 0x0F
    day = entry.dos_date & 0x1F
    hour = (entry.dos_time >> 11) & 0x1F
    minute = (entry.dos_time >> 5) & 0x3F
    second = (entry.dos_time & 0x1F) * 2
    datetime(year, month, day, hour, minute, second)
    return year, month, day, hour, minute, second


def _read_member(source, entry: LocalZipEntry) -> bytes:
    source.seek(entry.data_offset)
    compressed = source.read(entry.compressed_size)
    if len(compressed) != entry.compressed_size:
        raise ValueError(f"完整成员读取长度不符：{entry.name}")
    if entry.method == zipfile.ZIP_STORED:
        payload = compressed
    else:
        payload = zlib.decompress(compressed, -zlib.MAX_WBITS)
    if len(payload) != entry.uncompressed_size:
        raise ValueError(f"成员解压长度不符：{entry.name}")
    if binascii.crc32(payload) & 0xFFFFFFFF != entry.crc32:
        raise ValueError(f"成员 CRC-32 不符：{entry.name}")
    return payload


def recover_prefix_archive(
    *,
    source_path: Path,
    output_path: Path,
    catalog_path: Path,
    project_root: Path = PROJECT_ROOT,
) -> dict[str, object]:
    project_root = project_root.resolve()
    source_path = source_path.resolve()
    output_path = output_path.resolve()
    catalog_path = catalog_path.resolve()
    if source_path == output_path:
        raise ValueError("恢复输出不能覆盖来源前缀文件。")
    if output_path.exists() or catalog_path.exists():
        raise FileExistsError("恢复输出或目录文件已存在；为避免覆盖，请先选择新路径。")
    entries, truncated = scan_complete_local_entries(source_path)
    participant_entries = tuple(
        entry
        for entry in entries
        if entry.name.startswith("capture24/P") and entry.name.endswith(".csv.gz")
    )
    if not participant_entries:
        raise ValueError("来源前缀中没有完整 CAPTURE-24 参与者文件。")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    catalog_path.parent.mkdir(parents=True, exist_ok=True)
    with source_path.open("rb") as source, zipfile.ZipFile(
        output_path,
        mode="x",
        compression=zipfile.ZIP_STORED,
        allowZip64=True,
    ) as recovered:
        for entry in entries:
            payload = _read_member(source, entry)
            info = zipfile.ZipInfo(entry.name, date_time=_date_time(entry))
            info.compress_type = zipfile.ZIP_STORED
            info.external_attr = 0o40775 << 16 if entry.name.endswith("/") else 0o600 << 16
            recovered.writestr(info, payload)

    with zipfile.ZipFile(output_path) as recovered:
        bad_member = recovered.testzip()
        recovered_names = recovered.namelist()
    if bad_member is not None:
        raise ValueError(f"恢复 ZIP 自检失败：{bad_member}")
    expected_names = [entry.name for entry in entries]
    if recovered_names != expected_names:
        raise ValueError("恢复 ZIP 成员顺序或数量与已核验前缀不一致。")

    participants = [Path(entry.name).name.removesuffix(".csv.gz") for entry in participant_entries]
    source_hash = _sha256(source_path)
    output_hash = _sha256(output_path)
    try:
        source_relative = source_path.relative_to(project_root).as_posix()
        output_relative = output_path.relative_to(project_root).as_posix()
        catalog_relative = catalog_path.relative_to(project_root).as_posix()
    except ValueError as error:
        raise ValueError("真实恢复运行的来源、输出和目录必须位于项目目录内。") from error
    result: dict[str, object] = {
        "format_version": "1.0.0",
        "dataset": "CAPTURE-24",
        "official_source_url": OFFICIAL_SOURCE_URL,
        "official_declared_bytes": OFFICIAL_DECLARED_BYTES,
        "source_prefix_relative_path": source_relative,
        "source_prefix_bytes": source_path.stat().st_size,
        "source_prefix_sha256": source_hash,
        "recovered_zip_relative_path": output_relative,
        "recovered_zip_bytes": output_path.stat().st_size,
        "recovered_zip_sha256": output_hash,
        "recovered_member_count": len(entries),
        "participant_count": len(participants),
        "participants": participants,
        "metadata_member_recovered": "capture24/metadata.csv" in expected_names,
        "truncated_member_excluded": (
            None
            if truncated is None
            else {
                "name": truncated.name,
                "header_offset": truncated.header_offset,
                "expected_compressed_size": truncated.expected_compressed_size,
                "available_compressed_bytes": truncated.available_compressed_bytes,
            }
        ),
        "catalog_relative_path": catalog_relative,
        "execution_command": (
            "python -m backend.scripts.recover_capture24_prefix "
            f"--source-prefix {source_relative} --output {output_relative} "
            f"--catalog {catalog_relative}"
        ),
        "limitations": [
            "这是官方 ZIP 下载失败后，从文件开头恢复出的完整成员子集，不是完整 151 人数据包。",
            "只有通过本地头部尺寸、解压长度和 CRC-32 核验的完整成员进入恢复 ZIP。",
            "被截断成员和其后的未知成员均未恢复；不得把本目录描述为完整 CAPTURE-24。",
            "后续训练必须保存实际参与者清单，并使用互不重叠的训练与评估参与者。",
        ],
        "raw_or_recovered_data_committed": False,
    }
    catalog_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="从不完整 CAPTURE-24 ZIP 前缀恢复已完整写入并通过 CRC 的成员。"
    )
    parser.add_argument("--source-prefix", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--catalog", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = recover_prefix_archive(
        source_path=args.source_prefix,
        output_path=args.output,
        catalog_path=args.catalog,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
