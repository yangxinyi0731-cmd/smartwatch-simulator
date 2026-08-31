@echo off
setlocal
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0stop-early-risk-workbench.ps1"
pause
endlocal
