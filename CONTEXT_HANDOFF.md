# 老年人 AI 模拟智能手表平台：当前完整交接

更新时间：2026-08-29
实际项目：`C:\Users\yangxinyi\Documents\Codex\2026-08-27\smartwatch-health-simulator`

## 新任务接手顺序

不要在默认空目录新建项目。所有项目命令必须显式使用上面的实际目录作为工作目录。

先完整阅读：

1. `TABLER_MIGRATION_HANDOFF.md`；
2. 本文件；
3. `PRODUCT.md`；
4. `DATA_AND_MODEL_NOTICE.md`；
5. `TASK_STATE.md`；
6. `DESIGN.md`；
7. `UX-CONTRACT.md`；
8. `THIRD_PARTY_NOTICES.md`。

随后只读执行：

```powershell
git status --short
git log -3 --oneline
git remote -v
```

必须以现场输出为准。预期分支为 `codex/tabler-ui-migration`；Tabler 迁移提交为 `11eb7f1`，后续已有多个数据、模型、回放和本地交付提交。项目仍无 Git 远程。

## 当前完成结果

平台已经形成可在 Windows 本机运行的完整研究演示闭环：

- Vue 3 + TypeScript + Vite + Tabler 前端；
- FastAPI 服务版本 `0.8.0`；
- SQLite 结构版本 `5`；
- WebSocket 系统状态；
- 105 个可追溯案例；
- 跌倒检测、个人规律异常、腕部活动识别三个独立研究模型；
- 单案例真实波形/事件回放；
- 三份带范围、限制、路径和 SHA-256 的测试报告；
- SQLite 持久化、幂等、可恢复的批量回放；
- Windows 双击启动、停止和诊断脚本；
- 同一只监听 `127.0.0.1:8000` 的本机进程提供生产前端、API 与 WebSocket。

最新真实批量验收：105/105 完成、失败 0，其中跌倒 100、规律 1、活动 4。另有一次真实重启恢复验收：任务从 `RUNNING` 重启后完成，`recovery_count=1`。这些是本机案例管线行为核验，不是新增模型准确率或外部泛化成绩。

## 数据与模型事实

### WEDA-FALL

- 固定来源 HEAD：`74e0b93cb061d4ecbca12628f2d47090e97fbeea`；
- 40 条年轻参与者受控床垫模拟跌倒；
- 30 条老年参与者受控日常活动；
- 30 条年轻参与者受控日常活动；
- 老人没有执行跌倒；
- 跌倒 ONNX SHA-256：`1e214ebd89fce6620cf09a7a071aa904cd5ca0932e960181ce43c3695e212a3f`；
- 同源 100 案例重放：40/40 受控模拟跌倒出现重叠候选告警，60 个日常活动出现 2 段误报告警，30 个老人日常活动本次 0 段；不能称为外部泛化评估；
- WEDA-FALL 许可状态仍为 `UNVERIFIED`，原始与处理数组不进 Git、不重新分发。

### 合成生活规律

- 固定种子 `20260828`；
- 100 天、551 条用餐/午睡/散步事件；
- 真实性固定为 `SYNTHETIC_ROUTINE`；
- 五个确定性规则场景通过；这不是准确率或医学风险。

### CAPTURE-24 活动识别

- 官方大文件下载中断，只从前缀恢复出 48 个逐成员通过长度与 CRC-32 核验的完整参与者成员；绝不能称为完整 151 人数据包；
- 24 名训练参与者、12 名不重叠评估参与者；
- 7,240 个训练窗口、3,728 个评估窗口；
- 恢复子集内参与者留出准确率 `0.6075643776824035`、宏平均 F1 `0.5977935900949525`；
- 活动 ONNX SHA-256：`47a552b23092920ffbd74c14f3de3abce2aad33771066180f31a42f6e6be667e`；
- CAPTURE-24 以年轻参与者为主，不是老人专项数据；上述结果不是独立外部验证。

三个模型均保持 `deployment_approved=false`，不得合并成综合医学风险分数。

## 普通用户运行

首次安装完成后，打开 `scripts\windows`：

- 双击 `start-smartwatch.cmd` 启动并打开页面；
- 双击 `stop-smartwatch.cmd` 停止，保留 SQLite 与日志；
- 双击 `diagnose-smartwatch.cmd` 做只读诊断。

生产页面：`http://127.0.0.1:8000/`。

开发模式仍可分别运行：

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
npm --prefix frontend run dev
```

## 最新验证基线

- 后端：59 个测试通过；
- 前端生产构建通过；
- npm audit：0 个已知漏洞；
- pip check：无损坏或冲突依赖；
- designmd lint：0 错误、0 警告；
- Premium 严格审计：0 findings；
- 一键生产页面在 1440×900 与 390×844 无页面级横向溢出；
- 浏览器控制台无错误或警告；
- Windows 一键流程已实测启动、重复启动复用、诊断、停止、停止态诊断和重启；
- 端口只监听 `127.0.0.1:8000`。

下一任务仍需重新运行验证，不能把本文件当成现场状态。

## 开源参考现状

`docs/OPEN_SOURCE_REFERENCE_REVIEW.md` 保存采用与排除理由。2026-08-29 已重新只读核验 Open Wearables、WEDA-FALL、DevGurav/fall-detect-system、Stable-Polynomial-Train、FastAPI 官方模板和 OxWearables/capture24 的 GitHub HEAD。没有复制外部项目的指标、权重或未经核验许可的数据。

## 尚未完成与授权边界

- 左侧独立“案例库”页面尚未开放，但总览页已有案例筛选、单案例和批量回放；
- WebSocket 仍只传系统状态，不承担传感器实时流；
- 没有真实设备、医疗诊断或正式救援能力；
- 没有创建或推送本项目 GitHub 远程。

用户已授权普通技术工作连续推进，不必每个小步骤确认。但以下操作仍必须由用户本人授权或参与：GitHub/外部发布、登录、许可申请、隐私或法律选择、真实设备与真实个人数据接入。不得因“尽量上 GitHub”擅自创建远程仓库或上传许可未核验的数据。

## 永久表述边界

- 年轻参与者在受控条件下模拟的跌倒，不是真实老人跌倒；
- 老年参与者只执行日常活动，用于误报分析；
- CAPTURE-24 恢复前缀子集不是完整 151 人数据；
- 缺少真实陀螺仪的数据不能补零后冒充六轴；
- 无实际输入时不生成随机波形或分数；
- 未实测指标不得编造；
- 本项目是研究与比赛演示原型，不是医疗器械、诊断或正式救援系统。
