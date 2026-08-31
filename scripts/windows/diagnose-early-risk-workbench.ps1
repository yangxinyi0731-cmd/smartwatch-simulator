[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Continue'

$projectRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$pythonPath = Join-Path $projectRoot '.venv\Scripts\python.exe'
$statePath = Join-Path $projectRoot 'backend\runtime\early-risk-workbench\server-state.json'
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

$requiredFiles = @(
    'research\early_risk\workbench_server.py',
    'research\early_risk\workbench\index.html',
    'research\early_risk\workbench\app.css',
    'research\early_risk\workbench\app.js',
    'configs\early_risk\target_contract.v1.yaml',
    'reports\early_risk\e0\p0_p2_gate_summary.json',
    'reports\early_risk\e0\fixture_benchmark.json',
    'reports\early_risk\e0\current_data_audit.json'
)
$missingFiles = @($requiredFiles | Where-Object {
    -not (Test-Path -LiteralPath (Join-Path $projectRoot $_) -PathType Leaf)
})
if ($missingFiles.Count -eq 0) {
    Add-Check '工作台与 E0 证据文件' '通过' "$($requiredFiles.Count) 个必需文件均存在。"
}
else {
    Add-Check '工作台与 E0 证据文件' '失败' ("缺少：" + ($missingFiles -join '，'))
}

if (Test-Path -LiteralPath $pythonPath -PathType Leaf) {
    $pythonVersion = (& $pythonPath --version 2>&1) -join ' '
    Add-Check 'Python 虚拟环境' '通过' $pythonVersion
    $contractCheck = (& $pythonPath -c "from research.early_risk.workbench_server import build_workbench_payload, simulate_policy; p=build_workbench_payload(); s=simulate_policy({}); assert p['meta']['evidence_level']=='E0'; assert p['meta']['prediction_evidence'] is False; assert s['summary']['external_notification_count']==0; print('E0 contract and dry-run safety boundary passed')" 2>&1) -join ' '
    if ($LASTEXITCODE -eq 0) {
        Add-Check '证据与安全边界' '通过' $contractCheck
    }
    else {
        Add-Check '证据与安全边界' '失败' $contractCheck
    }
}
else {
    Add-Check 'Python 虚拟环境' '失败' '缺少 .venv\Scripts\python.exe'
}

try {
    $health = Invoke-RestMethod -Uri 'http://127.0.0.1:8010/api/health' -TimeoutSec 3
    if ($health.state -eq 'ready' -and $health.bind_scope -eq 'loopback_only' -and -not $health.external_notifications_enabled) {
        Add-Check '本机运行服务' '通过' '127.0.0.1:8010，E0，外部通知关闭。'
    }
    else {
        Add-Check '本机运行服务' '失败' '服务响应存在，但安全边界状态不符合 E0 合同。'
    }
}
catch {
    if (Test-Path -LiteralPath $statePath -PathType Leaf) {
        Add-Check '本机运行服务' '失败' '存在运行状态文件，但健康检查不可达；请先停止再启动。'
    }
    else {
        Add-Check '本机运行服务' '警告' '当前未启动；可双击 start-early-risk-workbench.cmd。'
    }
}

Write-Host ''
Write-Host 'E0 提前风险研究工作台诊断结果' -ForegroundColor Cyan
$checks | Format-Table -AutoSize -Wrap
if ($failed) {
    Write-Host '诊断发现必须修复的问题。' -ForegroundColor Red
    exit 1
}
Write-Host '未发现阻止本机运行的问题。' -ForegroundColor Green
exit 0
