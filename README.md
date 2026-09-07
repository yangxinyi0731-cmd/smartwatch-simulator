# 老年人 AI 模拟智能手表

英文仓库名：`smartwatch-health-simulator`

这是一个只在 Windows 电脑上运行的模拟智能手表研究平台。主产品保留跌倒检测、个人规律异常和腕部活动识别三个独立模型；校赛风险工作台另外接入了一个基于公开受控腕部六轴数据训练的 1/2/3 秒代理提前风险模型。当前具备 100 个可追溯 WEDA 案例、1 个合成规律案例、4 个 CAPTURE-24 自由生活活动窗口、新数据真实计算、波形与逐秒风险展示和一键本地交付。所有模型均未完成现实环境外部验证，也不获部署批准。

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
- 独立校赛风险评估工作台：可上传标准六轴 CSV/JSON，真实运行活动识别、跌倒候选和 1/2/3 秒公开代理研究模型；同时保留 105 组公开案例，并新增 30 组 P01 自主采集案例、模拟手表、实际波形、逐秒风险曲线和格式化判断依据。自主采集工程验证已完成，现实预测与通知边界仍保持关闭。
- 私有 GitHub 仓库：`https://github.com/yangxinyi0731-cmd/smartwatch-simulator`；当前开发分支跟踪同名远程分支。

尚未完成：

- 真实设备接入。

## 提前风险校赛研究版与 E0 基础

独立目录 `research/early_risk/` 已完成 P0+P1+P2：产品与目标合同、数据与标签合同、当前资产适用性审计、严格事件前截断、事件级指标、误报/人日、校准、覆盖率、抑制影响和 dry-run 状态机。工程基础入口为 `EARLY_RISK_P0_P2_HANDOFF.md`；当前校赛版完整交接为 `EARLY_RISK_SCHOOL_DEMO_HANDOFF.md`；旧版页面记录 `EARLY_RISK_E0_WORKBENCH_HANDOFF.md` 只作为历史保留；Gate 证据为 `docs/early_risk/GATE_DECISION.md`。

P0–P2 的 E0 工程骨架仍然保留。校赛工作台另外训练并接入了公开数据代理提前风险基线：只读取 WEDA 数据集跌倒区间开始之前的因果窗口，按参与者隔离训练、校准和评估，输出 1/2/3 秒三个研究分数。它证明公开受控代理模式可被当前方法计算，不证明现实意外跌倒预测，也不等同于真实 `t_instability`。

完成一次“首次安装”后，可以双击 `scripts\windows\start-early-risk-workbench.cmd` 打开独立研究工作台，地址固定为 `http://127.0.0.1:8010/`。对应的停止和诊断入口为 `stop-early-risk-workbench.cmd` 与 `diagnose-early-risk-workbench.cmd`。工作台不启动现有产品服务；上传内容只在内存中分析，不写 SQLite。六轴公开案例和新文件会真实运行模型，但不会振动、发声、发送消息或产生外部通知。

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

### 打开校赛风险研究工作台（保留 E0 真实性边界）

在同一个 `scripts\windows` 文件夹中：

1. 双击 `start-early-risk-workbench.cmd`：启动只监听本机的研究证据服务并打开页面；
2. 双击 `stop-early-risk-workbench.cmd`：核对进程身份后停止工作台；
3. 双击 `diagnose-early-risk-workbench.cmd`：检查证据文件、虚拟环境、E0 合同、dry-run 安全边界和运行状态。

研究工作台地址固定为 `http://127.0.0.1:8010/`，健康检查为 `http://127.0.0.1:8010/api/health`。它不等同于 P9 风险 UI：P3–P9 仍然锁定，页面不会显示真实个人风险，也不会连接短信、电话、家属或救援服务。详细说明见 `docs/early_risk/WORKBENCH.md`。

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
.\.venv\Scripts\python.exe -m pytest .\tests\early_risk -q
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
