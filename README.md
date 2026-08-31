# 老年人 AI 模拟智能手表

英文仓库名：`smartwatch-health-simulator`

这是一个只在 Windows 电脑上运行的三模型模拟智能手表研究平台。当前已经具备 Tabler 风格 Vue 前端、FastAPI 本地后端、100 个可追溯 WEDA 案例、1 个合成规律案例、4 个 CAPTURE-24 真实自由生活活动窗口、WebSocket 实时状态通道、真实回放、可恢复批量回放和一键本地交付。跌倒检测、个人规律异常和腕部活动识别三个研究模型均已接入；三者仍未完成外部验证，也不获部署批准。

## 当前真实状态

已经完成：

- Vue 3 + TypeScript + Vite 前端；
- Tabler 工作台布局、共享状态和空状态组件；
- `GET /api/health` 真实健康检查；
- SQLite 结构版本 5：来源、案例、传感器流、导入批次、原始文件哈希、质量记录、真实标签、合成规律、模型 manifest、回放、三模型独立输出和可恢复批量任务表；
- `WS /ws/system` 实时系统状态；
- `GET /api/contracts`：真实性类别、三模型固定输入输出和回放事件合同；
- `GET /api/cases`：真实服务端分页、筛选和白名单排序；
- `GET /api/models`：从 SQLite 读取模型版本、artifact 哈希、评估引用、审批状态和局限；
- `GET /api/reports`：把已登记模型的本地评估文件规范化为带证据范围、限制和报告 SHA-256 的统一清单；
- `GET /api/reports/export.json`：下载当前统一测试报告 JSON 快照；
- `GET /api/cases/{case_id}/replay-preview`：重新校验本地文件并返回真实波形、标签、模型窗口、候选告警或合成规律逐日判断；
- `POST /api/batch-replays`、`GET /api/batch-replays` 与 `GET /api/batch-replays/{task_id}`：创建、查询并恢复 SQLite 持久化批量回放；
- Pydantic → OpenAPI/JSON Schema → TypeScript 的可重复生成链；
- 前端自动检查、断线重试和手动刷新；
- 后端接口与数据库自动测试；
- 100 个固定版本 WEDA-FALL 来源案例及确定性导入器；
- 每条案例的原始文件 SHA-256、处理文件 SHA-256、质量标记和标签边界；
- 已核验接入的跌倒 ONNX、100 案例重放报告、100 天合成规律与统计规则；
- CAPTURE-24 恢复前缀子集的固定可用性扫描、24 人训练组、12 人不重叠评估组、活动 ONNX、模型卡与留出报告；
- 前端按真实性筛选案例、开始/暂停/继续/重置回放、1×–16×速度、真实三轴/六轴波形、证据时间线和数据质量展示；
- 前端测试报告区域：实读保存的评估文件、显示适用范围与限制，并提供 JSON 下载。
- 前端批量回放区域：按当前真实性筛选创建任务，显示真实进度、失败数、恢复次数和三个模型各自完成数，不生成综合医学风险。

尚未完成：

- 真实设备接入；
- GitHub 远程发布。

## 提前风险研究 E0 基础

独立目录 `research/early_risk/` 已完成 P0+P1+P2：产品与目标合同、数据与标签合同、当前资产适用性审计、严格事件前截断、事件级指标、误报/人日、校准、覆盖率、抑制影响和 dry-run 状态机。入口文档为 `EARLY_RISK_P0_P2_HANDOFF.md`，Gate 证据为 `docs/early_risk/GATE_DECISION.md`。

这些能力只属于 E0 工程研究骨架，没有接真实个人数据，没有训练提前预测模型，也没有风险 UI 或通知。不能把夹具指标或现有三个模型写成真实老人提前预测成绩。

当前 SQLite 案例总数为 105：40 条年轻参与者受控床垫模拟跌倒、30 条老年参与者受控日常活动、30 条年轻参与者受控日常活动、1 个明确标记为合成数据的 100 天生活规律案例，以及 4 个从固定评估参与者真实三轴窗口生成的 CAPTURE-24 自由生活活动演示案例。它们不是“100 个真实老人跌倒”。CAPTURE-24 来源只是逐成员核验的 48 人恢复前缀子集，不是完整 151 人数据包，也不能描述为老人专项数据。

