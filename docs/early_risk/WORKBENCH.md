# 模拟手表风险评估工作台（校赛研究版）

更新时间：2026-09-01

## 定位

`http://127.0.0.1:8010/` 现在是一个可真实运行模型的本机风险评估工作台，而不是产品介绍页。评委既可以选择 105 组已登记公开案例，也可以上传一段新的六轴记录。系统会依次完成传感器校验、采样率和单位统一、活动识别、跌倒候选筛查、1/2/3 秒公开数据研究基线、波形展示和格式化结论。

自主采集登记必须保持 `0/约30组`，直到收到真实文件。当前没有用随机数据、复制的公开案例或静态前端结论填充这一栏。

## 当前完成的模型能力

第四个研究模型保存在：

- `models/early_risk/public_weda_linear_v1/model.json`；
- `models/early_risk/public_weda_linear_v1/manifest.json`；
- `reports/early_risk/public_weda_linear_v1.json`。

它使用 WEDA-FALL 50 Hz 六轴记录和数据集提供的跌倒区间开始时间，训练三个独立逻辑回归头。每个输出只读取当前时刻之前的 1 秒窗口，分别估计该公开受控模式是否接近未来 1、2、3 秒内的跌倒区间开始。训练、阈值校准、最终评估按参与者完全隔离；模型保存为可由 NumPy 直接执行的可移植 JSON 参数，不依赖浏览器中的静态数值。

必须使用准确名称“数据集跌倒区间开始代理锚点”。它不是专家判定的 `t_instability`，也不是现实意外跌倒的真实失稳起点。页面中的三个数值是与公开受控代理标签的研究分数，不是现实个人跌倒概率。

## 新数据检测

支持标准 `.csv` 和 `.json`，具体格式见 `NEW_DATA_FORMAT.md`。首版请求流程是：

```text
选择六轴文件
  → 检查时间、加速度和陀螺仪
  → 把加速度统一为 m/s²、角速度统一为 rad/s
  → 插值到 50 Hz
  → 活动识别（至少 20 秒）
  → 跌倒候选筛查（至少 4 秒）
  → 1/2/3 秒研究模型（至少 1 秒）
  → 实际波形、逐秒风险曲线、判断依据与最终结论
```

上传文件最大 5 MB，只在进程内存中处理，不写 SQLite、不加入案例库、不进入 Git，刷新页面后不保留。结果分别显示数据质量、当前动作候选、跌倒动作筛查、实测依据和最终结论；不得生成“综合风险 78 分”一类无法追溯的合成分数。

## 页面结构

- 侧栏六个真实锚点都包含简体中文副标题：“新数据检测、实时检测、案例回放、判断过程、模型状态、说明与边界”。任何时刻只有一个 `aria-current`。
- “新数据检测”是首要工作流：文件选择器、单位选项、六步实际处理状态和结果区域。失败时保留所选文件并显示文字错误，可修正后重试。
- 公共案例区继续保留 105 组案例、类型筛选、搜索、6 条分页、模拟手表和开始/暂停/重置。
- 六轴 WEDA 案例的证据接口会在请求时真实运行跌倒模型和提前风险模型；动作示意仍明确标为非证据，实际判断依据来自本机核验文件的波形和模型输出。
- 1/2/3 秒图用三种颜色和三种线型共同区分，并同时显示各自关注阈值；受控跌倒案例另显示代理锚点竖线。图下方提供不依赖颜色的文字摘要。
- 四个模型分别给出中文释义，结果保持独立。活动候选、跌倒候选、提前风险研究分数和生活规律异常不得合成为医学分数。

## 接口

| 方法 | 路径 | 用途 | 持久化 |
|---|---|---|---|
| GET | `/api/health` | 核验回环范围、模型状态、自主采集状态和通知关闭状态 | 否 |
| GET | `/api/workbench` | 返回公开模型报告、0/30 登记状态、E0 合同和案例摘要 | 否 |
| GET | `/api/case-evidence/{case_id}` | 核对本机案例文件；六轴案例同时运行真实模型 | 否 |
| POST | `/api/analyze-upload` | 解析新文件、统一输入、运行三个传感器模型并生成解释 | 否 |
| POST | `/api/simulate` | 保留原有确定性 dry-run 策略测试 | 否 |
| GET | `/evidence/{allowlisted-name}` | 下载白名单内的合同、模型报告和格式说明 | 否 |

动态响应使用 `Cache-Control: no-store`。服务仍只允许绑定 `127.0.0.1` 或 `localhost`，设置 CSP、`nosniff`、`DENY` frame、同源资源和无引用来源等响应头。

## 自主采集最后一公里

空登记位于 `data/catalog/self_collected_pending_v1.json`：

- 目标约 30 组；
- 当前收到 0 组；
- 当前接受 0 组；
- `cases=[]`；
- 最终校赛表述未启用。

收到真实文件后只剩：文件哈希登记、动作/场景标签人工复核、质量检查、参与者隔离工程验证、页面导入和最终报告冻结。没有真实文件之前，软件只能写“公开数据模型与新文件分析链路已完成，自主采集验证待接入”。

## 真实性边界

- 公开正例是参与者在床垫条件下完成的受控模拟跌倒，不是真实意外跌倒。
- WEDA 时间标签只是数据集区间开始代理锚点，不是经专家判定的失稳起点。
- 精确提前 1/2/3 秒快照的分母必须与命中数同时显示，不能只展示百分比。
- `prediction_evidence=false` 继续表示没有现实环境预测证据；同时新增 `public_proxy_model_ready=true`，两者不能混为一件事。
- `self_collected_validation_complete=false`、`deployment_approved=false`、外部通知 0 次。
- 不振动、不发声、不联系家属、不接救援、不作医疗诊断。

## 启动与验证

完成仓库首次依赖安装后，可双击 `scripts\windows\start-early-risk-workbench.cmd`。停止与诊断分别使用 `stop-early-risk-workbench.cmd` 和 `diagnose-early-risk-workbench.cmd`。

关键命令：

```powershell
.\.venv\Scripts\python.exe -m research.early_risk.train_public_risk_baseline
.\.venv\Scripts\python.exe -m pytest .\tests\early_risk -q
.\.venv\Scripts\python.exe -m pytest .\backend\tests -q
node --check .\research\early_risk\workbench\app.js
npm --prefix frontend run build
npx -y -p @google/design.md designmd lint DESIGN.md
.\.venv\Scripts\python.exe C:\Users\yangxinyi\.codex\plugins\cache\openai-curated-remote\frontend-design-premium\1.4.0\skills\frontend-design-premium\scripts\audit_project.py . --mode strict --output reports\early_risk\e0\workbench-premium-audit.json
```

浏览器验收必须覆盖：合法上传、缺列失败、短记录降级、文件移除和重试；桌面与 `390×844`；键盘文件选择和焦点回到结果标题；逐秒图、阈值、代理锚点、波形文字摘要；105 组案例选择与手表同步；自主采集始终为 0；控制台无错误且页面无横向溢出。
