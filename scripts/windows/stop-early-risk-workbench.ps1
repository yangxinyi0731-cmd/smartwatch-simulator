[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$projectRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$statePath = Join-Path $projectRoot 'backend\runtime\early-risk-workbench\server-state.json'

if (-not (Test-Path -LiteralPath (Join-Path $projectRoot 'research\early_risk\workbench_server.py') -PathType Leaf)) {
    throw "项目目录校验失败：$projectRoot"
}
if (-not (Test-Path -LiteralPath $statePath -PathType Leaf)) {
    Write-Host '校赛风险研究工作台当前没有由一键脚本记录的运行进程。' -ForegroundColor Yellow
    exit 0
}

$state = Get-Content -LiteralPath $statePath -Raw -Encoding UTF8 | ConvertFrom-Json
try {
    $process = Get-Process -Id ([int]$state.pid) -ErrorAction Stop
}
catch {
    Remove-Item -LiteralPath $statePath -Force
    Write-Host '工作台进程已经结束，旧运行状态已清理。' -ForegroundColor Yellow
    exit 0
}

$actualPath = [IO.Path]::GetFullPath($process.Path)
$expectedPath = [IO.Path]::GetFullPath([string]$state.process_path)
$actualStartTicks = $process.StartTime.ToUniversalTime().Ticks
$expectedStartTicks = if ($null -ne $state.PSObject.Properties['process_start_time_utc_ticks']) {
    [long]$state.process_start_time_utc_ticks
}
else {
    ([DateTime]$state.process_start_time_utc).ToUniversalTime().Ticks
}
if ($actualPath -ne $expectedPath -or $actualStartTicks -ne $expectedStartTicks) {
    throw '运行状态中的进程标识已被其他程序复用；为避免误停其他程序，已拒绝执行。'
}

Stop-Process -Id $process.Id -ErrorAction Stop
Wait-Process -Id $process.Id -Timeout 10 -ErrorAction SilentlyContinue
if (Get-Process -Id $process.Id -ErrorAction SilentlyContinue) {
    Stop-Process -Id $process.Id -Force -ErrorAction Stop
}
Remove-Item -LiteralPath $statePath -Force
Write-Host '校赛风险研究工作台已停止。合同、报告和日志均保留。' -ForegroundColor Green
