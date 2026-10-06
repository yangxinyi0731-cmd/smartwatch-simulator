"""USB 串口实时读取 M5StickS3 六轴数据流，并提供滚动研究分析。

仅在用户显式调用 /api/live/start 时占用串口；停止后立即释放。
所有输出都是滚动窗口上的研究模型结果，不是现实报警。
"""
from __future__ import annotations

import re
import threading
import time
from collections import deque
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np

try:
    import serial
    from serial.tools import list_ports
except ImportError:  # pragma: no cover - 缺少 pyserial 时保持只读状态
    serial = None
    list_ports = None

from research.early_risk.common import PROJECT_ROOT
from research.early_risk.upload_analysis import analyze_normalized_imu

TARGET_RATE_HZ = 50.0
BUFFER_SECONDS = 120
OFFLINE_AFTER_S = 3.0
RECONNECT_INTERVAL_S = 2.0
MAX_SAMPLES_PER_POLL = 600
ANALYSIS_WINDOW_S = 30.0
ANALYSIS_CACHE_S = 2.0
MINIMUM_ANALYSIS_SAMPLES = 50
OUTPUT_DIR = PROJECT_ROOT / "data" / "raw" / "watch"
LINE_RE = re.compile(
    r"^(\d+),(-?\d+\.?\d*),(-?\d+\.?\d*),(-?\d+\.?\d*),"
    r"(-?\d+\.?\d*),(-?\d+\.?\d*),(-?\d+\.?\d*)$"
)


def parse_sample_line(line: str) -> tuple[int, tuple[float, ...]] | None:
    match = LINE_RE.match(line.strip())
    if match is None:
        return None
    t_ms = int(match.group(1))
    values = tuple(float(match.group(index)) for index in range(2, 8))
    if not all(np.isfinite(value) for value in values):
        return None
    return t_ms, values


def find_watch_port() -> str | None:
    if serial is None or list_ports is None:
        return None
    candidates = [item for item in list_ports.comports() if item.vid == 0x303A]
    candidates.sort(key=lambda item: 0 if item.pid == 0x1001 else 1)
    return candidates[0].device if candidates else None


