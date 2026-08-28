# 老年人 AI 模拟智能手表平台：完整开发上下文交接

更新时间：2026-08-28  
交接目的：在一个新的 Codex 对话中继续开发，避免依赖旧聊天记录。  
当前开发项目：`C:\Users\yangxinyi\Documents\Codex\2026-08-27\smartwatch-health-simulator`

---

## 0. 新对话必须先做什么

新对话开始后，必须先完整阅读：

1. 本文件 `CONTEXT_HANDOFF.md`；
2. `PRODUCT.md`；
3. `DATA_AND_MODEL_NOTICE.md`；
4. `TASK_STATE.md`；
5. `DESIGN.md`；
6. `UX-CONTRACT.md`；
7. `THIRD_PARTY_NOTICES.md`。

然后先执行只读检查：

```powershell
git status --short
git log -3 --oneline
git remote -v
```

不得从空白上下文自行发明新目标。Tabler 前端迁移、“FastAPI + SQLite + WebSocket 最小本地数据闭环”和“统一案例与三模型合同”均已完成。用户在 2026-08-28 最新明确授权后续按完整大关连续推进，不需要每关等待确认；只有登录、许可申请、隐私/法律选择或外部账号操作必须由用户本人处理时才暂停。

---

## 1. 用户情况与协作方式

用户没有代码基础，希望一边学习代码知识，一边完成比赛项目。解释要求：

- 使用简体中文；
- 先讲结果，再讲原因；
- 技术词第一次出现时给通俗解释；
- 每个完整大关要总结并本地提交：完成了什么、文件在哪里、怎样运行、实测结果、还没完成什么；
- 最新授权允许完成一个大关后自动进入下一大关，不再为普通技术步骤反复确认；
- 不用随机数字或静态演示冒充真实模型结果；
- 不泄露账号、密码、令牌、验证码或隐私数据。

用户明确要求：“分步来做，每完成一步停止一下，并给出总结。”

---

## 2. 项目最终目标

开发一个必须在 Windows 电脑上打开的、具有前端和后端的“三模型模拟智能手表”可视化程序，用于比赛演示和后续研究复现。

最终用户应当无需阅读代码，就能：

1. 选择一个测试案例；
2. 按时间回放腕部传感器数据；
3. 查看三个模型分别做出的判断；
4. 查看告警原因、数据质量和输入窗口；
5. 查看数据从哪里来、属于哪种真实性类别；
6. 查看模型版本、manifest、测试指标和局限性；
7. 导出或展示测试报告。

当前只开发软件与模型，不开发实体手表硬件。以下均不在当前范围：

- ESP32；
- MPU6050；
- OLED；
- 实体智能手表结构；
- 正式医疗诊断；
- 正式救援服务；
- 未经纵向数据支持的“未来几分钟跌倒预测”。

---

## 3. 权威来源与优先级

### 3.1 当前技术与真实性边界

首要方案文档：

`C:\Users\yangxinyi\Documents\Codex\2026-08-27\mu\outputs\老年人跌倒检测与模拟手表软件方案_数据集版.md`

它是跌倒数据集、训练、防泄漏、真实性和安全表述的主要边界。

### 3.2 用户提供的参考执行计划

参考文件：

`C:\Users\yangxinyi\Documents\xwechat_files\wxid_nwhtciv09c2v12_b1a6\msg\file\2026-08\项目执行计划_老年人AI智能手表.html`

该文件只能作为项目功能、比赛展示和第三模型方向的参考，不是事实来源。文件中包含需要纠正的旧表述，例如：

- 把 SisFall 描述为大量真实老人跌倒；
- 把 UCI HAR 直接并入腕部跌倒模型；
- 没有纵向标签却宣称预测未来跌倒；
- 在未实测前写入 F1=0.89 等成绩；
- 当前范围已排除硬件，但文件仍要求 ESP32 硬件演示。

新开发不得复制这些不准确表述。

### 3.3 冲突处理顺序

如信息冲突，按以下顺序处理：

1. 用户当前明确要求；
2. `DATA_AND_MODEL_NOTICE.md`；
3. 原始数据集优先方案文档；
4. 已保存的模型 manifest、测试报告和实际命令输出；
5. `PRODUCT.md`、`UX-CONTRACT.md`、`DESIGN.md`；
6. 用户提供的参考 HTML；
7. 一般开发默认值。

