r"""通过 Wi-Fi 热点读取 M5StickS3 六轴数据流并保存为采集文件。

使用前提：
1. 手表已烧录 firmware/m5sticks3_imu_stream（v2）；
2. 单击手表正面按钮打开 WiFi（屏幕显示 HealthWatch 与 192.168.4.1）；
3. 电脑连接到名为 HealthWatch 的网络（密码 healthwatch）；
4. 运行： .\.venv\Scripts\python.exe tools\watch_wifi_receiver.py --seconds 30 --name P01-走路-01

结束后生成 data/raw/watch/wifi-<时间>.csv，格式与串口录制一致（time_s,ax,ay,az,gx,gy,gz），
可继续交给“新数据检测”或 import_watch_serial.py 使用。
"""
from __future__ import annotations

import argparse
import json
import socket
import sys
import time
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = PROJECT_ROOT / "data" / "raw" / "watch"
TARGET_PATH = OUTPUT_DIR / "wifi_target.json"
DEFAULT_HOST = "192.168.4.1"
WATCH_PORT = 5005
G_TO_MS2 = 9.80665
DEG_TO_RAD = 0.017453292519943295


def canonical_values(raw: list[float]) -> list[float]:
    """把手表原始单位（g、deg/s）换算为项目标准单位（m/s²、rad/s）。"""
    return [
        raw[0] * G_TO_MS2,
        raw[1] * G_TO_MS2,
        raw[2] * G_TO_MS2,
        raw[3] * DEG_TO_RAD,
        raw[4] * DEG_TO_RAD,
        raw[5] * DEG_TO_RAD,
    ]


def resolve_host() -> str:
    try:
        payload = json.loads(TARGET_PATH.read_text(encoding="utf-8"))
        host = str(payload.get("ip", "")).strip()
        return host or DEFAULT_HOST
    except (OSError, ValueError):
        return DEFAULT_HOST


def main() -> None:
    parser = argparse.ArgumentParser(description="通过 Wi-Fi 保存手表六轴数据。")
    parser.add_argument("--seconds", type=float, default=30.0, help="录制秒数，默认 30")
    parser.add_argument("--name", default="", help="记录名字，写入文件名便于辨认")
    parser.add_argument("--host", default=None, help="手表地址，默认读取 wifi_target.json")
    parser.add_argument("--port", type=int, default=WATCH_PORT)
    args = parser.parse_args()

    host = args.host or resolve_host()
    sys.stdout.write(f"正在连接手表 {host}:{args.port} …\n")
    try:
        connection = socket.create_connection((host, args.port), timeout=5.0)
    except OSError as error:
        raise SystemExit(
            f"连接失败：{error}\n请先运行 scripts\\windows\\connect-watch-wifi.cmd 完成一次配对。"
        )
    sys.stdout.write("已连接，开始读取。\n")

    samples: list[tuple[int, list[float]]] = []
    deadline = time.monotonic() + args.seconds
    buffer = b""
    connection.settimeout(5.0)
    try:
        while time.monotonic() < deadline:
            try:
                chunk = connection.recv(4096)
            except socket.timeout:
                sys.stdout.write("\n连接停滞（手表可能走远或热点不稳定），提前结束。\n")
                break
            if not chunk:
                break
            buffer += chunk
            while b"\n" in buffer:
                line, buffer = buffer.split(b"\n", 1)
                text = line.decode("ascii", errors="ignore").strip()
                parts = text.split(",")
                if len(parts) != 7 or not parts[0].isdigit():
                    continue
                try:
                    raw_values = [float(value) for value in parts[1:]]
                except ValueError:
                    continue
                samples.append((int(parts[0]), canonical_values(raw_values)))
            done = args.seconds - (deadline - time.monotonic())
            sys.stdout.write(f"\r已读取 {len(samples)} 个样本（{done:.1f} 秒）")
            sys.stdout.flush()
    except KeyboardInterrupt:
        sys.stdout.write("\n收到中断，提前结束。\n")
    finally:
        connection.close()

    sys.stdout.write("\n")
    if len(samples) < 100:
        raise SystemExit("样本不足 2 秒，未保存。请检查手表 WiFi 连接后重试。")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    suffix = f"-{args.name}" if args.name else ""
    output_path = OUTPUT_DIR / f"wifi-{stamp}{suffix}.csv"
    first_t_ms = samples[0][0]
    lines = ["time_s,ax,ay,az,gx,gy,gz"]
    for t_ms, values in samples:
        seconds = (t_ms - first_t_ms) / 1000.0
        if seconds < 0:
            continue
        lines.append(f"{seconds:.3f}," + ",".join(f"{value:.4f}" for value in values))
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    duration_s = (samples[-1][0] - first_t_ms) / 1000.0
    rate = (len(samples) - 1) / duration_s if duration_s > 0 else 0.0
    sys.stdout.write(
        f"已保存 {len(samples)} 个样本（{duration_s:.1f} 秒，约 {rate:.1f} 次/秒）到 "
        f"{output_path.relative_to(PROJECT_ROOT)}\n"
    )


if __name__ == "__main__":
    main()
