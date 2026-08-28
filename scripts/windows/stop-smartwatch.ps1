[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$projectRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$statePath = Join-Path $projectRoot 'backend\runtime\local-delivery\server-state.json'

if (-not (Test-Path -LiteralPath (Join-Path $projectRoot 'backend\app\main.py') -PathType Leaf)) {
    throw "项目目录校验失败：$projectRoot"
}
if (-not (Test-Path -LiteralPath $statePath -PathType Leaf)) {
    Write-Host '平台当前没有由一键脚本启动的运行进程。' -ForegroundColor Yellow
    exit 0
}

$state = Get-Content -LiteralPath $statePath -Raw -Encoding UTF8 | ConvertFrom-Json
try {
    $process = Get-Process -Id ([int]$state.pid) -ErrorAction Stop
}
catch {
    Remove-Item -LiteralPath $statePath -Force
    Write-Host '平台进程已经结束，旧运行状态已清理。' -ForegroundColor Yellow
    exit 0
}

$actualPath = [IO.Path]::GetFullPath($process.Path)
$expectedPath = [IO.Path]::GetFullPath([string]$state.process_path)
$actualStart = $process.StartTime.ToUniversalTime().ToString('o')
if ($actualPath -ne $expectedPath -or $actualStart -ne [string]$state.process_start_time_utc) {
    throw '运行状态中的进程标识已被其他程序复用；为避免误停其他程序，已拒绝执行。'
}

Stop-Process -Id $process.Id -ErrorAction Stop
Wait-Process -Id $process.Id -Timeout 10 -ErrorAction SilentlyContinue
if (Get-Process -Id $process.Id -ErrorAction SilentlyContinue) {
    Stop-Process -Id $process.Id -Force -ErrorAction Stop
}
Remove-Item -LiteralPath $statePath -Force
Write-Host '模拟智能手表平台已停止。SQLite 数据与日志均保留。' -ForegroundColor Green
