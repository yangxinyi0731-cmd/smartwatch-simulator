# 老年人 AI 模拟智能手表

英文仓库名：`smartwatch-health-simulator`

这是一个只在 Windows 电脑上运行的三模型模拟智能手表研究平台。当前已经具备 Tabler 风格 Vue 前端、FastAPI 本地后端、SQLite 空案例库、WebSocket 实时状态通道，以及统一案例/来源/回放/三模型合同；尚未导入案例或接入任何模型。

## 当前真实状态

已经完成：

- Vue 3 + TypeScript + Vite 前端；
- Tabler 工作台布局、共享状态和空状态组件；
- `GET /api/health` 真实健康检查；
- SQLite 结构版本 2：来源、案例、传感器流、模型 manifest、回放和三模型独立输出表；
- `WS /ws/system` 实时系统状态；
- `GET /api/contracts`：真实性类别、三模型固定输入输出和回放事件合同；
- `GET /api/cases`：真实服务端分页、筛选和白名单排序；
- Pydantic → OpenAPI/JSON Schema → TypeScript 的可重复生成链；
- 前端自动检查、断线重试和手动刷新；
- 后端接口与数据库自动测试。

尚未完成：

- 公开数据和 100 个可追溯案例导入；
- 跌倒 ONNX 接入；
- 个人规律异常模型重构；
- 腕部活动识别模型训练；
- 波形、时间线、告警和报告业务流程；
- 真实设备接入；
- Windows 一键交付包和 GitHub 远程发布。

因此，界面中的“0 个案例”“暂无数据”“待接入”和“待训练”都是准确状态，不是演示占位数据。

## 首次安装

以下命令都在项目根目录运行：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r .\backend\requirements-lock.txt
npm --prefix frontend install
```

依赖锁定清单来自 Windows CPython 3.14 环境。直接依赖声明分别保存在 `backend/requirements.txt` 和 `backend/requirements-dev.txt`。

## 本地运行

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
