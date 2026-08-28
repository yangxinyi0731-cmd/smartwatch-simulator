# 项目持续状态

更新时间：2026-08-28

## 总目标

完成一个可在 Windows 电脑上直接打开的三模型模拟智能手表平台，并保留数据来源、模型卡、测试报告和可复现命令。

## 当前步骤

“最小本地数据闭环”已经实现：FastAPI、SQLite、WebSocket 和前端真实连接状态位于 `codex/tabler-ui-migration` 分支。本大关完成后必须停止，等待用户确认下一大关；不能自动进入案例导入、模型接入或训练阶段。

## 本步已完成

- 新建 FastAPI `0.141.1` 本地服务，并固定 Uvicorn `0.52.4`；
- 新建 `GET /api/health`，返回后端、SQLite、结构版本和案例实数；
- 新建 `WS /ws/system`，连接后立即发送状态并每 15 秒更新；
- 新建 SQLite 结构版本 1、迁移记录和带真实性/来源约束的空 `cases` 表；
- 默认数据库保存在 Git 忽略的 `backend/runtime/smartwatch.sqlite3`；自定义路径必须是绝对路径；
- 发现高于程序支持版本的 SQLite 时拒绝自动降级；
- 前端从静态“尚未开始”改为真实 HTTP 健康检查和 WebSocket 状态；
- 前端断线使用 1/2/5/10 秒有上限退避，切换页面可见性或手动刷新时取消旧请求；
- 新建共享 `AppButton`，提供真实“刷新状态”操作和稳定忙碌状态；
- 保留 0 个案例、暂无回放数据和三个模型未接入/待训练的真实状态；
- 新建四个后端自动测试，固定 Windows CPython 3.14 完整依赖锁；
- 更新产品、架构、设计、UX、许可、启动和交接文档。

## 本步验证结果

- Python 依赖安装：FastAPI、Uvicorn 和 Windows CPython 3.14 依赖解析成功；
- `.\.venv\Scripts\python.exe -m pytest .\backend\tests -q`：4 个测试通过，无警告；
- `.\.venv\Scripts\python.exe -m pip check`：没有损坏或冲突的依赖；
- `backend/requirements-lock.txt` 与当前实装 Python 环境逐项一致；
- `npm --prefix frontend audit`：0 个已知漏洞；
- `npm --prefix frontend run build`：成功；Vue 类型检查和 Vite 生产构建均通过；
- 当前构建产物：CSS 546.37 kB（gzip 70.52 kB），JavaScript 83.49 kB（gzip 32.12 kB）；
- `designmd lint DESIGN.md`：0 个错误、0 个警告、1 条令牌汇总信息；
- Premium 严格审计：0 个 findings、0 个错误、0 个警告、0 个未解决项；
- 反模式检查：没有原生 `alert / confirm / prompt`、假链接、非语义点击、表单/原生选择器绕过、危险 HTML、浏览器存储或旧静态后端状态；
- 离线启动：前端显示“后端未连接”、SQLite 不可读取和自动重试说明，控制台 0 错误 / 0 警告；
- 后端启动：页面自动恢复为 FastAPI `v0.2.0`、SQLite 结构版本 1、WebSocket 已连接和案例实数 0；
- 运行中断线：页面降级为未连接；重新启动后自动恢复，控制台 0 错误 / 0 警告；
- 手动“刷新状态”：操作完成后按钮恢复可用，连接状态保持正确；
- 1440×900：四列系统状态和两栏工作区，无页面级横向溢出；
- 1024×768：两列系统状态和单列工作区，无页面级横向溢出；
- 390×844：单列系统状态与工作区，导航只在自身容器横向滚动，页面无横向溢出；
- 键盘焦点：“跳到主要内容”链接显示约 3px 蓝色轮廓且位于可见区域；
- 浏览器限制：Google Chrome 已安装，但未运行且 ChatGPT/Codex Chrome 控制扩展未安装；本轮真实浏览器验收使用 Codex 应用内 Chromium，不能表述为 Chrome 专项兼容性验证。

## 明确未完成

- 没有下载或导入 100 个测试案例；
- 没有解压、重构或接入模型二；
- 没有训练模型三；
- 没有接入跌倒 ONNX；
- 没有定义完整传感器窗口、模型输入输出、回放、告警和报告数据库 schema；
- WebSocket 目前只传递系统状态，不传输传感器或模型数据；
- 没有创建或推送 GitHub 远程仓库；
- 没有新增任何模型指标。

## 运行命令

以下命令均从项目根目录运行。第一个 PowerShell 窗口：

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

第二个 PowerShell 窗口：

```powershell
npm --prefix frontend run dev
```

前端默认地址：`http://127.0.0.1:5173/`；健康检查：`http://127.0.0.1:8000/api/health`。

## 下一大关（等待用户确认）

建议下一大关先定义统一案例、三模型输入输出、回放事件和模型 manifest 合同，并为 SQLite 结构版本 2、Pydantic schema 和合同测试建立可迁移骨架。这个大关只定义和验证合同，不自动下载数据、接入模型或训练模型。没有得到用户明确确认前，不开始。

## 用户约定

后续按“大关确认”协作：一个完整阶段实现、验证并提交后停止，不再为阶段内部的小步骤频繁请求确认。
