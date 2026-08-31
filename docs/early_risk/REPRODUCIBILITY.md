# P0+P1+P2 E0 复现说明

## 1. 环境与边界

命令在仓库根目录运行，使用现有 Windows `.venv`。本流程离线、无个人数据、不下载数据、不训练模型、不启动服务、不修改产品 UI，也不发送通知。

## 2. 合同与 Schema

```powershell
.\.venv\Scripts\python.exe -m research.early_risk.validate_contract --config configs/early_risk/target_contract.v1.yaml
.\.venv\Scripts\python.exe -m research.early_risk.export_contracts --check
```

## 3. 当前资产审计

```powershell
.\.venv\Scripts\python.exe -m research.early_risk.audit_current_data --no-download
```

## 4. 确定性夹具重复运行

```powershell
.\.venv\Scripts\python.exe -m research.early_risk.run_fixture_benchmark --config configs/early_risk/baselines.v1.yaml --repeat 2
```

两次规范化报告 SHA-256 必须相同，时间泄漏 finding 必须为 0，外部通知数必须为 0。

## 5. 测试与声明检查

```powershell
.\.venv\Scripts\python.exe -m pytest tests/early_risk -q
.\.venv\Scripts\python.exe -m research.early_risk.check_claims
git diff --check
```

完整仓库回归仍需运行 `backend/tests`。E0 结果的唯一允许总结是研究骨架、合同、指标和 dry-run 状态机可重复运行；不能写成预测能力。