## 首次安装

以下命令都在项目根目录运行：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r .\backend\requirements-lock.txt
npm --prefix frontend install
```

依赖锁定清单来自 Windows CPython 3.14 环境。直接依赖声明分别保存在 `backend/requirements.txt` 和 `backend/requirements-dev.txt`。

## 本地运行

### 最简单：双击启动

完成一次“首次安装”后，打开 `scripts\windows` 文件夹：

1. 双击 `start-smartwatch.cmd`：自动构建前端、启动只监听本机的服务并打开页面；
2. 双击 `stop-smartwatch.cmd`：只停止该脚本记录的本项目进程，保留 SQLite 和日志；
3. 双击 `diagnose-smartwatch.cmd`：检查 Python、Node.js、依赖、前端构建、数据库、三个模型资产和服务健康状态。

一键版只使用一个后台进程，同时提供前端、API 和 WebSocket，地址固定为 `http://127.0.0.1:8000/`。运行状态与日志保存在 Git 忽略目录 `backend/runtime/local-delivery/`。

### 开发模式

打开第一个 PowerShell 窗口，在项目根目录启动后端：

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

打开第二个 PowerShell 窗口，在同一项目根目录启动前端：

```powershell
npm --prefix frontend run dev
```

然后访问终端显示的前端地址，通常是 `http://127.0.0.1:5173/`。前端开发服务器会把 `/api` 和 `/ws` 安全地转发到只监听本机的后端。

健康检查地址：`http://127.0.0.1:8000/api/health`

FastAPI 接口文档：`http://127.0.0.1:8000/docs`

统一合同：`http://127.0.0.1:8000/api/contracts`

案例目录：`http://127.0.0.1:8000/api/cases`

模型清单：`http://127.0.0.1:8000/api/models`

测试报告：`http://127.0.0.1:8000/api/reports`

测试报告 JSON 下载：`http://127.0.0.1:8000/api/reports/export.json`

单案例回放预览：`http://127.0.0.1:8000/api/cases/weda-f01-u01_r01/replay-preview`

批量回放清单：`http://127.0.0.1:8000/api/batch-replays`

固定版本 WEDA-FALL 导入命令和许可边界见 `backend/README.md` 与 `data/catalog/README.md`。来源许可证尚未核验，因此原始和处理后的传感器文件都不进入 Git，也不被重新分发。

默认数据库位于 `backend/runtime/smartwatch.sqlite3`，数据库文件已被 Git 忽略。需要改到其他位置时，只接受绝对路径：

```powershell
$env:SMARTWATCH_DATABASE_PATH = 'D:\smartwatch-data\smartwatch.sqlite3'
```

## 验证

```powershell
.\.venv\Scripts\python.exe -m pytest .\backend\tests -q
.\.venv\Scripts\python.exe -m backend.scripts.export_contracts
npm --prefix frontend run generate:api
npm --prefix frontend run build
npm --prefix frontend audit
```

完整设计审计、浏览器验证和阶段证据记录在 `TASK_STATE.md`。

## 真实性边界

本项目是研究与比赛演示原型，不是医疗器械、诊断或正式救援系统。请先阅读 `DATA_AND_MODEL_NOTICE.md`：

- 年轻参与者在受控条件下模拟的跌倒不能描述为真实老人跌倒；
- 老年参与者数据只涉及日常活动误报分析；
- 合成规律必须标记为合成数据；
- 没有实际输入时不显示随机波形或模型分数；
- 任何指标都必须来自保存了配置、分组和命令的实际运行。

跨对话继续开发前，请先阅读 `CONTEXT_HANDOFF.md` 和 `TASK_STATE.md`。当前用户已授权按完整大关连续推进；只有登录、许可申请、隐私/法律选择或外部账号操作需要用户本人处理时才暂停。