任何无法证明的成绩都必须标记为“目标”或“尚未实测”。

---

## 4. 三个模型的最终分工

三个模型各自独立输出，不能简单平均三个分数，因为“跌倒概率”“规律异常分数”和“活动类别概率”不是同一个含义。

### 模型一：腕部跌倒检测

任务：识别刚刚发生的跌倒候选事件，不预测未来跌倒。

首版输入：

- 佩戴位置：腕部；
- 采样率：50 Hz；
- 窗口：4 秒；
- 样本数：200；
- 通道数：6；
- 通道：`ax, ay, az, gx, gy, gz`；
- 加速度单位：`m/s²`；
- 角速度单位：`rad/s`；
- 输入形状：`[batch, 200, 6]`。

输出：`adl` 或 `fall` 候选概率，再交给事件状态机处理，不能用单窗口概率直接宣布真实跌倒。

真实性：

- WEDA-FALL 跌倒正样本来自年轻参与者在床垫上的受控模拟；
- 77–95 岁老人只执行日常活动；
- 老人数据用于日常活动误报分析，不能说成真实老人跌倒；
- 未进行真实老人跌倒、外部数据集、长时间自由生活或 Android 验收。

### 模型二：个人生活规律异常

任务：学习一个人的用餐、午睡和散步规律，判断时间、次数、时长或缺失是否异常。

用户提供的原始压缩包：

`C:\Users\yangxinyi\Documents\xwechat_files\wxid_nwhtciv09c2v12_b1a6\msg\file\2026-08\anomaly_detection(1).zip`

压缩包实际包含：

```text
anomaly_detection/
├─ meal_learning.py
├─ nap_learning.py
├─ walk_learning.py
├─ requirements.txt
└─ outputs/
   ├─ meal_data_with_bins.csv
   ├─ nap_data_with_bins.csv
   ├─ walk_data_with_bins.csv
   └─ rules.json
```

当前实际逻辑：

- 三个 Python 脚本分别生成 100 天吃饭、午睡、散步合成数据；
- 吃饭脚本固定 `numpy` 随机种子 42；
- 午睡和散步脚本的随机种子被注释，当前运行结果不能完全复现；
- 吃饭和散步通过 KDE（核密度估计）寻找时间段分割点；
- 使用 IQR 去除极端时间；
- 用均值 ± `1 × 标准差` 形成规律区间；
- 区间内为正常，区间外按早/晚和偏差量判异常；
- 当前主要检测“发生时间异常”，还不是完整的多维生活规律模型；
- 午睡脚本生成了时长字段，但当前异常判断主要仍看时间；
- 没有严格的训练/验证/测试划分和真实用户评估；
- `rules.json` 当前是服药、睡眠、起床、饭后和喝水提醒规则，不是三个学习器统一导出的模型 manifest；
- `requirements.txt` 没有直接列出脚本实际导入的 `scipy`，后续要修正依赖锁定。

因此当前只能准确称为：

> “基于 100 天合成生活事件的统计规律区间与异常检测原型。”

不能称为已用真实老人数据训练完成的机器学习模型，也不能声称已有泛化指标。

后续接入前需要：

1. 解压到项目受控目录并登记原始哈希；
2. 固定随机种子；
3. 分离数据生成、规律学习、异常检测和序列化；
4. 统一用餐、午睡和散步事件 schema；
5. 增加缺失、次数、时长等异常；
6. 生成模型二 manifest；
7. 建立合成测试集和边界测试；
8. 明确界面标记 `SYNTHETIC_ROUTINE`。

### 模型三：腕部活动识别

任务：把腕部加速度翻译为后续规律模型能使用的生活事件候选。

首版建议输入：

- 采样率：20 Hz；
- 窗口：20 秒；
- 样本数：400；
- 通道：三轴加速度；
- 输入形状：`[batch, 400, 3]`。

首版候选类别：

- 走路；
- 进食候选；
- 睡眠/躺卧候选；
- 其他/未知。

当前状态：尚未下载活动识别数据、尚未训练、尚无 ONNX、尚无实测指标。

可能参考的开源路线已登记在 `THIRD_PARTY_NOTICES.md`，包括 CAPTURE-24、ActiNet、SSL Wearables、LIMU-BERT、Transformer HAR、LSTM HAR。真正引入前必须重新核验许可证、数据参与者、设备位置、字段和标签。

