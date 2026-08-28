# 项目持续状态

更新时间：2026-08-28

## 总目标

完成一个可在 Windows 电脑上直接打开的三模型模拟智能手表平台，并保留数据来源、模型卡、测试报告和可复现命令。

## 当前步骤

“100 个可追溯来源案例导入”大关已经实现：固定版本 WEDA-FALL 只读核验、确定性分层选择、六轴对齐、文件哈希、质量记录、标签边界、SQLite 结构版本 3 和可安全重跑的原子导入均已完成。用户已明确授权后续按完整大关连续推进，不需要每个大关再等待确认；只有必须由用户本人处理的登录、许可申请、隐私/法律选择或外部账号操作才暂停。

## 本步已完成

- 只读核验 WEDA-FALL 本机检出为固定提交 `74e0b93cb061d4ecbca12628f2d47090e97fbeea`，并要求已跟踪文件无改动；
- 导入器固定处理代码来源提交 `6c8bd6058f19467221e292c77a8df00630b8bd0b`，独立实现相同的排序、重复时间戳平均和公共 50 Hz 时间网格对齐；
- 按确定性平衡规则选择 100 条不同来源记录：40 条年轻参与者受控床垫模拟跌倒、30 条老年参与者受控日常活动、30 条年轻参与者受控日常活动；
- 每条记录均包含真实加速度与陀螺仪，没有添加全零或伪造陀螺仪；
- 处理后 100 个 NPY 文件均至少 200 行、固定六列 `ax/ay/az/gx/gy/gz`，并保存在 Git 忽略目录 `data/processed/`；
- `data/catalog/weda_fall_100_v1.json` 保存固定来源、选择策略、100 个不同来源指纹、原始文件哈希、处理文件哈希、采样信息、质量标记和标签；
- WEDA-FALL 许可状态保持 `UNVERIFIED`、是否可重新分发保持未知；原始与处理文件均不提交 Git；
- 100 条记录均如实保留原始时间轴间隙质量标记；38 条还保留至少一个传感器有效回调频率偏离名义 50 Hz 超过 10% 的标记；
- SQLite 从结构版本 2 迁移到版本 3，新增 `import_runs`、`case_import_runs`、`case_source_files`、`sensor_quality` 和 `ground_truth_events`；
- 导入在一个数据库事务内完成：等价批次可安全重跑，复用标识但内容冲突会整批回滚；
- 默认运行数据库已实测写入 100 个案例、100 个传感器流、240 个来源文件记录、100 个质量记录和 100 个标签事件；
- 服务版本提升到 `0.4.0`，`GET /api/health` 返回结构版本 3 和案例实数 100；
- 以下上一大关成果继续保留：
- 新建 `backend/app/contracts.py`，固定五种真实性类别和三个模型的独立职责；
- 固定跌倒模型 `50 Hz × 4 秒 × 6 轴 = 200×6`，缺少真实陀螺仪的案例会被合同拒绝；
- 固定规律异常模型为 100 天合成的用餐、午睡、散步事件，不描述为真实老人训练；
- 固定活动识别模型 `20 Hz × 20 秒 × 3 轴 = 400×3` 和四类活动候选；
- 为案例、来源、传感器窗口、model manifest、三个独立模型输出和五类回放事件建立 Pydantic 合同；
- 合同拒绝不安全相对路径、形状/单位不一致、概率和不一致、阈值判断漂移、派生案例无父关系和未完成外部验证却通过部署审批；
- SQLite 从结构版本 1 迁移到版本 2；
- 新建 `data_sources`、扩展 `cases`，并新建 `sensor_streams`、`model_manifests`、`replay_sessions`、`replay_events`、`model_outputs`；
- 真实存在的 v1 案例迁移时保留原值，缺失字段明确标记为 `UNKNOWN / UNVERIFIED / legacy-unrecorded`，不编造来源；
- 旧版派生案例缺少父关系时只作为禁止进入模型的 legacy 记录保留；新合同仍强制所有新派生案例记录父案例；
- 新建 `GET /api/contracts`，返回合同版本 `1.0.0`、三模型合同和真实性硬边界；
- 新建 `GET /api/cases`，提供参数绑定搜索、真实性/适用模型筛选、白名单排序、服务端分页和越界页码收敛；
- 案例库失败返回不含内部堆栈的可重试 503；
- 合同生成链继续覆盖 OpenAPI、领域 JSON Schema 和前端 TypeScript；
- 新建 OpenAPI 与领域 JSON Schema 生成脚本，并增加提交快照漂移测试；
- 使用 `@hey-api/openapi-ts@0.99.0` 生成前端 TypeScript 类型；生成器输入只使用本地 JSON；
- 使用 npm override 将 `js-yaml` 固定为 `4.3.1`，npm audit 恢复为 0 个已知漏洞；
- 检索并固定 RADAR-base、Open mHealth、AWARE、FastAPI 官方模板、WEDA-FALL、OxWearables 和近期相似端到端跌倒项目的 Git HEAD 与许可状态；
- 新建 `docs/OPEN_SOURCE_REFERENCE_REVIEW.md`，明确采用与排除理由；没有复制这些项目的指标、权重或数据。

