# -*- coding: utf-8 -*-
"""从 M5StickS3 读取六轴数据流，保存为标准 CSV（time_s,ax,ay,az,gx,gy,gz）。"""
import csv
import math
import re
import sys
import time
from datetime import datetime
from pathlib import Path

import serial
from serial.tools import list_ports

ACCEL_TO_MPS2 = 9.80665
GYRO_TO_RADS = math.pi / 180.0
DEFAULT_SECONDS = 30
REPO = Path(__file__).resolve().parent.parent
OUT_DIR = REPO / "data" / "raw" / "watch"

LINE_RE = re.compile(
    r"^(\d+),(-?\d+\.?\d*),(-?\d+\.?\d*),(-?\d+\.?\d*),"
    r"(-?\d+\.?\d*),(-?\d+\.?\d*),(-?\d+\.?\d*)$"
)


def find_watch_port():
    candidates = [p for p in list_ports.comports() if p.vid == 0x303A]
    candidates.sort(key=lambda p: 0 if p.pid == 0x1001 else 1)
    for p in candidates:
        try:
            s = serial.Serial(p.device, 115200, timeout=1)
        except Exception:
            continue
        deadline = time.time() + 3
        while time.time() < deadline:
            line = s.readline().decode("ascii", errors="ignore").strip()
            if LINE_RE.match(line):
                s.close()
                return p.device
        s.close()
    return None


def ask(prompt, default):
    try:
        value = input(prompt).strip()
    except EOFError:
        return default
    return value if value else default


def main():
    print("=" * 52)
    print("模拟手表 · 动作数据采集")
    print("=" * 52)
    print("正在寻找手表串口……")
    port = find_watch_port()
    if port is None:
        print("没有找到手表。请确认：")
        print("  1) 手表已经用 USB 线接在电脑上，屏幕在闪动计数")
        print("  2) Arduino IDE 的串口监视器已经关闭")
        sys.exit(1)
    print(f"已找到手表：{port}")
    name = ask("给这次记录起个名字（例如 P01-走路-01，直接回车自动命名）: ", "")
    if not name:
        name = "记录-" + datetime.now().strftime("%Y%m%d-%H%M%S")
    name = name.replace("/", "-").replace("\\", "-").strip()
    secs_raw = ask(f"这次记录多少秒？（直接回车默认 {DEFAULT_SECONDS} 秒）: ", str(DEFAULT_SECONDS))
    try:
        seconds = max(1, min(600, int(float(secs_raw))))
    except ValueError:
        seconds = DEFAULT_SECONDS

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / f"{name}.csv"

    print()
    for i in (3, 2, 1):
        print(f"{i} 秒后开始……")
        time.sleep(1)
    print("开始！请做动作。")

    ser = serial.Serial(port, 115200, timeout=1)
    drain_until = time.time() + 0.3
    while time.time() < drain_until:
        ser.readline()
    rows = []
    skipped = 0
    t0 = None
    t_end = time.time() + seconds
    last_print = time.time()
    try:
        while time.time() < t_end:
            line = ser.readline().decode("ascii", errors="ignore").strip()
            if not line:
                continue
            m = LINE_RE.match(line)
            if not m:
                skipped += 1
                continue
            t_ms = int(m.group(1))
            if t0 is None:
                t0 = t_ms
            dt = (t_ms - t0) / 1000.0
            rows.append((
                dt,
                float(m.group(2)) * ACCEL_TO_MPS2,
                float(m.group(3)) * ACCEL_TO_MPS2,
                float(m.group(4)) * ACCEL_TO_MPS2,
                float(m.group(5)) * GYRO_TO_RADS,
                float(m.group(6)) * GYRO_TO_RADS,
                float(m.group(7)) * GYRO_TO_RADS,
            ))
            now = time.time()
            if now - last_print >= 5:
                last_print = now
                print(f"  已记录 {len(rows)} 个点（{dt:.1f} 秒）……")
    except KeyboardInterrupt:
        print("提前结束记录。")
    except serial.SerialException as exc:
        print(f"串口断开：{exc}")
    finally:
        ser.close()

    if not rows:
        print("没有收到任何数据，请把这句话告诉助手。")
        sys.exit(1)

    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["time_s", "ax", "ay", "az", "gx", "gy", "gz"])
        for r in rows:
            writer.writerow([f"{r[0]:.3f}"] + [f"{v:.4f}" for v in r[1:]])

    dur = rows[-1][0] - rows[0][0]
    rate = (len(rows) - 1) / dur if dur > 0 else 0.0
    print()
    print("=" * 52)
    print("保存完成")
    print(f"  文件：{out_path}")
    print(f"  点数：{len(rows)}")
    print(f"  时长：{dur:.1f} 秒")
    print(f"  实际采样率：约 {rate:.1f} 次/秒（目标 50）")
    if skipped:
        print(f"  忽略的异常行：{skipped}")
    print("=" * 52)
    try:
        input("按回车键关闭这个窗口。")
    except EOFError:
        pass


if __name__ == "__main__":
    main()