---

## 5. 已有跌倒模型的真实状态

跌倒模型独立仓库：

`C:\Users\yangxinyi\Documents\Codex\2026-08-27\elderly-fall-model-development`

GitHub 远程：

`https://github.com/yangxinyi0731-cmd/watch-fall-detection-model.git`

已核对 manifest：

`C:\Users\yangxinyi\Documents\Codex\2026-08-27\elderly-fall-model-development\models\fall_detector\tcn_final_candidate\manifest.json`

模型文件状态：

- ID：`fall_detector_tcn_final_candidate`；
- 版本：`0.2.0-dev`；
- 格式：ONNX；
- SHA-256：`1e214ebd89fce6620cf09a7a071aa904cd5ca0932e960181ce43c3695e212a3f`；
- 参数量：3025；
- 文件大小：16180 bytes；
- `deployment_approved=false`；
- WEDA-FALL 固定源提交：`74e0b93cb061d4ecbca12628f2d47090e97fbeea`；
- 训练范围：25 名参与者、969 条记录、8886 个窗口；
- 配置：`configs/tcn_final.json`；
- 随机种子：`20261827`；
- 训练 8 epochs。

预先固定阈值 0.5 的 25 折 LOSO 开发评估：

- 事件级 Recall：0.9742857143；
- 事件级 Precision：0.7560975610；
- 事件级 F1：0.8514357054；
- 误报事件：110；
- 回放时长：12209.6 秒；
- 误报率：32.4335 次/回放小时；
- 试验级混淆矩阵：`[[513, 99], [9, 341]]`；
- 老人 ADL 误报事件：14；
- 老人 ADL 误报率：29.6995 次/回放小时。

阈值 0.7 的事后开发选择结果：

- 事件级 Recall：0.9142857143；
- Precision：0.8311688312；
- F1：0.8707482993；
- 误报事件：65；
- 误报率：19.1652 次/回放小时；
- 老人 ADL 误报事件：6；
- 老人 ADL 误报率：12.7283 次/回放小时；
- 试验级混淆矩阵：`[[552, 60], [30, 320]]`。

阈值 0.7 是查看 WEDA-FALL 折外标签后选择的开发工作点，必须标记 `posthoc_development_only_requires_external_confirmation`。不能用它证明独立泛化能力。

主报告仍应优先展示预先固定阈值 0.5 的 LOSO 结果，并突出当前误报率很高、未通过部署审批。

Windows CPU 主机延迟实测仅代表当前电脑：

- 200 次运行；
- median 约 0.1602 ms；
- p95 约 0.1762 ms；
- 不是 Android 或真实手表性能。

正式应用模式必须拒绝 `deployment_approved=false` 的模型；比赛研究演示模式可以在清晰警告下加载。

---

## 6. 数据集与真实性边界

### 6.1 跌倒模型优先数据

- WEDA-FALL：主训练与老人日常活动误报分析；腕部 Fitbit Sense、50 Hz、六轴；老人没有跌倒正样本。
- SmartFallMM：老人日常活动和跨设备补充；跌倒仍主要由年轻人执行。
- UP-Fall 腕部通道：年轻参与者实验室模拟跌倒，用于外部泛化测试，不是老人数据。
- FARSEEING：真实老年人意外跌倒，但需要申请，佩戴位置不统一，不能冒充腕表主训练集。
- BITS-2：可选腕部补充，参与者主要较年轻，实验室模拟。
- SisFall：腰部设备，不并入腕部主训练。
- UCI HAR：腰部手机、无跌倒标签，不并入腕部跌倒主模型。

### 6.2 100 个测试案例的正确含义

用户希望找到“100 个开源、具体、确切、真实、较新的数据实例”作为模拟手表测试数据。

可实现的严谨版本是：

> 建立 100 个来源可追溯的测试案例，每个案例对应公开数据集中的一段真实采集记录或明确的派生/合成记录。

不能承诺 100 个都是真实老人跌倒，因为公开、腕部、真实老人意外跌倒三者同时满足的数据非常少。

每个案例必须登记：

