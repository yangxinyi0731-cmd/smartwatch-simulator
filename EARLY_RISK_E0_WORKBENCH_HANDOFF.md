# 模拟智能手表检测台：E0 前端改版完成交接

更新时间：2026-08-31

实际仓库：`C:\Users\yangxinyi\Documents\Codex\2026-08-27\smartwatch-health-simulator`

当前分支：`codex/early-risk-e0-workbench`

基础提交：`75745e0ad0690126bde84c91df612b7f5b95a986`

生活化改版起点：`2d72a770d116424cbcaa74df6a944af20670568d`

本次前端改版起点：`4f6df8feeaba64cbba2a9b074b981c9f595f689f`

## 1. 当前结论

P0+P1+P2 的版本化合同、资产审计、确定性夹具、Gate 和 dry-run 策略已经形成可在 Windows 本机直接打开的独立页面。固定地址为 `http://127.0.0.1:8010/`。本次在不修改后端、模型和数据合同的前提下，把原来的生活化说明页改成可操作的模拟智能手表检测台：左侧选择 105 组案例，中间操作模拟手表，右侧核对四步判断和已保存结果。

这个成品仍是 E0 工程演示，不是 P9 老人风险界面。页面中的起身、散步、弯腰、快速坐下、坐车颠簸、甩水和摘表等内容只解释未来产品逻辑，不表示当前模型已识别成功。它不会把人工夹具或现有三个模型包装成真实老人“提前几秒预测”，不会写 SQLite，不会训练模型，也不会振动、发声、联系家属或触发救援。

## 2. 用户打开方式

完成仓库 `README.md` 的首次安装后，进入 `scripts\windows`：

- 双击 `start-early-risk-workbench.cmd`：启动并打开工作台；
- 双击 `stop-early-risk-workbench.cmd`：核对 PID、Python 路径和启动时间后停止；
- 双击 `diagnose-early-risk-workbench.cmd`：只读检查证据、依赖、安全边界和运行状态。

健康检查：`http://127.0.0.1:8010/api/health`

运行日志和进程状态位于 Git 忽略目录 `backend/runtime/early-risk-workbench/`。启动脚本可安全重复执行；已经运行时会复用现有进程。

## 3. 评委打开后可以操作什么

- 在案例库查看全部 105 组案例，并按受控跌倒 40、日常活动 60、活动识别 4、生活规律 1 分类筛选；
- 搜索案例编号、短标题或参与者，每页查看 6 条并翻页；
- 选择案例后，让模拟手表同步显示来源、编号、采样率、传感器轴数和当前阶段；
- 使用开始、暂停、继续和重置，观察“读取腕部数据—整理连续窗口—独立模型判断—结果复核”四步过程；
- WEDA-FALL 案例完成后查看仓库已经保存的最高候选概率与候选段摘要；
- CAPTURE-24 与合成规律只显示案例就绪，不伪造当前不存在的逐样本回放；
- 在模型状态中直接看到未来几秒风险预测仍为“后端尚未接入 / 锁定”；
- 在说明与边界展开区查看生活化目标、困难正常动作和 P3–P9 仍需完成的事项。

所有夹具数字均显示技术名和“工程夹具”，并在互动区直接说明“只演示、不报警”。后端始终强制 `dry_run=true`，客户端不能关闭，也没有外部通知收件人或发送接口。

## 4. 架构与隔离

页面由 `research.early_risk.workbench_server` 和 `research/early_risk/workbench/` 静态界面组成，只监听 `127.0.0.1:8010`。案例搜索、筛选、分页和四步检测阶段完全在静态前端中切换，不调用或修改模型。它独立于现有 `backend.app.main`、Vue 产品、SQLite 和三个研究模型运行路径。

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
- 应用内 Chromium 实测桌面 `1440×900`、`390×844` 竖屏和 `844×390` 横屏均无页面级横向溢出；所有可见按钮、输入框和链接操作目标至少 `44×44px`；
- 105 组总数与 `40 / 60 / 4 / 1` 分类、6 条分页、类型筛选、搜索、清除、翻页后案例/手表/判断区同步均通过；
- 开始、暂停、继续和重置通过；受控跌倒显示已保存候选摘要，受控日常活动能显示“误报候选”，CAPTURE-24 显示“活动案例已就绪”，合成规律显示“规律规则已登记”，外部通知始终为 0；
- DOM 验收为单一 `h1`、重复 ID `0`、未标注字段 `0`、无名称按钮 `0`、缺少 `novalidate` 的表单 `0`；`DESIGN.md` lint 为 `0` 错误、`0` 警告，Premium 严格审计为 `0` findings。

机器可读的界面审计见 `reports/early_risk/e0/workbench-premium-audit.json`，完整交付核验摘要见 `reports/early_risk/e0/workbench-verification.json`。

## 7. Git 与恢复

本分支从 `75745e0…` 创建，与原有三模型产品提交隔离。没有 Git remote，也没有推送。需要撤销本次成品时，先确认当前分支和提交，再对本次交付提交执行标准 `git revert <commit>`；不得使用 `git reset --hard` 或改写历史。

## 8. 仍然锁定

P3–P9 仍需正式签署、伦理与知情同意、数据控制和许可、真实目标人群采集、长期个体基线、短时前兆模型、融合/时间到事件、独立外部验证、前瞻静默试运行和报警安全验证。交接文件记录状态，不授权进入这些阶段。
