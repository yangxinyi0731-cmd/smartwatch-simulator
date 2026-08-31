# 模拟智能手表检测台（E0 前端演示）

更新时间：2026-08-31

## 定位

本页面把已经完成的 P0、P1、P2 工程基础做成一个可在 Windows 本机直接操作的模拟智能手表检测软件。现场评委可以从 105 组已登记案例中搜索、筛选和选择案例，在可见的手表界面上开始、暂停、继续或重置检测，并在同一屏查看四步判断过程与仓库已有结果。

本次只重做前端演示界面，不修改后端、模型、数据合同或部署边界。WEDA-FALL 案例可以显示仓库已经保存的同源回放摘要；CAPTURE-24 和合成生活规律只显示案例输入已经登记，不伪造逐样本输出。页面不是 P9，不具备真实老人提前几秒预测、真实报警或部署批准。

## 打开、停止和诊断

完成仓库 `README.md` 的首次安装后，在 `scripts\windows` 中使用：

- `start-early-risk-workbench.cmd`：启动并打开工作台；
- `stop-early-risk-workbench.cmd`：核对进程身份后停止；
- `diagnose-early-risk-workbench.cmd`：只读检查文件、依赖、E0 合同、安全边界和服务状态。

固定地址：`http://127.0.0.1:8010/`

健康检查：`http://127.0.0.1:8010/api/health`

运行状态和日志位于 `backend/runtime/early-risk-workbench/`，该目录已被 Git 忽略。启动脚本记录 PID、Python 绝对路径和启动时间；停止脚本必须三项一致才会停止进程，避免误停其他程序。

## 架构隔离

```text
版本化 YAML / JSON 合同与报告
            │ 只读
            ▼
research.early_risk.workbench_server
            │ 127.0.0.1:8010
            ▼
独立 HTML / CSS / JavaScript 模拟手表检测台
```

该服务不挂载到 `backend.app.main`，不读取或写入 SQLite，不调用现有三个模型，不修改 Vue 产品界面，也不连接外部网络。两个本机界面只共享 `frontend/src/tokens.css` 中的视觉令牌值。

## 页面内容

### 首屏检测软件

页面使用深色应用侧栏、设备状态栏和浅色工作区。首屏固定显示三个协作区域：左侧案例库，中间模拟手表，右侧判断过程。评委不需要先读研究说明，就能直接选择案例并操作手表。

### 105 组案例库

案例总数和分类固定显示为：全部 105、受控模拟跌倒 40、受控日常活动 60、活动识别 4、生活规律 1。列表每页 6 条，支持按案例 ID、短标题或参与者搜索。切换类型或有效搜索后，如果原案例不再可见，手表与判断区会同步到首个可见案例。

### 模拟手表操作

手表显示当前时间、电量、案例编号、数据来源、采样率、传感器轴数、检测阶段、进度和结果。开始检测后按“读取腕部数据—整理连续窗口—独立模型判断—结果复核”四步运行；暂停、继续和重置只控制浏览器内的阶段状态，不启动真实传感器、不训练模型、不发送通知。

### 结果真实性

- WEDA-FALL 的 100 组案例显示仓库已经保存的最高候选概率和候选段数；受控模拟跌倒与受控日常活动分别标记，误报候选不会被包装成真实风险。
- CAPTURE-24 的 4 组活动案例只显示输入规格和“案例已就绪”；当前前端没有伪造活动窗口的逐样本回放。
- 100 天合成生活规律只显示合成输入规模和“规律规则已登记”；它不是真实老人记录。
- 三个现有模块保持独立，不合成医学风险分数。未来几秒风险预测显示“后端尚未接入 / 锁定 / 需要 P3–P9”。

### 说明与边界

页面保留一个渐进展开的“说明与边界”区域，继续说明“先认识每位老人的平常”、老人一天的生活路线、快速坐到沙发、坐车颠簸和摘表充电等未来产品要求。这些文字只解释目标和困难负样本，不冒充当前识别结果。页面始终显示 `prediction_evidence=false`、“只演示、不报警”和外部通知 0 次。

## 本机接口

| 方法 | 路径 | 用途 | 是否写入 |
|---|---|---|---|
| GET | `/api/health` | 核验回环范围、E0 和通知关闭状态 | 否 |
| GET | `/api/workbench` | 汇总版本化合同与报告供页面读取 | 否 |
| POST | `/api/simulate` | 对固定策略输入执行一次 dry-run | 否 |
| GET | `/evidence/{allowlisted-name}` | 下载五类固定证据原件 | 否 |

所有动态响应使用 `Cache-Control: no-store`。服务设置 CSP、`X-Content-Type-Options: nosniff`、`X-Frame-Options: DENY`、同源资源和无引用来源等安全响应头。

## 强制安全边界

- 服务器拒绝绑定 `0.0.0.0`、局域网地址或公网地址；
- POST 请求上限为 16 KiB，只接受 `application/json`；
- 触发阈值、复位阈值、连续证据数和冷却期均有服务端范围检查；
- 策略端拒绝 `dry_run=false`；
- 证据下载使用文件名白名单并拒绝路径穿越；
- 页面不使用浏览器原生 `alert`、`confirm` 或 `prompt`；
- 页面不使用本地存储保存参数，不把参数写入 URL；
- 页面没有真实个人数据、通知收件人、电话、短信、振动、声音、救援或部署入口；
- 外部通知计数必须为 0，否则启动与测试视为失败。

## 验证命令

```powershell
.\.venv\Scripts\python.exe -m pytest .\tests\early_risk\test_workbench_server.py -q
.\.venv\Scripts\python.exe -m pytest .\backend\tests .\tests\early_risk -q
node --check .\research\early_risk\workbench\app.js
npm --prefix frontend run build
cmd.exe /d /c .\scripts\windows\diagnose-early-risk-workbench.cmd
npx -y -p @google/design.md designmd lint DESIGN.md
.\.venv\Scripts\python.exe C:\Users\yangxinyi\.codex\plugins\cache\openai-curated-remote\frontend-design-premium\1.4.0\skills\frontend-design-premium\scripts\audit_project.py . --mode strict --output reports\early_risk\e0\workbench-premium-audit.json
```

运行态验收还需要启动页面，检查桌面和 `390×844` 窄窗口布局、键盘焦点、五项真实导航、105 组总数与 `40 / 60 / 4 / 1` 分类、搜索/清除/无结果、6 条分页、案例与手表同步、开始/暂停/继续/重置、WEDA 保存摘要、CAPTURE-24 与合成规律就绪状态、P3–P9 锁定、说明与边界展开、外部通知 0 次、至少 44×44px 的可见操作目标、控制台错误和页面级横向溢出。

完成证据见 `reports/early_risk/e0/workbench-verification.json` 与仓库根目录 `EARLY_RISK_E0_WORKBENCH_HANDOFF.md`。Premium 审计命令中的技能版本路径属于当前 Codex 工作站；其他机器应改用其实际安装位置。

## P3–P9 仍然需要什么

工作台完成不会自动授权进入下一阶段。伦理、知情同意、数据最小化、撤回、许可、真实采集、长期个体基线、预事件模型、风险融合、独立外部验证、前瞻静默试运行和任何形式的用户通知，仍必须按照桌面总纲逐阶段通过 Gate。
