[CmdletBinding()]
param(
    [switch]$NoBrowser
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$projectRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$pythonPath = Join-Path $projectRoot '.venv\Scripts\python.exe'
$serverModulePath = Join-Path $projectRoot 'research\early_risk\workbench_server.py'
$workbenchIndex = Join-Path $projectRoot 'research\early_risk\workbench\index.html'
$runtimeDirectory = Join-Path $projectRoot 'backend\runtime\early-risk-workbench'
$statePath = Join-Path $runtimeDirectory 'server-state.json'
$stdoutPath = Join-Path $runtimeDirectory 'server.stdout.log'
$stderrPath = Join-Path $runtimeDirectory 'server.stderr.log'
$url = 'http://127.0.0.1:8010/'

function Test-LocalPort {
    param([int]$Port)

    $client = [Net.Sockets.TcpClient]::new()
    try {
        $client.Connect('127.0.0.1', $Port)
        return $true
    }
    catch {
        return $false
    }
    finally {
        $client.Dispose()
    }
}

function Test-RecordedProcess {
    param([object]$State)

    try {
        $process = Get-Process -Id ([int]$State.pid) -ErrorAction Stop
        $actualPath = [IO.Path]::GetFullPath($process.Path)
        $expectedPath = [IO.Path]::GetFullPath([string]$State.process_path)
        $actualStart = $process.StartTime.ToUniversalTime().ToString('o')
        return ($actualPath -eq $expectedPath -and $actualStart -eq [string]$State.process_start_time_utc)
    }
    catch {
        return $false
    }
}

if (-not (Test-Path -LiteralPath $serverModulePath -PathType Leaf)) {
    throw "项目目录校验失败：$projectRoot"
}
if (-not (Test-Path -LiteralPath $workbenchIndex -PathType Leaf)) {
    throw '缺少研究工作台静态资源。'
}
if (-not (Test-Path -LiteralPath $pythonPath -PathType Leaf)) {
    throw '缺少 Python 虚拟环境。请先按 README 的“首次安装”执行依赖安装。'
}

New-Item -ItemType Directory -Path $runtimeDirectory -Force | Out-Null

if (Test-Path -LiteralPath $statePath -PathType Leaf) {
    try {
        $existingState = Get-Content -LiteralPath $statePath -Raw -Encoding UTF8 | ConvertFrom-Json
        if (Test-RecordedProcess -State $existingState) {
            $health = Invoke-RestMethod -Uri 'http://127.0.0.1:8010/api/health' -TimeoutSec 3
            if ($health.state -eq 'ready') {
                Write-Host "E0 研究工作台已经运行：$($existingState.url)" -ForegroundColor Green
                if (-not $NoBrowser) {
                    Start-Process -FilePath ([string]$existingState.url)
                }
                exit 0
            }
        }
    }
    catch {
        Write-Warning '发现无法复用的旧运行状态，将只清理该状态文件。'
    }
    Remove-Item -LiteralPath $statePath -Force
}

if (Test-LocalPort -Port 8010) {
    throw '本机端口 8010 已被其他程序占用。请先关闭占用程序，再重新启动。'
}

Write-Host '正在启动仅限本机访问的 E0 提前风险研究工作台……' -ForegroundColor Cyan
$env:PYTHONIOENCODING = 'utf-8'
$process = Start-Process `
    -FilePath $pythonPath `
    -ArgumentList @('-m', 'research.early_risk.workbench_server', '--host', '127.0.0.1', '--port', '8010') `
    -WorkingDirectory $projectRoot `
    -RedirectStandardOutput $stdoutPath `
    -RedirectStandardError $stderrPath `
    -WindowStyle Hidden `
    -PassThru
$process.Refresh()

$state = [ordered]@{
    pid = $process.Id
    process_path = $process.Path
    process_start_time_utc = $process.StartTime.ToUniversalTime().ToString('o')
    started_at_utc = [DateTime]::UtcNow.ToString('o')
    project_root = $projectRoot
    url = $url
    evidence_level = 'E0'
    external_notifications_enabled = $false
}
$state | ConvertTo-Json | Set-Content -LiteralPath $statePath -Encoding UTF8

$health = $null
$deadline = [DateTime]::UtcNow.AddSeconds(30)
while ([DateTime]::UtcNow -lt $deadline) {
    if ($process.HasExited) {
        break
    }
    try {
        $health = Invoke-RestMethod -Uri 'http://127.0.0.1:8010/api/health' -TimeoutSec 2
        if ($health.state -eq 'ready') {
            break
        }
    }
    catch {
        Start-Sleep -Milliseconds 300
    }
}

if ($null -eq $health -or $health.state -ne 'ready') {
    if (-not $process.HasExited) {
        Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue
    }
    Remove-Item -LiteralPath $statePath -Force -ErrorAction SilentlyContinue
    $lastError = if (Test-Path -LiteralPath $stderrPath) {
        (Get-Content -LiteralPath $stderrPath -Tail 20) -join [Environment]::NewLine
    }
    else {
        '未生成错误日志。'
    }
    throw "工作台未能在 30 秒内就绪。诊断信息：`n$lastError"
}

if ($health.bind_scope -ne 'loopback_only' -or $health.evidence_level -ne 'E0' -or $health.external_notifications_enabled) {
    Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue
    Remove-Item -LiteralPath $statePath -Force -ErrorAction SilentlyContinue
    throw '工作台安全边界检查失败，已停止启动。'
}

Write-Host "E0 研究工作台已就绪：$url" -ForegroundColor Green
Write-Host '范围：仅本机、确定性夹具、prediction_evidence=false、外部通知关闭。' -ForegroundColor Green
Write-Host '可双击 stop-early-risk-workbench.cmd 停止；遇到问题可双击 diagnose-early-risk-workbench.cmd。'
if (-not $NoBrowser) {
    Start-Process -FilePath $url
}
