# 老年人智能手表提前风险研究：E0 生活化说明页完成交接

更新时间：2026-08-31

实际仓库：`C:\Users\yangxinyi\Documents\Codex\2026-08-27\smartwatch-health-simulator`

当前分支：`codex/early-risk-e0-workbench`

基础提交：`75745e0ad0690126bde84c91df612b7f5b95a986`

生活化改版起点：`2d72a770d116424cbcaa74df6a944af20670568d`

## 1. 当前结论

P0+P1+P2 的版本化合同、资产审计、确定性夹具、Gate 和 dry-run 策略已经形成可在 Windows 本机直接打开的独立页面。固定地址为 `http://127.0.0.1:8010/`。默认界面不再要求用户先理解研究术语，而是先用老人一天中的实际生活场景讲清楚“个人平常、连续动作、生活语境、误报和拒判”，再按需展开技术依据。

这个成品仍是 E0 工程演示，不是 P9 老人风险界面。页面中的起身、散步、弯腰、快速坐下、坐车颠簸、甩水和摘表等内容只解释未来产品逻辑，不表示当前模型已识别成功。它不会把人工夹具或现有三个模型包装成真实老人“提前几秒预测”，不会写 SQLite，不会训练模型，也不会振动、发声、联系家属或触发救援。

## 2. 用户打开方式

完成仓库 `README.md` 的首次安装后，进入 `scripts\windows`：

- 双击 `start-early-risk-workbench.cmd`：启动并打开工作台；
- 双击 `stop-early-risk-workbench.cmd`：核对 PID、Python 路径和启动时间后停止；
- 双击 `diagnose-early-risk-workbench.cmd`：只读检查证据、依赖、安全边界和运行状态。

健康检查：`http://127.0.0.1:8010/api/health`

运行日志和进程状态位于 Git 忽略目录 `backend/runtime/early-risk-workbench/`。启动脚本可安全重复执行；已经运行时会复用现有进程。

## 3. 普通人打开后能看懂什么

- 首屏用一句话说明：先认识每位老人的平常，再判断当前连续动作是否真的偏离；
- 沿老人一天的路线理解从床上起身、早餐与服药、公园散步、弯腰捡东西和夜里去卫生间；
- 切换起身后发晃、快速坐到沙发、坐车颠簸和摘表充电，比较同一类手腕动作在不同生活语境中的含义；
- 看懂为什么快速坐下、车辆颠簸、甩水和摘表/松动必须作为困难正常情况，不能轻率报警；
- 播放、暂停和重置 7 个固定人工分数点，观察“普通变化—连续升高—只记候选—缺信号拒判”；
- 用四步路线查看软件地基、伦理/许可、真实个体研究和静默试运行之间的差距；
- 在展开区查看 P0–P9、工程参数、逐时刻记录、指标、合同、三个现有模型和五类白名单证据原件。

所有夹具数字均显示技术名和“工程夹具”，并在互动区直接说明“只演示、不报警”。后端始终强制 `dry_run=true`，客户端不能关闭，也没有外部通知收件人或发送接口。

## 4. 架构与隔离

页面由 `research.early_risk.workbench_server` 和 `research/early_risk/workbench/` 静态界面组成，只监听 `127.0.0.1:8010`。生活场景解释完全在静态前端中切换，不调用模型。它独立于现有 `backend.app.main`、Vue 产品、SQLite 和三个研究模型运行路径。

服务每次请求只读以下版本化证据：

- `configs/early_risk/target_contract.v1.yaml`；
- `reports/early_risk/e0/p0_p2_gate_summary.json`；
- `reports/early_risk/e0/current_data_audit.json`；
- `tests/early_risk/fixtures/deterministic_timeline.v1.json`；
- `reports/early_risk/e0/fixture_benchmark.json`。

现有 Vue 产品与独立工作台只共享 `frontend/src/tokens.css` 中的视觉令牌；既有颜色、字体和圆角值没有改变。

## 5. 接口与安全边界

| 方法 | 路径 | 行为 |
|---|---|---|
| GET | `/api/health` | 返回回环范围、E0 和通知关闭状态 |
| GET | `/api/workbench` | 汇总版本化只读证据 |
| POST | `/api/simulate` | 对固定人工时间线执行一次 dry-run |
| GET | `/evidence/{allowlisted-name}` | 下载固定白名单证据 |

服务拒绝非回环绑定；POST 限制为 16 KiB 和 `application/json`；只接受四个白名单策略字段及服务端范围；任意额外字段、`dry_run` 字段、非法 JSON、路径穿越和未知证据名都会失败。动态响应使用 `Cache-Control: no-store`，并设置 CSP、`nosniff`、`X-Frame-Options: DENY`、无引用来源和同源资源策略。

## 6. 完成验证

- 完整 Python 回归：`100 passed`；其中工作台服务专项测试 `14 passed`；
- 合同校验通过，规范化 SHA-256 为 `4f796983479cdedb5795189834d7f658599791a515396a33942f27dee6ab62b0`；
- 当前资产审计覆盖 `11/11`，时间泄漏发现 `0`，参与者交叉 `0`；
- 确定性夹具重复两次，规范化报告哈希一致：`02f97ab1d6d2fff4beab0553a69d5ff42329a7aa0ff4a28e7a78d9f78d9ff609`；
- 真实外部通知数 `0`；
- 前端 TypeScript 检查和 Vite 生产构建通过；npm audit 为 `0` 个已知漏洞；pip check 无损坏依赖；
- `DESIGN.md` 官方 lint 为 `0` 错误、`0` 警告；Premium 严格审计为 `0` findings；
- 声明扫描未发现禁用能力断言，Markdown 结构检查通过，JavaScript 语法检查和 Python 编译检查通过；
- Windows 诊断通过，重复启动正确复用，服务实测仅监听 `127.0.0.1:8010`；
- 应用内 Chromium 实测桌面、`390×844` 竖屏和 `844×390` 横屏均无页面级横向溢出；老人一天 5 个场景、4 个可切换生活解释和 4 类困难正常动作均可读；
- 四个场景切换后的 `aria-pressed`、文案边界、专业参数展开、通俗参数错误与字段焦点、恢复默认、播放、暂停、重置、P0–P9/技术依据展开、断服中文错误与重连恢复均通过；
- DOM 验收为单一 `h1`、重复 ID `0`、标题跳级 `0`、未标注字段 `0`、无名称按钮 `0`、小于 24px 的可见指针目标 `0`、缺少 `novalidate` 的表单 `0`；控制台错误和警告为 `0`。

机器可读的界面审计见 `reports/early_risk/e0/workbench-premium-audit.json`，完整交付核验摘要见 `reports/early_risk/e0/workbench-verification.json`。

## 7. Git 与恢复

本分支从 `75745e0…` 创建，与原有三模型产品提交隔离。没有 Git remote，也没有推送。需要撤销本次成品时，先确认当前分支和提交，再对本次交付提交执行标准 `git revert <commit>`；不得使用 `git reset --hard` 或改写历史。

## 8. 仍然锁定

P3–P9 仍需正式签署、伦理与知情同意、数据控制和许可、真实目标人群采集、长期个体基线、短时前兆模型、融合/时间到事件、独立外部验证、前瞻静默试运行和报警安全验证。交接文件记录状态，不授权进入这些阶段。