- `case_id`；
- 数据集；
- 来源 URL；
- 固定版本或下载日期；
- 文件哈希；
- 许可证/使用条件；
- 参与者匿名 ID；
- 年龄组；
- 设备和佩戴位置；
- 原始采样率；
- 字段和单位；
- 活动标签；
- 真实性类别；
- 允许进入哪个模型；
- 是否有陀螺仪；
- 处理命令与派生关系。

不得把缺失的陀螺仪通道补全为全零并假装是真实六轴数据。

### 6.3 界面真实性类别

- `REAL_FREE_LIVING`：真实自由生活记录；
- `REAL_LAB_ACTIVITY`：真实参与者执行的受控活动；
- `SIMULATED_FALL`：受控模拟跌倒；
- `SYNTHETIC_ROUTINE`：程序生成的生活规律；
- `DERIVED_PERTURBATION`：真实数据上的明确派生异常。

### 6.4 训练防泄漏要求

- 原始数据只读保存；
- 必须先按参与者分组，再切窗口；
- 首选 LOSO；
- 或 GroupKFold，`groups=subject_id`；
- 严禁随机拆分重叠窗口；
- 回放测试保留完整时间顺序；
- 使用事件级 Recall、Precision、F1、误报次数/小时或天、检测延迟和混淆矩阵；
- 不用窗口 Accuracy 替代事件级评估；
- 不让老人或无专业保护的人员模拟跌倒。

---

## 7. 新平台的技术架构

当前确定的方向：

```text
Windows 电脑浏览器中的 Vue 前端
               ↓ HTTP / WebSocket
              FastAPI
               ↓
       SQLite v2 + 来源/案例/传感器/回放/模型输出
               ↓
          三个模型适配器
        ├─ 跌倒 ONNX
        ├─ 规律异常
        └─ 活动识别 ONNX
```

技术栈：

- 前端：Vue 3 + TypeScript + Vite；
- 后端：FastAPI；
- 数据库：SQLite；
- 实时通道：WebSocket；
- 模型部署：ONNX Runtime；
- 运行原则：本地优先、尽量离线、Windows 电脑可直接打开；
- 最终交付：一键启动或桌面包装，具体方式后续验证后决定。

三模型必须通过统一适配器接入，但保持各自语义，不生成未经校准的综合医学风险分数。

---

## 8. 新平台当前已完成状态

项目路径：

`C:\Users\yangxinyi\Documents\Codex\2026-08-27\smartwatch-health-simulator`

本地 Git：

- 当前开发分支：`codex/tabler-ui-migration`；
- 初始平台提交：`57034ba chore: establish smartwatch simulator foundation`；
- Tabler 迁移从 `4d53e93 docs: hand off Tabler migration context` 之后开始；
- 当前尚未创建新平台的 GitHub 远程仓库；
- 不要与已有跌倒模型仓库混淆。

已创建：

- Vue 3 + TypeScript + Vite 前端；
- Tabler 风格 AppShell、桌面侧栏、顶部工具栏和窄屏导航；
- 实用的小型设备/回放状态面板；
- 三模型连续状态列表；
- 数据真实性与来源面板；
- 共享 `AppCard`、`StatusBadge` 和 `EmptyState` 组件；
- 共享 `AppButton` 和真实系统连接状态组合式函数；
- FastAPI `GET /api/health` 健康检查；
- WebSocket `/ws/system` 实时状态；
- SQLite 结构版本 1、迁移记录和空案例表；
- Pydantic 统一来源、案例、传感器窗口、三模型输出、回放事件和模型 manifest 合同；
- SQLite 结构版本 2：`data_sources`、扩展 `cases`、`sensor_streams`、`model_manifests`、`replay_sessions`、`replay_events`、`model_outputs`；
- `GET /api/contracts` 和服务端分页 `GET /api/cases`；
- OpenAPI、领域 JSON Schema 和前端 TypeScript 自动生成链；
- 近期相似开源项目 HEAD、许可与采用/排除记录；
- 前端自动重试、旧请求取消和手动“刷新状态”；
- 后端健康检查、WebSocket 和数据库版本自动测试；
- `PRODUCT.md`；
- `DATA_AND_MODEL_NOTICE.md`；
- `DESIGN.md`；
- `UX-CONTRACT.md`；
- `THIRD_PARTY_NOTICES.md`；
- `TASK_STATE.md`；
- 后端、模型、数据、测试和文档目录。

