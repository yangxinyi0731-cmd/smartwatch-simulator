# 提前风险研究生活化说明页（E0 工程演示）

更新时间：2026-08-31

## 定位

本页面把已经完成的 P0、P1、P2 工程基础做成一个可在 Windows 本机直接打开的生活化说明与只读工程演示。默认阅读层面向老人、家属、比赛评委和不懂技术的公众，用老人一天中的真实活动回答四个问题：

1. 为什么不能“动作大就报警”；
2. 为什么必须先认识每个人自己的生活规律，再看当前连续动作；
3. 快速坐下、坐车颠簸、甩水和摘表为什么容易误会；
4. 当前软件已经做了什么、离真实提醒还差什么。

研究人员可以按需展开专业参数、逐时刻记录、指标、合同、资产审计和原始证据。它不是面向老人、家属或救援方的真实风险界面，也不是 P9。生活场景只解释未来产品逻辑；页面仍只允许展示 E0 工程证据和人工确定性夹具。

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
独立 HTML / CSS / JavaScript 生活化说明页
```

该服务不挂载到 `backend.app.main`，不读取或写入 SQLite，不调用现有三个模型，不修改 Vue 产品界面，也不连接外部网络。两个本机界面只共享 `frontend/src/tokens.css` 中的视觉令牌值。

## 页面内容

### 一眼看懂

首页先给出普适原则：“先认识每位老人的平常，再判断此刻是否真的不对劲”。它用三层通俗问题解释长期个体规律、当前连续动作和验证后提醒，并在同一首屏明确说明“工程演示，还不能给真实老人报警”。`E0` 只作为次要阶段名出现。

### 老人一天的生活路线

页面按早到晚展示五类生活场景：从床上起身、早餐与服药、公园散步、弯腰捡东西和夜里去卫生间。每个场景同时说明正常解释、可能值得留意的连续变化，以及为什么单次动作不能直接等同危险。

生活场景选择器进一步比较起身后发晃、快速坐到沙发、坐车颠簸和摘表充电。切换只更新固定解释文案，不调用模型、不生成分数，也不宣称当前系统已经识别这些场景。

### 容易误会的正常动作

快速坐下、坐车颠簸、甩手上的水和摘表/松动作为困难负样本进入默认阅读层。页面明确说明：没有可靠信号时，正确答案是“无法判断”，不是“安全”。

### 固定工程互动

默认只显示通俗判断过程、播放控制、固定分数图和四项结果摘要。专业参数和逐时刻表格使用原生 `details` 渐进展开。页面允许调整以下纯工程参数：

- 触发阈值；
- 复位阈值；
- 连续证据数；
- 候选冷却期。

后端只接受白名单参数，并始终自行设置 `dry_run=true`。公众文案将它解释为“只演示、不报警”。客户端不能传入或关闭 dry-run；任何额外字段都会被拒绝。输入固定来自 `tests/early_risk/fixtures/deterministic_timeline.v1.json`，输出只返回当前 HTTP 响应，不写文件。

时间轴同时提供可见图例、逐时刻通俗文字状态和可展开数据表，颜色不是唯一信息。播放、暂停和重置只移动浏览器中的可视游标，不启动真实时间传感器或通知。

### 现在做到哪

公众层把路线压缩为四步：软件规则与检查、伦理/许可/本人同意、真实个体基线与短时前兆研究、静默试运行后再决定提醒。P0–P9 完整路线放在展开区；P0–P2 只标记为工程检查，P3–P9 显示锁定原因。用户不能通过页面按钮解锁任何阶段。

### 技术依据

指标先用现实问题命名，再显示事件级精确率、AP/AUPRC、误报/人日、ECE、覆盖率和 1/2/3/5/10 秒事件级召回等技术名。每组数字都明确标记为工程夹具，用途仅为验证公式、序列化和页面展示。

合同、Gate、当前资产审计、三个现有模型、确定性夹具和夹具报告继续从仓库原件读取，但全部位于“技术依据”渐进展开区。下载端点使用固定白名单，不接受任意文件路径。

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

运行态验收还需要启动页面，检查桌面和窄窗口布局、键盘焦点、五项真实导航、四个生活场景按钮、老人一天路线、重新读取、专业参数展开、参数错误与焦点、重新判断、播放/暂停/重置、无法判断、摘表抑制、技术依据展开、原件下载、控制台错误和页面级横向溢出。

完成证据见 `reports/early_risk/e0/workbench-verification.json` 与仓库根目录 `EARLY_RISK_E0_WORKBENCH_HANDOFF.md`。Premium 审计命令中的技能版本路径属于当前 Codex 工作站；其他机器应改用其实际安装位置。

## P3–P9 仍然需要什么

工作台完成不会自动授权进入下一阶段。伦理、知情同意、数据最小化、撤回、许可、真实采集、长期个体基线、预事件模型、风险融合、独立外部验证、前瞻静默试运行和任何形式的用户通知，仍必须按照桌面总纲逐阶段通过 Gate。