class WatchLiveSession:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._serial = None
        self._buffer: deque[tuple[int, tuple[float, ...]]] = deque(
            maxlen=int(BUFFER_SECONDS * TARGET_RATE_HZ) + 100
        )
        self._cursor = 0
        self._status = "stopped"
        self._port: str | None = None
        self._last_error: str | None = None
        self._last_sample_at: float | None = None
        self._started_at: float | None = None
        self._analysis_cache: tuple[float, dict[str, Any]] | None = None

    def start(self) -> dict[str, Any]:
        with self._lock:
            if self._thread is not None and self._thread.is_alive():
                return self._status_payload_locked()
            if serial is None:
                self._status = "error"
                self._last_error = "本机缺少串口支持库（pyserial），无法读取手表数据。"
                return self._status_payload_locked()
            self._stop_event.clear()
            self._buffer.clear()
            self._cursor = 0
            self._analysis_cache = None
            self._last_error = None
            self._last_sample_at = None
            self._port = None
            self._started_at = time.time()
            self._status = "connecting"
            self._thread = threading.Thread(
                target=self._run, name="watch-live-reader", daemon=True
            )
            self._thread.start()
            return self._status_payload_locked()

    def stop(self) -> dict[str, Any]:
        self._stop_event.set()
        thread = self._thread
        if thread is not None:
            thread.join(timeout=2.0)
        with self._lock:
            self._close_serial_locked()
            self._thread = None
            if self._status != "error":
                self._status = "stopped"
            return self._status_payload_locked()

    def snapshot(self, since: int) -> dict[str, Any]:
        with self._lock:
            total = self._cursor
            rows = list(self._buffer)
            first_index = total - len(rows)
            offset = min(max(0, since - first_index), len(rows))
            selected = rows[offset : offset + MAX_SAMPLES_PER_POLL]
            next_cursor = first_index + offset + len(selected)
            age = (
                time.monotonic() - self._last_sample_at
                if self._last_sample_at is not None
                else None
            )
            payload: dict[str, Any] = {
                "status": self._status,
                "port": self._port,
                "last_error": self._last_error,
                "sample_count": total,
                "rate_hz": self._rate_locked(),
                "cursor": next_cursor,
                "samples": [
                    [int(t_ms), *[round(value, 4) for value in values]]
                    for t_ms, values in selected
                ],
                "last_sample_age_s": round(age, 2) if age is not None else None,
            }
        payload["analysis"] = self._analysis(rows)
        return payload

    def save_recording(self) -> dict[str, Any]:
        with self._lock:
            rows = list(self._buffer)
        if len(rows) < MINIMUM_ANALYSIS_SAMPLES:
            raise ValueError("实时缓冲不足 1 秒数据，暂时没有可保存的记录。")
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        file_name = f"live-{datetime.now().strftime('%Y%m%d-%H%M%S')}.csv"
        output_path = OUTPUT_DIR / file_name
        first_t_ms = rows[0][0]
        lines = ["time_s,ax,ay,az,gx,gy,gz"]
        for t_ms, values in rows:
            seconds = (t_ms - first_t_ms) / 1000.0
            if seconds < 0:
                continue
            lines.append(
                f"{seconds:.3f}," + ",".join(f"{value:.4f}" for value in values)
            )
        output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        duration_s = (rows[-1][0] - first_t_ms) / 1000.0
        try:
            relative = output_path.relative_to(PROJECT_ROOT).as_posix()
        except ValueError:
            relative = str(output_path)
        return {
            "status": "SAVED",
            "file": relative,
            "sample_count": len(rows),
            "duration_s": round(duration_s, 2),
        }

    def _status_payload_locked(self) -> dict[str, Any]:
        return {
            "status": self._status,
            "port": self._port,
            "last_error": self._last_error,
            "sample_count": self._cursor,
        }

    def _rate_locked(self) -> float:
        rows = list(self._buffer)[-int(5 * TARGET_RATE_HZ) :]
        if len(rows) < 2:
            return 0.0
        span_s = (rows[-1][0] - rows[0][0]) / 1000.0
        if span_s <= 0:
            return 0.0
        return round((len(rows) - 1) / span_s, 1)

    def _close_serial_locked(self) -> None:
        if self._serial is not None:
            try:
                self._serial.close()
            except Exception:
                pass
            self._serial = None

    def _run(self) -> None:
        while not self._stop_event.is_set():
            with self._lock:
                if self._serial is None:
                    candidate = find_watch_port()
                    if candidate is None:
                        self._status = "connecting"
                        self._last_error = (
                            "没有找到 Espressif 串口设备；请确认手表已用数据线连接。"
                        )
                    else:
                        try:
                            self._serial = serial.Serial(candidate, 115200, timeout=0.5)
                            self._port = candidate
                            self._status = "live"
                            self._last_error = None
                        except Exception as exc:
                            self._status = "connecting"
                            self._last_error = f"串口打开失败：{exc}"
                serial_port = self._serial
            if serial_port is None:
                if self._stop_event.wait(RECONNECT_INTERVAL_S):
                    return
                continue
            try:
                line = serial_port.readline()
            except Exception as exc:
                with self._lock:
                    self._close_serial_locked()
                    self._status = "reconnecting"
                    self._last_error = f"串口读取失败：{exc}"
                if self._stop_event.wait(RECONNECT_INTERVAL_S):
                    return
                continue
            if not line:
                with self._lock:
                    if (
                        self._serial is not None
                        and self._last_sample_at is not None
                        and time.monotonic() - self._last_sample_at > OFFLINE_AFTER_S
                    ):
                        self._close_serial_locked()
                        self._status = "reconnecting"
                        self._last_error = "超过 3 秒没有收到数据，正在尝试重新连接。"
                continue
            parsed = parse_sample_line(line.decode("ascii", errors="ignore"))
            if parsed is None:
                continue
            t_ms, values = parsed
            with self._lock:
                self._buffer.append((t_ms, values))
                self._cursor += 1
                self._last_sample_at = time.monotonic()
                if self._status != "live":
                    self._status = "live"
                    self._last_error = None

    def _analysis(self, rows: list[tuple[int, tuple[float, ...]]]) -> dict[str, Any]:
        if len(rows) < MINIMUM_ANALYSIS_SAMPLES:
            return {
                "status": "WAITING",
                "detail": "等待至少 1 秒实时数据后开始滚动计算。",
            }
        now = time.monotonic()
        with self._lock:
            cache = self._analysis_cache
        if cache is not None and now - cache[0] <= ANALYSIS_CACHE_S:
            return cache[1]
        try:
            result = self._compute_analysis(rows)
        except Exception as exc:  # pragma: no cover - 防御性兜底
            result = {"status": "ERROR", "detail": f"滚动分析暂时失败：{exc}"}
        with self._lock:
            self._analysis_cache = (now, result)
        return result

    def _compute_analysis(
        self, rows: list[tuple[int, tuple[float, ...]]]
    ) -> dict[str, Any]:
        times = np.asarray([row[0] for row in rows], dtype=np.float64) / 1000.0
        values = np.asarray([row[1] for row in rows], dtype=np.float64)
        end = float(times[-1])
        start = max(float(times[0]), end - ANALYSIS_WINDOW_S)
        mask = times >= start
        times = times[mask]
        values = values[mask]
        sample_count = int((times[-1] - times[0]) * TARGET_RATE_HZ) + 1
        if sample_count < MINIMUM_ANALYSIS_SAMPLES:
            return {"status": "WAITING", "detail": "实时窗口不足 1 秒。"}
        grid = times[0] + np.arange(sample_count, dtype=np.float64) / TARGET_RATE_HZ
        normalized = np.column_stack(
            [np.interp(grid, times, values[:, axis]) for axis in range(6)]
        ).astype(np.float32)
        if not np.isfinite(normalized).all():
            return {"status": "WAITING", "detail": "实时数据包含无效数值。"}
        analysis = analyze_normalized_imu(normalized)
        acceleration = np.linalg.norm(values[:, :3], axis=1)
        rotation = np.linalg.norm(values[:, 3:], axis=1)
        activity = analysis["activity_model"]
        fall = analysis["fall_model"]
        risk = analysis["early_risk_model"]
        return {
            "status": "COMPLETED",
            "window_s": round((len(normalized) - 1) / TARGET_RATE_HZ, 1),
            "activity": {
                "status": activity["status"],
                "label": activity["label"],
                "detail": activity["detail"],
            },
            "fall": {
                "status": fall["status"],
                "screening": fall["screening"],
                "max_score": fall["max_score"],
                "candidate_count": len(fall["candidate_windows"]),
                "detail": fall.get("detail"),
            },
            "risk": {
                "status": risk["status"],
                "attention_detected": risk.get("attention_detected"),
            },
            "peaks": {
                "acceleration_mps2": round(float(np.max(acceleration)), 2),
                "rotation_rad_s": round(float(np.max(rotation)), 2),
            },
            "conclusion": analysis["interpretation"]["conclusion"],
        }