当前页面的后端、SQLite 和 WebSocket 状态来自真实连接；运行态已实测 FastAPI `v0.3.0` 和 SQLite 结构版本 2。“0 个案例”“待训练”“暂无数据”也是真实状态，不是演示填充。

明确未完成：

- 100 案例；
- 100 个真实来源案例及其传感器文件；
- 模型二正式接入；
- 模型三训练；
- 跌倒 ONNX 接入新平台；
- 新平台 GitHub 远程；
- Windows 一键交付包。

### 8.1 Tabler 迁移已执行的验证

- `npm install` 成功；
- 54 个 npm 软件包审计，0 个已知漏洞；
- `npm run build` 成功；
- Vue 类型检查成功；
- Vite 生产构建成功；
- `designmd lint DESIGN.md`：0 错误、0 警告；
- Premium 严格审计：0 错误、0 警告、0 未解决项；
- 反模式检查：无原生弹窗、假链接、非语义点击、旧 AI 风格关键词或持续动画；
- 浏览器控制台：0 错误、0 警告；
- 1440×900：无页面横向溢出；
- 1024×768：两列系统状态、单列工作区，无页面横向溢出；
- 390×844：顶部横向导航与单列内容，无页面横向溢出；
- 键盘跳转链接焦点可见；
- 所有页面锚点都有真实目标，未开放功能不是链接；
- 页面没有持续动画，并保留 `prefers-reduced-motion` 降级规则；
- 实际浏览器验证使用 Codex 应用内 Chromium；当前任务未连接用户 Chrome/Edge 扩展，因此不得写成已完成用户 Chrome 专项验收。

### 8.2 最小本地数据闭环验证

- 后端 4 个自动测试通过，无警告；
- Python `pip check` 无依赖冲突，锁定清单与实装环境一致；
- 前端类型检查和 Vite 生产构建通过；
- npm 审计 0 个已知漏洞；
- DESIGN lint 0 错误 / 0 警告；
- Premium 严格审计 0 findings；
- 离线、连接、运行中断线、重新启动自动恢复和手动刷新均已在真实 Chromium 中验证；
- 1440×900、1024×768、390×844 均无页面级横向溢出；
- 浏览器控制台 0 错误 / 0 警告；
- Google Chrome 已安装，但 ChatGPT/Codex Chrome 控制扩展未安装，本轮浏览器验收使用 Codex 应用内 Chromium，不能称为 Chrome 专项兼容性验证。

### 8.3 当前运行命令

```powershell
cd "C:\Users\yangxinyi\Documents\Codex\2026-08-27\smartwatch-health-simulator"
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

另开一个位于同一项目根目录的 PowerShell：

```powershell
npm --prefix frontend run dev
```

默认前端地址通常为：`http://127.0.0.1:5173/`；健康检查为 `http://127.0.0.1:8000/api/health`。

生产构建：

```powershell
npm --prefix frontend run build
```

---

## 9. 已确认的 Tabler 前端设计决定

用户已明确选择：

> 前端方案 B：Tabler。

官方来源：

- 演示：`https://preview.tabler.io/`
- GitHub：`https://github.com/tabler/tabler`
- 文档：`https://docs.tabler.io/`
- 许可证：MIT；正式引入时保留 LICENSE、版权和第三方登记。

### 9.1 总体原则

Tabler 只作为视觉系统和必要组件来源，不把整个演示后台复制进来。

保留当前 Vue 3、TypeScript、Vite 和业务目录。不要改成纯 HTML，不要引入无用的登录、员工、商品、订单、邮件、聊天、财务和权限演示页面。

目标风格：

> 普通、专业、清楚、稳定的健康监测后台；像真实电脑软件，不像 AI 生成的概念展示页。

### 9.2 采用的 Tabler 元素

- 浅色后台页面框架；
- 左侧功能导航；
- 顶部工具栏；
- 无衬线字体；
- 白色/浅灰工作区；
- 细边框、小圆角、少阴影；
- 标准卡片、表格、按钮、表单；
- 状态标签；
- 空数据、加载和错误状态；
- Tabler 风格线性图标；
- 响应式布局。

建议首版导航：

```text
系统总览
案例库
实时回放
三模型中心
  ├─ 跌倒检测
  ├─ 规律异常
  └─ 活动识别
告警记录
测试报告
数据与来源
```

