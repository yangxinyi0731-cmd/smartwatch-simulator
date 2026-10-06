@echo off
chcp 65001 > nul
setlocal
set /p SSID=请输入 Wi-Fi 名称（手机热点名）:
set /p PASS=请输入 Wi-Fi 密码:
"%~dp0..\..\.venv\Scripts\python.exe" "%~dp0..\..\tools\watch_join_wifi.py" --ssid "%SSID%" --password "%PASS%"
pause
