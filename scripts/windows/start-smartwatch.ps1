[CmdletBinding()]
param(
    [switch]$NoBrowser,
    [switch]$SkipBuild
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$projectRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$pythonPath = Join-Path $projectRoot '.venv\Scripts\python.exe'
$frontendPackage = Join-Path $projectRoot 'frontend\package.json'
$frontendIndex = Join-Path $projectRoot 'frontend\dist\index.html'
$runtimeDirectory = Join-Path $projectRoot 'backend\runtime\local-delivery'
$statePath = Join-Path $runtimeDirectory 'server-state.json'
$stdoutPath = Join-Path $runtimeDirectory 'server.stdout.log'
$stderrPath = Join-Path $runtimeDirectory 'server.stderr.log'
$url = 'http://127.0.0.1:8000/'

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

if (-not (Test-Path -LiteralPath (Join-Path $projectRoot 'backend\app\main.py') -PathType Leaf)) {
    throw "项目目录校验失败：$projectRoot"
}
if (-not (Test-Path -LiteralPath $pythonPath -PathType Leaf)) {
    throw '缺少 Python 虚拟环境。请先按 README 的“首次安装”执行依赖安装。'
}
if (-not (Test-Path -LiteralPath $frontendPackage -PathType Leaf)) {
    throw '缺少 frontend/package.json，无法构建前端。'
}

New-Item -ItemType Directory -Path $runtimeDirectory -Force | Out-Null

if (Test-Path -LiteralPath $statePath -PathType Leaf) {
    try {
        $existingState = Get-Content -LiteralPath $statePath -Raw -Encoding UTF8 | ConvertFrom-Json
        if (Test-RecordedProcess -State $existingState) {
            Write-Host "平台已经运行：$($existingState.url)" -ForegroundColor Green
            if (-not $NoBrowser) {
                Start-Process -FilePath ([string]$existingState.url)
            }
            exit 0
        }
    }
    catch {
        Write-Warning '发现无法读取的旧运行状态，将只清理该状态文件。'
    }
    Remove-Item -LiteralPath $statePath -Force
}

if ($env:SMARTWATCH_DATABASE_PATH) {
    if (-not [IO.Path]::IsPathRooted($env:SMARTWATCH_DATABASE_PATH)) {
        throw 'SMARTWATCH_DATABASE_PATH 必须是绝对路径。'
    }
    $databasePath = [IO.Path]::GetFullPath($env:SMARTWATCH_DATABASE_PATH)
}
else {
    $databasePath = Join-Path $projectRoot 'backend\runtime\smartwatch.sqlite3'
}
$env:SMARTWATCH_DATABASE_PATH = $databasePath

if (-not $SkipBuild) {
    $npmCommand = Get-Command npm.cmd -ErrorAction SilentlyContinue
    if ($null -eq $npmCommand) {
        throw '未找到 npm。请先安装 Node.js，再按 README 完成首次安装。'
    }
    Write-Host '正在检查并构建前端……' -ForegroundColor Cyan
    Push-Location $projectRoot
    try {
        & $npmCommand.Source --prefix frontend run build
        if ($LASTEXITCODE -ne 0) {
            throw "前端构建失败，退出码：$LASTEXITCODE"
        }
    }
    finally {
        Pop-Location
    }
}

if (-not (Test-Path -LiteralPath $frontendIndex -PathType Leaf)) {
    throw '未找到 frontend/dist/index.html。请不要使用 -SkipBuild，或先完成前端构建。'
}
if (Test-LocalPort -Port 8000) {
    throw '本机端口 8000 已被其他程序占用。请先关闭占用程序，再重新启动。'
}

Write-Host '正在启动仅限本机访问的平台服务……' -ForegroundColor Cyan
$process = Start-Process `
    -FilePath $pythonPath `
    -ArgumentList @('-m', 'uvicorn', 'backend.app.main:app', '--host', '127.0.0.1', '--port', '8000') `
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
    database_path = $databasePath
    url = $url
}
$state | ConvertTo-Json | Set-Content -LiteralPath $statePath -Encoding UTF8

$health = $null
$deadline = [DateTime]::UtcNow.AddSeconds(30)
while ([DateTime]::UtcNow -lt $deadline) {
    if ($process.HasExited) {
        break
    }
    try {
        $health = Invoke-RestMethod -Uri 'http://127.0.0.1:8000/api/health' -TimeoutSec 2
        if ($health.service.state -eq 'ready' -and $health.database.state -eq 'ready') {
            break
        }
    }
    catch {
        Start-Sleep -Milliseconds 300
    }
}

if ($null -eq $health -or $health.service.state -ne 'ready' -or $health.database.state -ne 'ready') {
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
    throw "平台未能在 30 秒内就绪。诊断信息：`n$lastError"
}

Write-Host "平台已就绪：$url" -ForegroundColor Green
Write-Host "案例：$($health.cases.count) 个；数据库结构版本：$($health.database.schema_version)" -ForegroundColor Green
Write-Host '可双击 stop-smartwatch.cmd 停止；遇到问题可双击 diagnose-smartwatch.cmd。'
if (-not $NoBrowser) {
    Start-Process -FilePath $url
}