### 9.3 必须删除或改造的“AI 感”元素

- 删除巨大宣传口号“先看懂，再相信每一次判断”；
- 页面标题改成“系统总览”等普通功能标题；
- 删除大号宋体展示标题；
- 删除全页面方格纸背景；
- 删除装饰性巨大手表外壳；
- 将手表改成实用的小型回放/设备状态面板；
- 删除持续呼吸的圆环动画；
- 删除无真实运行含义的环境动画；
- 减少大圆角、软阴影和过量留白；
- 删除装饰性 `WATCH / 001`；
- 删除没有流程含义的 `01 / 02 / 03`；
- 减少到处出现的胶囊标签；
- 不使用含糊宣传词，如“开启守护”“智慧洞察”。

### 9.4 必须保留的项目特点

- 模拟手表数据回放；
- 三个模型的独立状态和结果；
- 六轴/三轴波形；
- 活动时间线；
- 告警事件；
- 数据真实性标签；
- 来源追溯；
- 模型 manifest；
- “没有数据就显示没有数据”；
- 简体中文和通俗解释；
- 绿色正常、橙色关注、红色紧急、蓝色信息；
- 不用颜色作为唯一状态表达。

### 9.5 推荐迁移方式

采用“轻量接入”，不是整体替换工程：

1. 保留 Vue/Vite/TypeScript；
2. 在动手前核验 Tabler 当前稳定版本、包名、许可证和依赖；
3. 只引入需要的 Tabler 基础样式和图标；
4. Vue 自己管理菜单、折叠、下拉和业务状态；
5. 建立共享 AppShell、Navigation、StatusBadge、Card、EmptyState 等基础组件；
6. 先迁移静态首页；
7. 验证后再删除旧样式；
8. 同步更新 `DESIGN.md`、`UX-CONTRACT.md` 和 `THIRD_PARTY_NOTICES.md`。

不要让旧 CSS 与 Tabler CSS 长期混杂，也不要一次性无验证地删除当前页面。

### 9.6 已识别风险

1. Tabler 核心不是专门为当前 Vue 工程制作，交互不能盲目复制 HTML 示例；
2. Tabler/Bootstrap 样式可能与当前 CSS 冲突；
3. 完全照搬会失去智能手表项目特点；
4. Tabler 信息密度较高，需要为无代码用户保留说明；
5. 必须保留 MIT 许可和版权；
6. 必须固定版本，避免比赛前自动升级；
7. 采用模板不等于自动满足可访问性，仍需重新测试。

---

## 10. 当前完成点与连续推进边界

Tabler 前端迁移、最小本地数据闭环和统一合同大关已经完成：FastAPI、SQLite 结构版本 2、WebSocket、前端真实连接状态、Pydantic 合同、OpenAPI/JSON Schema 和案例分页均已实现并测试。

用户已经授权连续推进。当前下一大关是：

> 核验并导入可公开追溯的数据与 100 个测试案例。先建立来源登记和导入器，原始大文件只读且不进入 Git，每个案例必须保存哈希、处理命令、真实性类别和允许进入的模型。

仍然不允许：

- 未核验许可就重新分发或商用公开下载的数据；
- 把测试夹具或随机波形凑成 100 个案例；
- 把缺少陀螺仪的案例补零后送入六轴跌倒模型；
- 创建或推送新平台 GitHub 仓库，除非用户另行明确授权外部发布；
- 改变已有跌倒模型仓库；
- 声称新增任何模型指标。

---

## 11. 后续完整阶段路线

按用户最新“完整大关连续推进”的约定执行：

1. 已完成：独立本地仓库、Vue 空壳、产品/真实性/设计/交互合同；
2. 已完成：Tabler 风格迁移；
3. 已完成：建立 FastAPI、SQLite、WebSocket，并让前端状态来自真实健康检查；
4. 已完成：定义三个模型统一输入输出、案例 schema、回放事件和 manifest；
5. 进行中：核验并导入可公开追溯的数据与 100 个测试案例；
6. 接入跌倒模型和事件级解释；
7. 重构并接入个人规律异常模型；
8. 开发模型三的数据管线；
9. 训练、分组评估并报告模型三；
10. ONNX 导出与统一推理服务；
11. 开发回放时间线、波形、告警和证据可视化；
12. 案例选择、批量测试和比赛演示流程；
13. 来源、模型卡、测试报告和导出页面；
14. 端到端、性能、异常恢复、离线和无障碍验证；
15. Windows 一键启动或桌面交付包；
16. 创建并推送新平台 GitHub 仓库，整理答辩交付。

