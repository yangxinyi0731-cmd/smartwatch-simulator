"""实时读取 M5StickS3 六轴数据流（USB 串口或 Wi-Fi 热点），并提供滚动研究分析。

仅在用户显式调用 /api/live/start 时占用串口或连接手表热点；停止后立即释放。
滚动结果会同步推送到手表屏幕（USB 与 Wi-Fi 两种连接都支持）。
所有输出都是滚动窗口上的研究模型结果，不是现实报警。
"""
from __future__ import annotations

import json
import re
import socket
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
WIFI_TARGET_PATH = OUTPUT_DIR / "wifi_target.json"
WIFI_HOST = "192.168.4.1"
WIFI_PORT = 5005
SOURCES = ("usb", "wifi")
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


def resolve_wifi_host() -> str:
    """读取 tools/watch_join_wifi.py 记录的手表 Wi-Fi 地址；否则退回默认热点地址。"""
    try:
        payload = json.loads(WIFI_TARGET_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return WIFI_HOST
    host = str(payload.get("ip", "")).strip()
    return host or WIFI_HOST


class WatchLiveSession:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._serial = None
        self._wifi_socket: socket.socket | None = None
        self._wifi_file = None
        self._buffer: deque[tuple[int, tuple[float, ...]]] = deque(
            maxlen=int(BUFFER_SECONDS * TARGET_RATE_HZ) + 100
        )
        self._cursor = 0
        self._status = "stopped"
        self._source = "usb"
        self._port: str | None = None
        self._last_error: str | None = None
        self._last_sample_at: float | None = None
        self._started_at: float | None = None
        self._analysis_cache: tuple[float, dict[str, Any]] | None = None
        self._pushed_text: str | None = None
        self._alert_active = False
        self._device: dict[str, Any] = {}

    def start(self, source: str = "usb") -> dict[str, Any]:
        with self._lock:
            if source not in SOURCES:
                raise ValueError("数据来源必须是 usb（USB 串口）或 wifi（手表热点）。")
            if self._thread is not None and self._thread.is_alive():
                return self._status_payload_locked()
            if source == "usb" and serial is None:
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
            self._source = source
            self._pushed_text = None
            self._alert_active = False
            self._device = {}
            self._started_at = time.time()
            self._status = "connecting"
            self._thread = threading.Thread(
                target=self._run, name="watch-live-reader", daemon=True
            )
            self._thread.start()
            return self._status_payload_locked()

    def stop(self) -> dict[str, Any]:
        self.send_command("#CLEAR")
        self.send_command("#VIB:0")
        self._stop_event.set()
        thread = self._thread
        if thread is not None:
            thread.join(timeout=2.0)
        with self._lock:
            self._close_connection_locked()
            self._thread = None
            self._pushed_text = None
            self._alert_active = False
            if self._status != "error":
                self._status = "stopped"
            return self._status_payload_locked()

    def send_command(self, command: str) -> bool:
        payload = (command.strip() + "\n").encode("utf-8")
        with self._lock:
            source = self._source
            serial_port = self._serial
            wifi_socket = self._wifi_socket
        try:
            if source == "usb" and serial_port is not None:
                serial_port.write(payload)
                return True
            if source == "wifi" and wifi_socket is not None:
                wifi_socket.sendall(payload)
                return True
        except Exception:
            return False
        return False

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
                "source": self._source,
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
                "device": dict(self._device),
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
            "source": self._source,
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

    def _close_connection_locked(self) -> None:
        if self._serial is not None:
            try:
                self._serial.close()
            except Exception:
                pass
            self._serial = None
        if self._wifi_file is not None:
            try:
                self._wifi_file.close()
            except Exception:
                pass
            self._wifi_file = None
        if self._wifi_socket is not None:
            try:
                self._wifi_socket.close()
            except Exception:
                pass
            self._wifi_socket = None

    def _ensure_connection_locked(self) -> bool:
        if self._source == "usb":
            if self._serial is not None:
                return True
            candidate = find_watch_port()
            if candidate is None:
                self._status = "connecting"
                self._last_error = (
                    "没有找到 Espressif 串口设备；请确认手表已用数据线连接。"
                )
                return False
            try:
                self._serial = serial.Serial(candidate, 115200, timeout=0.5)
            except Exception as exc:
                self._status = "connecting"
                self._last_error = f"串口打开失败：{exc}"
                return False
            self._port = candidate
            self._status = "live"
            self._last_error = None
            return True

        if self._wifi_socket is not None:
            return True
        host = resolve_wifi_host()
        try:
            self._wifi_socket = socket.create_connection((host, WIFI_PORT), timeout=4.0)
            self._wifi_file = self._wifi_socket.makefile("rb")
        except OSError as exc:
            self._wifi_socket = None
            self._wifi_file = None
            self._status = "connecting"
            self._last_error = (
                f"连接手表 Wi-Fi 失败：{exc}；请确认手表已通过"
                " scripts\\windows\\connect-watch-wifi.cmd 连接过网络。"
            )
            return False
        self._port = f"Wi-Fi {host}:{WIFI_PORT}"
        self._status = "live"
        self._last_error = None
        return True

    def _read_line(self) -> bytes:
        with self._lock:
            source = self._source
            serial_port = self._serial
            wifi_file = self._wifi_file
        if source == "usb":
            return serial_port.readline()
        return wifi_file.readline()

    def _run(self) -> None:
        while not self._stop_event.is_set():
            with self._lock:
                connected = self._ensure_connection_locked()
            if not connected:
                if self._stop_event.wait(RECONNECT_INTERVAL_S):
                    return
                continue
            try:
                line = self._read_line()
            except Exception as exc:
                with self._lock:
                    self._close_connection_locked()
                    self._status = "reconnecting"
                    self._last_error = f"读取失败：{exc}，正在尝试重新连接。"
                if self._stop_event.wait(RECONNECT_INTERVAL_S):
                    return
                continue
            if not line:
                with self._lock:
                    if (
                        self._status == "live"
                        and self._last_sample_at is not None
                        and time.monotonic() - self._last_sample_at > OFFLINE_AFTER_S
                    ):
                        self._close_connection_locked()
                        self._status = "reconnecting"
                        self._last_error = "超过 3 秒没有收到数据，正在尝试重新连接。"
                continue
            text = line.decode("utf-8", errors="ignore").strip()
            parsed = parse_sample_line(text)
            if parsed is None:
                self._handle_info_line(text)
                continue
            t_ms, values = parsed
            with self._lock:
                self._buffer.append((t_ms, values))
                self._cursor += 1
                self._last_sample_at = time.monotonic()
                if self._status != "live":
                    self._status = "live"
                    self._last_error = None

    def _handle_info_line(self, text: str) -> None:
        if not text.startswith("#"):
            return
        if text.startswith("#DEV:"):
            info: dict[str, Any] = {}
            for pair in text[5:].split(";"):
                if "=" not in pair:
                    continue
                key, _, value = pair.partition("=")
                key = key.strip()
                value = value.strip()
                if key in {"bat", "chg", "sta", "ap"}:
                    try:
                        info[key] = int(value)
                    except ValueError:
                        continue
                elif key == "ip":
                    info[key] = value
            if info:
                with self._lock:
                    self._device.update(info)
        elif text.startswith("#STA:OK ip="):
            with self._lock:
                self._device["sta"] = 1
                self._device["ip"] = text.split("ip=", 1)[1].strip()
        elif text.startswith("#WIFI:AP"):
            with self._lock:
                self._device["ap"] = 1
        elif text.startswith("#WIFI:OFF") or text.startswith("#WIFI:FAIL"):
            with self._lock:
                self._device["ap"] = 0

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
        try:
            self._push_device_text(result)
        except Exception:  # pragma: no cover - 推送失败不影响网页结果
            pass
        with self._lock:
            self._analysis_cache = (now, result)
        return result

    def _push_device_text(self, result: dict[str, Any]) -> None:
        if result.get("status") != "COMPLETED":
            if self._pushed_text != "分析中":
                self.send_command("#STATUS:分析中")
                self._pushed_text = "分析中"
            return
        fall = result.get("fall", {})
        candidates = (
            int(fall.get("candidate_count") or 0)
            if fall.get("status") == "COMPLETED"
            else 0
        )
        activity = result.get("activity", {})
        label = (
            activity.get("label")
            if activity.get("status") == "COMPLETED"
            else "滚动分析"
        )
        if candidates:
            text = f"跌倒候选 {candidates} 个"
            if not self._alert_active or text != self._pushed_text:
                self.send_command(f"#TEXT:{text}")
                self.send_command("#VIB:1")
                self._alert_active = True
                self._pushed_text = text
            return
        if self._alert_active:
            self.send_command("#TEXT:")
            self.send_command("#VIB:0")
            self._alert_active = False
        text = f"{label} · 无跌倒候选"
        if text != self._pushed_text:
            self.send_command(f"#STATUS:{text}")
            self._pushed_text = text

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
