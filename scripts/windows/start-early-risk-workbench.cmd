@echo off
setlocal
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0start-early-risk-workbench.ps1"
if errorlevel 1 pause
endlocal
