r"""让手表连接指定 Wi-Fi 网络（例如手机热点），为免插线实时做准备。

用法（手表需先用数据线连接电脑一次）：
    .\.venv\Scripts\python.exe tools\watch_join_wifi.py --ssid "手机热点名" --password "密码"

成功后手表会记住本次连接（直到断电重启），并把地址写入
data/raw/watch/wifi_target.json，工作台的“Wi-Fi 无线”来源会自动使用该地址。
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import serial
from serial.tools import list_ports

PROJECT_ROOT = Path(__file__).resolve().parents[1]
TARGET_PATH = PROJECT_ROOT / "data" / "raw" / "watch" / "wifi_target.json"
WATCH_VID = 0x303A


def find_watch_port() -> str | None:
    candidates = [item for item in list_ports.comports() if item.vid == WATCH_VID]
    candidates.sort(key=lambda item: 0 if item.pid == 0x1001 else 1)
    return candidates[0].device if candidates else None


def main() -> None:
    parser = argparse.ArgumentParser(description="让手表连接指定 Wi-Fi 网络。")
    parser.add_argument("--ssid", required=True, help="Wi-Fi 名称（手机热点名）")
    parser.add_argument("--password", required=True, help="Wi-Fi 密码")
    args = parser.parse_args()

    port = find_watch_port()
    if port is None:
        raise SystemExit("没有找到手表串口，请先用手表数据线连接电脑。")
    print(f"使用串口 {port}，正在让手表连接 “{args.ssid}” …")

    address: str | None = None
    with serial.Serial(port, 115200, timeout=1.0) as connection:
        time.sleep(0.5)
        connection.read_all()
        command = f"#STA:{args.ssid}|{args.password}\n"
        connection.write(command.encode("utf-8"))
        deadline = time.monotonic() + 25.0
        while time.monotonic() < deadline:
            raw = connection.readline()
            if not raw:
                continue
            line = raw.decode("utf-8", errors="ignore").strip()
            if not line.startswith("#STA:"):
                continue
            print("手表回复：", line)
            if "OK ip=" in line:
                address = line.split("ip=", 1)[1].strip()
                break
            if "FAIL" in line:
                break

    if not address:
        raise SystemExit("连接没有成功：请确认热点名称与密码，并确认手机热点允许设备互相访问。")

    TARGET_PATH.parent.mkdir(parents=True, exist_ok=True)
    TARGET_PATH.write_text(
        json.dumps({"ssid": args.ssid, "ip": address}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"连接成功：{args.ssid} → 手表地址 {address}")
    print("可以拔掉数据线；在工作台“手表实时”里把数据来源改为“Wi-Fi 无线”即可。")
    print(f"（地址已写入 {TARGET_PATH.relative_to(PROJECT_ROOT)}）")


if __name__ == "__main__":
    main()
