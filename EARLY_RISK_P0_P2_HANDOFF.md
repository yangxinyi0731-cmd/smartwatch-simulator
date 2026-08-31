# 老年人智能手表提前风险研究：P0+P1+P2 完成交接

更新时间：2026-08-31

实际仓库：`C:\Users\yangxinyi\Documents\Codex\2026-08-27\smartwatch-health-simulator`

分支：`codex/early-risk-p0-p2-foundation`

起点 HEAD：`32d20fd8df4ae7d62759749cd09d043e671c0c2f`

后续状态：P0+P1+P2 证据已经形成独立 E0 本机工作台；继续接手请先阅读 `EARLY_RISK_E0_WORKBENCH_HANDOFF.md`。本文件仍保留第一大关的历史边界。

## 1. 当前结论

第一大关已把未来提前风险研究的产品真实性、目标事件、时间锚点、数据/标签合同、指标公式、当前资产审计、严格事件前截断、确定性指标夹具和 dry-run 策略状态机落实为可测试代码与 E0 报告。

这只说明“离线研究骨架可重复运行”；它不构成任何真实老人未来危险预测证据。

## 2. 接手顺序

1. 完整阅读桌面总纲 `C:\Users\yangxinyi\Desktop\智能手表提前风险预测-最终方案与实施总纲.md`；
2. 阅读本文件；
3. 阅读 `docs/early_risk/PRODUCT_TRUTH_CONTRACT.md`、`PREDICTION_TARGETS.md`、`METRIC_SPEC.md`；
4. 阅读 `docs/early_risk/DATA_DICTIONARY.md`、`LABELING_PROTOCOL.md` 和 `CURRENT_DATA_AUDIT.md`；
5. 阅读 `docs/early_risk/GATE_DECISION.md`；
6. 现场执行 `git status --short`、`git branch --show-current`、`git rev-parse HEAD`、`git log -5 --oneline` 和 `git remote -v`；
7. 再决定是否只读复核或等待用户授权下一大关。

交接记录状态，不自动授权 P3 或任何后续阶段。

## 3. 关键文件

### P0

- `configs/early_risk/target_contract.v1.yaml`
- `research/early_risk/target_contract.py`
- `docs/early_risk/PRODUCT_TRUTH_CONTRACT.md`
- `docs/early_risk/PREDICTION_TARGETS.md`
- `docs/early_risk/METRIC_SPEC.md`

### P1

- `research/early_risk/contracts.py`
- `docs/contracts/early-risk-domain.schema.json`
- `configs/early_risk/sensor_profiles/`
- `docs/early_risk/DATA_DICTIONARY.md`
- `docs/early_risk/LABELING_PROTOCOL.md`

### P2

- `research/early_risk/temporal.py`
- `research/early_risk/metrics.py`
- `research/early_risk/policy.py`
- `research/early_risk/baselines.py`
- `research/early_risk/audit_current_data.py`
- `research/early_risk/run_fixture_benchmark.py`
- `tests/early_risk/`
- `reports/early_risk/e0/`

## 4. 已通过的 Gate

- 目标合同完整率 100%，规范化 SHA-256 为 `4f796983479cdedb5795189834d7f658599791a515396a33942f27dee6ab62b0`；
- P1 Schema 无漂移，SHA-256 为 `70114fccaf664be3c4412653dfe11ebf177e7fdfbedd0abb6905e0ee0eb38f72`；
- 11 个现有资产审计覆盖率 100%；
- 保存活动拆分参与者交叉 0；
- 确定性预事件窗口的事件后样本泄漏 0；
- 两次运行规范化哈希一致；
- E0 报告全部保持 `prediction_evidence=false`；
- dry-run 外部通知 0；
- 后端原有测试加新研究测试共 86 passed；
- 前端构建、npm audit、pip check、Markdown、声明扫描和 Git 空白检查通过。

## 5. 未完成且不得误报

- 正式产品、研究和安全/伦理负责人签署；
- 伦理、知情同意、数据控制、隐私、撤回、删除和许可；
- 真实老人/高风险人群数据；
- 个人长期基线、短时前兆、风险融合或时间到事件模型；
- 真实提前量、误报/人日、校准、外部验证和静默运行；
- 风险 UI、本地提示、家属通知、救援、部署或 GitHub 发布。

## 6. 复现命令

```powershell
.\.venv\Scripts\python.exe -m pytest backend/tests tests/early_risk -q
.\.venv\Scripts\python.exe -m research.early_risk.export_contracts --check
.\.venv\Scripts\python.exe -m research.early_risk.audit_current_data --no-download
.\.venv\Scripts\python.exe -m research.early_risk.run_fixture_benchmark --config configs/early_risk/baselines.v1.yaml --repeat 2
.\.venv\Scripts\python.exe -m research.early_risk.build_gate_evidence
.\.venv\Scripts\python.exe -m research.early_risk.verify_markdown
.\.venv\Scripts\python.exe -m research.early_risk.check_claims
npm --prefix frontend run build
npm --prefix frontend audit
.\.venv\Scripts\python.exe -m pip check
git diff --check
```

## 7. 下一步边界

当前必须停在 P2。只有用户再次明确授权进入 P3，且相应负责人开始处理正式签署、伦理、许可、隐私和采集方案后，才能继续；仍不能因为 P3 文档完成就采集真实数据或进入真实报警。