顺序可在用户明确确认后调整，但不能把未经验证的后期能力显示成已完成。

---

## 12. 必须持续遵守的表述

可以说：

> 我们使用腕部数据训练研究原型。WEDA-FALL 的跌倒由年轻参与者在受控环境中模拟，老人参与者只提供日常活动；这些老人日常活动用于重点分析误报。当前模型没有完成真实老人跌倒和外部独立验证，不能作为医疗器械或正式救援系统。

不能说：

- “训练集中有大量真实老人跌倒”；
- “模型能预测未来 5 分钟跌倒”；
- “100 个案例都是真实老人跌倒”；
- “手机数据等于腕部手表数据”；
- “模型已达到临床级准确率”；
- “F1=某数值”，除非同时说明模型版本、数据集、参与者分组、阈值和评估方法；
- “三个模型的概率平均后就是健康风险”；
- “模型二已用真实老人数据训练完成”；
- “模型三已训练”，因为当前尚未开始。

---

## 13. 文件导航

```text
smartwatch-health-simulator/
├─ CONTEXT_HANDOFF.md          # 本交接文件
├─ PRODUCT.md                  # 产品目标和三模型职责
├─ DATA_AND_MODEL_NOTICE.md    # 真实性硬边界
├─ TASK_STATE.md               # 当前步骤和验证结果
├─ DESIGN.md                   # 当前设计系统；Tabler 迁移时同步更新
├─ UX-CONTRACT.md              # 交互、状态、导航、恢复和无障碍合同
├─ THIRD_PARTY_NOTICES.md      # 开源来源登记
├─ premium-ui.json             # 严格审计配置
├─ premium-audit.json          # 最近静态审计证据
├─ frontend/                   # Vue 3 + TypeScript + Vite
├─ backend/                    # FastAPI、SQLite、WebSocket 与自动测试
├─ models/                     # 后续三模型适配器
├─ data/
│  ├─ catalog/                 # 数据来源登记
│  └─ cases/                   # 统一案例
├─ tests/                      # 后续自动测试
└─ docs/ARCHITECTURE.md        # 当前系统结构
```

---

## 14. 下一对话可直接使用的启动指令

```text
请继续开发“老年人 AI 模拟智能手表平台”。项目路径是：
C:\Users\yangxinyi\Documents\Codex\2026-08-27\smartwatch-health-simulator

开始前完整阅读项目根目录的 CONTEXT_HANDOFF.md，并按其权威顺序继续阅读 PRODUCT.md、DATA_AND_MODEL_NOTICE.md、TASK_STATE.md、DESIGN.md、UX-CONTRACT.md 和 THIRD_PARTY_NOTICES.md。先执行只读 Git 检查并报告。

Tabler 前端迁移、最小本地数据闭环和统一合同已经完成并保存在 codex/tabler-ui-migration 分支：FastAPI 健康检查、SQLite 结构版本 2、WebSocket 系统状态、统一 Pydantic/OpenAPI/JSON Schema、前端生成类型、案例分页、自动重连和手动刷新均已实现。案例实数仍为 0，三个模型仍未接入。

不要重复 Tabler 迁移、本地数据闭环或 schema 第 2 版。先报告当前分支、提交、工作区和验证状态，然后继续来源登记和 100 案例导入；普通大关不需要再次确认。只有登录、许可申请、隐私/法律选择、外部账号操作或 GitHub 发布需要用户本人处理时暂停。
```

---

## 15. 当前交接结论

项目不是从零开始：Vue 3 + TypeScript + Vite、Tabler 工作台、真实性/交互合同、FastAPI + SQLite + WebSocket 本地闭环，以及统一案例/模型/回放合同已经完成；跌倒 ONNX 仍只存在于独立仓库，且未获部署批准。

当前进入来源登记和 100 案例导入大关。可以自动继续不需要外部许可的工作，但不得为了凑数编造案例；需要申请访问的数据源只记录为阻塞候选，不伪装成已使用。