## 本步验证结果

- `.\.venv\Scripts\python.exe -m pytest .\backend\tests -q`：26 个测试通过；
- 数据库测试覆盖新库建表、v1→v2 保留迁移、旧版派生记录、来源许可缺失、服务端分页、筛选、LIKE 通配符转义和结构版本保护；
- 合同测试覆盖三模型输入、陀螺仪缺失、路径逃逸、派生父关系、六轴形状、概率和、阈值判断、最高概率标签、artifact 路径和部署审批；
- 提交的 OpenAPI 与领域 JSON Schema 均与当前代码生成结果一致；
- `npm --prefix frontend run generate:api`：成功生成 2 个 TypeScript 文件；
- `npm --prefix frontend run build`：成功；Vue 类型检查和 Vite 生产构建均通过；
- 当前构建产物仍为 CSS 546.37 kB（gzip 70.52 kB）、JavaScript 83.49 kB（gzip 32.12 kB）；
- `npm --prefix frontend audit`：0 个已知漏洞；
- `.\.venv\Scripts\python.exe -m pip check`：没有损坏或冲突的依赖；
- `designmd lint DESIGN.md`：0 个错误、0 个警告、1 条令牌汇总信息；
- Premium 严格审计：0 个 findings、0 个错误、0 个警告、0 个未解决项；
- 运行态 HTTP 实测：SQLite 结构版本 3、合同版本 1.0.0、3 个模型合同、案例总数 100、模拟跌倒筛选 40、适用跌倒模型的受控日常活动 60；
- 对 100 个本机 NPY 逐一重算 SHA-256，全部与目录一致；100 个案例 ID 与来源指纹均不重复，全部为六轴；
- 同一真实导入命令连续执行两次，案例数仍为 100，目录哈希保持 `4e6a68fa8de730999d85f2d254af40adc6241038fc2af2a0c2ce9cfab4041f49`；
- 右侧本地前端持续运行并自动显示新的后端版本和 SQLite 结构版本；
- 本步没有新增页面视觉结构，沿用上一大关已通过的 1440×900、1024×768、390×844、键盘焦点和断线恢复基线；正式完成新增案例页后必须重新跑完整浏览器状态矩阵；
- Google Chrome 已安装，但 ChatGPT/Codex Chrome 控制扩展仍未安装；不能把 Codex 应用内 Chromium 检查写成 Chrome 专项验收。

## 明确未完成

- 没有解压、重构或接入模型二；
- 没有训练模型三；
- 没有把独立仓库中的跌倒 ONNX 与 manifest 复制进本平台；
- 没有运行新增模型推理，因此没有新增任何模型指标；
- WebSocket 仍只传递系统状态，不传感器或模型数据；
- 没有案例库、回放、波形、告警、报告的新界面；
- 没有创建或推送 GitHub 远程仓库。

## 当前运行命令

第一个 PowerShell 窗口：

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

第二个 PowerShell 窗口：

```powershell
npm --prefix frontend run dev
```

前端默认地址：`http://127.0.0.1:5173/`；健康检查：`http://127.0.0.1:8000/api/health`；合同：`http://127.0.0.1:8000/api/contracts`；案例：`http://127.0.0.1:8000/api/cases`。

## 下一大关（已获连续推进授权）

接入三个相互独立的模型适配器。先复制并哈希核验既有跌倒 ONNX 与 manifest，再把规律异常脚本重构为可保存配置和结果的统计规则，最后只在来源、分组和评估均可复现的前提下推进腕部活动识别；未完成外部验证的模型全部保持 `deployment_approved=false`。继续保持：

- WEDA-FALL 跌倒是年轻参与者在受控条件下模拟；
- WEDA-FALL 老人只执行日常活动，用于误报分析；
- 合成规律必须标记 `SYNTHETIC_ROUTINE`；
- 不能满足六轴输入的记录不进入跌倒模型；
- 许可未核验的数据不重新分发或商用；
- 不凑数、不生成随机波形、不编造模型指标。

如果公开数据下载需要用户本人申请、同意条款或登录，只暂停相应数据源，继续推进不需要外部授权的部分。
