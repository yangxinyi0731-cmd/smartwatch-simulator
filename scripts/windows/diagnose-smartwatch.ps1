[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Continue'

$projectRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$pythonPath = Join-Path $projectRoot '.venv\Scripts\python.exe'
$databasePath = if ($env:SMARTWATCH_DATABASE_PATH) {
    $env:SMARTWATCH_DATABASE_PATH
}
else {
    Join-Path $projectRoot 'backend\runtime\smartwatch.sqlite3'
}
$statePath = Join-Path $projectRoot 'backend\runtime\local-delivery\server-state.json'
$checks = [Collections.Generic.List[object]]::new()
$failed = $false

function Add-Check {
    param(
        [string]$Name,
        [ValidateSet('通过', '警告', '失败')][string]$Status,
        [string]$Detail
    )
    $script:checks.Add([pscustomobject]@{
        检查项 = $Name
        状态 = $Status
        说明 = $Detail
    })
    if ($Status -eq '失败') {
        $script:failed = $true
    }
}

if (Test-Path -LiteralPath (Join-Path $projectRoot 'backend\app\main.py') -PathType Leaf) {
    Add-Check '项目目录' '通过' $projectRoot
}
else {
    Add-Check '项目目录' '失败' "目录内容不完整：$projectRoot"
}

if (Test-Path -LiteralPath $pythonPath -PathType Leaf) {
    $pythonVersion = (& $pythonPath --version 2>&1) -join ' '
    Add-Check 'Python 虚拟环境' '通过' $pythonVersion
    $pipCheck = (& $pythonPath -m pip check 2>&1) -join ' '
    if ($LASTEXITCODE -eq 0) {
        Add-Check 'Python 依赖' '通过' $pipCheck
    }
    else {
        Add-Check 'Python 依赖' '失败' $pipCheck
    }
}
else {
    Add-Check 'Python 虚拟环境' '失败' '缺少 .venv\Scripts\python.exe'
}

$nodeCommand = Get-Command node.exe -ErrorAction SilentlyContinue
$npmCommand = Get-Command npm.cmd -ErrorAction SilentlyContinue
if ($null -ne $nodeCommand -and $null -ne $npmCommand) {
    Add-Check 'Node.js 与 npm' '通过' "node $(& $nodeCommand.Source --version)，npm $(& $npmCommand.Source --version)"
}
else {
    Add-Check 'Node.js 与 npm' '失败' '缺少 node.exe 或 npm.cmd，无法重新构建前端。'
}

$frontendIndex = Join-Path $projectRoot 'frontend\dist\index.html'
if (Test-Path -LiteralPath $frontendIndex -PathType Leaf) {
    Add-Check '前端生产构建' '通过' $frontendIndex
}
else {
    Add-Check '前端生产构建' '警告' '尚未生成；启动脚本会自动执行 npm build。'
}

if ([IO.Path]::IsPathRooted($databasePath) -and (Test-Path -LiteralPath $databasePath -PathType Leaf)) {
    Add-Check 'SQLite 数据库' '通过' ([IO.Path]::GetFullPath($databasePath))
}
elseif (-not [IO.Path]::IsPathRooted($databasePath)) {
    Add-Check 'SQLite 数据库' '失败' 'SMARTWATCH_DATABASE_PATH 不是绝对路径。'
}
else {
    Add-Check 'SQLite 数据库' '警告' "数据库尚不存在：$databasePath"
}

$requiredAssets = @(
    'models\fall_detector\tcn_final_candidate\model.onnx',
    'models\routine_anomaly\statistical_v1\rules.json',
    'models\activity_recognition\capture24_linear_v1\model.onnx'
)
$missingAssets = @($requiredAssets | Where-Object {
    -not (Test-Path -LiteralPath (Join-Path $projectRoot $_) -PathType Leaf)
})
if ($missingAssets.Count -eq 0) {
    Add-Check '三个模型资产' '通过' '跌倒 ONNX、规律规则和活动 ONNX 均存在。'
}
else {
    Add-Check '三个模型资产' '失败' ("缺少：" + ($missingAssets -join '，'))
}

try {
    $health = Invoke-RestMethod -Uri 'http://127.0.0.1:8000/api/health' -TimeoutSec 3
    if ($health.service.state -eq 'ready' -and $health.database.state -eq 'ready') {
        Add-Check '本机运行服务' '通过' "v$($health.service.version)，结构版本 $($health.database.schema_version)，案例 $($health.cases.count) 个"
    }
    else {
        Add-Check '本机运行服务' '失败' $health.message
    }
}
catch {
    if (Test-Path -LiteralPath $statePath -PathType Leaf) {
        Add-Check '本机运行服务' '失败' '存在运行状态文件，但健康检查不可达；请先停止再启动。'
    }
    else {
        Add-Check '本机运行服务' '警告' '当前未启动；可双击 start-smartwatch.cmd。'
    }
}

Write-Host ''
Write-Host '模拟智能手表平台诊断结果' -ForegroundColor Cyan
$checks | Format-Table -AutoSize -Wrap
if ($failed) {
    Write-Host '诊断发现必须修复的问题。' -ForegroundColor Red
    exit 1
}
Write-Host '未发现阻止本机运行的问题。' -ForegroundColor Green
exit 0
