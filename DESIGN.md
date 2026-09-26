---
version: alpha
name: "模拟智能手表"
description: "面向比赛演示、案例回放与研究复核的本机模拟智能手表检测软件"
colors:
  ink: "#182433"
  ink-muted: "#667382"
  canvas: "#f6f8fb"
  surface: "#ffffff"
  surface-subtle: "#f8fafc"
  line: "#dce1e7"
  primary: "#206bc4"
  primary-soft: "#e9f2ff"
  success: "#2fb344"
  success-soft: "#eaf7ec"
  warning: "#f59f00"
  warning-soft: "#fff5db"
  danger: "#d63939"
  danger-soft: "#fdecec"
  focus: "#206bc4"
  scrollbar-thumb: "#a8b2bf"
  scrollbar-track: "#edf0f4"
  simulator-header: "#284b4a"
  simulator-sidebar: "#f7f8f6"
  simulator-canvas: "#f3f5f4"
  simulator-teal: "#20786f"
  simulator-watch: "#071b22"
  simulator-line: "#d8e2dd"
  simulator-line-strong: "#c2d0c8"
typography:
  heading:
    fontFamily: "Segoe UI, Microsoft YaHei UI, PingFang SC, Noto Sans CJK SC, system-ui, sans-serif"
  body:
    fontFamily: "Segoe UI, Microsoft YaHei UI, PingFang SC, Noto Sans CJK SC, system-ui, sans-serif"
  data:
    fontFamily: "Cascadia Mono, SFMono-Regular, Consolas, monospace"
rounded:
  DEFAULT: "0.375rem"
  sm: "0.25rem"
  md: "0.375rem"
  lg: "0.5rem"
spacing:
  page-inline: "2rem"
  section-gap: "1rem"
  panel-gap: "1rem"
  sidebar-width: "15rem"
components:
  app-shell:
    backgroundColor: "{colors.canvas}"
    textColor: "{colors.ink}"
  navigation:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink-muted}"
    rounded: "{rounded.md}"
  navigation-current:
    backgroundColor: "{colors.primary-soft}"
  primary-marker:
    backgroundColor: "{colors.primary}"
  divider:
    backgroundColor: "{colors.line}"
  app-card:
    backgroundColor: "{colors.surface-subtle}"
    rounded: "{rounded.lg}"
  app-button:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.md}"
  connection-message:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink-muted}"
    rounded: "{rounded.md}"
  status-success:
    backgroundColor: "{colors.success-soft}"
  status-success-marker:
    backgroundColor: "{colors.success}"
  status-warning:
    backgroundColor: "{colors.warning-soft}"
  status-warning-marker:
    backgroundColor: "{colors.warning}"
  status-danger:
    backgroundColor: "{colors.danger-soft}"
  status-danger-marker:
    backgroundColor: "{colors.danger}"
  focus-ring:
    backgroundColor: "{colors.focus}"
  scrollbar-thumb:
    backgroundColor: "{colors.scrollbar-thumb}"
  scrollbar-track:
    backgroundColor: "{colors.scrollbar-track}"
  simulator-shell:
    backgroundColor: "{colors.simulator-canvas}"
    textColor: "{colors.ink}"
  simulator-sidebar:
    backgroundColor: "{colors.simulator-sidebar}"
    textColor: "{colors.ink}"
  simulator-header:
    backgroundColor: "{colors.simulator-header}"
    textColor: "{colors.surface}"
  simulator-primary-action:
    backgroundColor: "{colors.simulator-teal}"
    textColor: "{colors.surface}"
  simulator-watch-device:
    backgroundColor: "{colors.simulator-watch}"
    textColor: "{colors.surface}"
  simulator-subtle-divider:
    backgroundColor: "{colors.simulator-line}"
  simulator-strong-rule:
    backgroundColor: "{colors.simulator-line-strong}"
---

# 模拟智能手表设计系统

## Overview

### Creative North Star

现有三模型产品继续以“医院或研究机构里的健康监测工作台”为参照：导航明确、密度适中、状态可以快速扫描，证据比装饰更醒目。独立校赛页面采用 Nobi 电脑端照护工作台的空间层级作为参考：深色通栏顶栏、浅色分组侧栏、浅灰主画布、紧凑筛选工具区和三列记录网格；评委先总览并打开一条离线研究样本，再运行模拟手表，核对六轴校验、实际波形、逐秒 1/2/3 秒研究曲线和格式化结论。新文件分析是同一工作台的另一条入口。参考的是信息组织与扫描节奏，不复制 Nobi 品牌、居民资料、素材或现实报警语义；页面必须像可操作的软件，而不是 PPT 或产品介绍。

### Product context and register

- **受众与主要任务：** 三模型产品面向比赛评委、项目成员和研究人员；独立校赛工作台面向现场评委和项目成员，主要任务是上传标准六轴记录并真实运行模型，或从 105 组公开案例中选择一组进行可追溯复核。研究人员可继续核对来源、参与者划分、代理锚点、阈值、报告和能力边界。
- **目标市场与证据：** 中国大陆简体中文比赛演示；产品范围来自 `PRODUCT.md`，真实性边界来自 `DATA_AND_MODEL_NOTICE.md`。
- **语言策略：** 首版只提供 `zh-CN`；普通中文是默认层，技术名放在次要说明或展开区。“公开数据代理锚点”必须解释为数据集跌倒区间开始，不能只显示缩写；不要求公众先理解 E0、AUPRC 或校准术语，也不使用含糊宣传词。
- **使用场景：** Windows 笔记本、1024 像素宽的小屏和投影大屏；短时演示与长时间调试并存。
- **界面类型：** 三模型产品和独立 E0 页面都是产品工具；后者是可操作的模拟腕表与案例回放台，不是营销落地页或说明书首页。
- **记忆点：** 三模型产品以“真实性与来源状态条”串起来源与回放；独立校赛工作台以“离线样本网格 → 记录详情 → 模拟手表六步检测 → 同一结果格式”为首屏路径，临时上传则从侧栏进入同一六步框架。公开、自主采集与临时上传共用检查输入、统一标准、识别动作或规律、筛查跌倒、分析提前风险、生成结果六步；双证据图把加速度/角速度波形与 1/2/3 秒研究曲线按同一时间轴语义并列。自主采集 `30/约30组` 始终可见，并明确它属于工程验证。
- **克制区域：** 侧栏、上传选项、案例列表、模型状态和边界说明采用普通软件布局；只让真正承担检测状态的手表设备和双证据图具有较强视觉识别。动作图必须标为“示意，不是案例影像”，传感器图必须来自所选文件或本机已登记文件；风险曲线必须由保存模型实际计算；规律案例必须改用合成事件时间图。禁止装饰性图表、随机波形或持续动画。
- **反例：** 不做 PPT 分页、产品介绍长卷、AI 概念海报、医疗级宣传、深色霓虹数据大屏、渐变 KPI 墙，或把前端阶段动画写成真实预测结果。
- **令牌归属与映射：** Model B。`frontend/src/tokens.css` 是两个本机界面的运行时令牌源；`frontend/src/style.css` 和 `research/early_risk/workbench/app.css` 分别实现产品界面与独立研究工作台，本文件镜像并解释已经接受的值。Tabler Core 是产品基础 CSS 层；全局令牌变更必须先修改唯一令牌源，再同步本文件并通过 lint、严格审计、构建和浏览器检查。

## Colors

`canvas` 使用 Tabler 式冷灰页面背景，`surface` 与 `surface-subtle` 形成白色工作区和轻微分组。`ink`、`ink-muted` 和 `line` 建立清楚但不过重的文字层级。`primary` 只用于当前导航、信息状态和焦点；`success` 表示已完成或正常；`warning` 表示未连接、待处理或需要关注；产品界面的 `danger` 保留真实紧急或不可逆危险语义。独立 E0 工作台的本次计算结果采用分级强调：等待/运行中保持中性或信息色，“需要复核”使用琥珀色，实际发现跌倒候选才使用红色；红色仍只是研究筛查状态，不代表现实报警。登记跌倒标签保持中性。所有状态同时显示文字或图标，不以颜色作为唯一信息。

首版为浅色主题。forced-colors 模式允许系统接管颜色和滚动条对比度。暗色主题需要在图表和告警语义完成后单独验证，本次迁移不自动加入。

## Typography

标题和正文统一使用适合 Windows 与简体中文的无衬线系统字体，删除原有宋体展示标题。独立工作台局部先尝试系统自带的 `Segoe UI Variable`，不可用时回退到共享 `body` 字体栈；不依赖远程字体，且不改变三模型产品的全局字体令牌。独立工作台首屏采用紧凑的“样本总览”标题、清楚的筛选与记录名称，而非海报式大标题；本次实际结论使用更大的字级和更清晰的字重，研究边界保持随结果可见。时间、采样率、输入形状、版本和哈希使用 `data` 等宽字体。正文基础在手机上不小于 16px，关键说明不低于正文；更小字号只用于非关键元信息。中文不使用斜体、全大写或过宽字距。

## Layout

桌面使用 `sidebar-width` 为 15rem 的固定语义侧栏、56px 左右的顶部工具栏和自然滚动的中央工作区。总览先显示一个四列系统状态条，再显示回放与来源两栏，最后用一个连续列表展示三个模型，避免把每条信息都做成独立卡片。

独立校赛工作台使用通栏深青色顶栏、窄而浅的分组侧栏和浅灰主画布。顶栏只显示产品标识、本机连接状态、当前位置与真实工具，不伪造个人账号。首屏为“样本总览”：紧凑的来源/类型筛选、搜索与 3×2 记录网格，按实际筛选显示每页六条。整张记录卡是按钮；点击后打开原生 `dialog`，先读来源、采样率、传感器、时长与当前判断状态，再明确“登记标签不等于模型结论”，最后进入模拟手表。卡片默认是待运行的中性色，只有该记录完成本次六步检测后才显示由真实结果驱动的筛查状态；不能以受控跌倒登记标签直接染成现实报警红卡。

模拟手表、判断过程和完整宽度信号证据沿自然阅读路径紧随总览；判断过程使用与上传页相同的六步组件。桌面双列仅并排呈现手表操作和简明结论；可展开的完整推导、所选案例资料、匹配度与六步流程移到紧随其后的全宽区域，避免右列长内容把左列下方撑成大块空白。窄屏保留手表、简明结论、全宽详解的自然阅读顺序。新数据检测从侧栏进入，左侧文件选择、单位与真实提交，右侧共用六步状态，完成后同样先显示结论卡，再显示四项事实和证据图。两种来源共用“一句实际生成的简明结论 → 三条直接取自输入或模型输出的关键依据 → 始终可见的适用边界 → 按需展开全部证据、模型推导、完整结论与使用规则”。结论卡使用单一语义色顶部细线；次要事实改用分隔线与留白，避免多层套框争夺注意力。实际加速度/角速度波形和逐秒 1/2/3 秒研究曲线仍可见；四个研究模块与长篇边界置于后续区域。视觉、DOM 与键盘阅读顺序一致，不依靠只改变 CSS 顺序制造错位。

顶部“投屏模式”是本页的可逆阅读密度切换，不改变数据、模型输出、颜色含义或页面顺序；按钮持续显示开/关状态并在同一浏览器标签页刷新后保留。投屏时结论、三条依据和事实字号加大，新数据结果改为先读完整文字、再看证据图；窄屏仍按单列自然滚动，关闭后回到普通密度。

三模型产品继续使用既有侧栏断点。独立 E0 检测台在约 1220px 收窄侧栏；在 820px 将浅色侧栏变成顶部可滚动导航；在 660px 将主操作区与网格改为单列。筛选按钮数字仅表示登记案例数，不伪装为报警数。桌面记录区三列、小屏按空间降列；首屏仍保留样本总览在模拟手表之前，且不让遮挡焦点或对话框内容。页面本身不得横向溢出；所有触控目标至少 44×44px。

运行时映射：

| DESIGN.md | CSS 变量 | 主要使用者 |
|---|---|---|
| `colors.canvas` | `frontend/src/tokens.css` → `--color-canvas` | 两个界面的页面背景、滚动条轨道 |
| `colors.surface` | `--color-surface` | 侧栏、工具栏、卡片 |
| `colors.primary` | `--color-primary` | 当前导航、信息状态、品牌标记 |
| `colors.success` | `--color-success` | 已就绪与正常状态 |
| `colors.warning` | `--color-warning` | 未连接、待接入和关注状态 |
| `colors.danger` | `--color-danger` | 真正紧急或危险状态 |
| `typography.body` | `--font-body` | 标题、正文与控件 |
| `typography.data` | `--font-data` | 时间、输入形状与校验值 |
| `rounded.md` | `--radius-md` | 导航、状态面板与普通容器 |
| `spacing.sidebar-width` | `--sidebar-width` | 桌面导航宽度 |
| `colors.simulator-header` | `research/early_risk/workbench/app.css` → `--sim-header` | 模拟器通栏深色顶栏 |
| `colors.simulator-sidebar` | `research/early_risk/workbench/app.css` → `--sim-sidebar` | 模拟器浅色侧栏与窄屏导航 |
| `colors.simulator-canvas` | `--sim-canvas` | 模拟器主画布 |
| `colors.simulator-teal` | `--sim-teal` | 模拟器当前选择、主要操作和完成流程 |
| `colors.simulator-watch` | `--sim-watch` | 功能性腕表显示屏与外壳基色 |
| `colors.simulator-line` | `--sim-line` | 工作台局部低对比边框和行分隔线 |
| `colors.simulator-line-strong` | `--sim-line-strong` | 结论卡外缘、控件与选中边界 |

## Elevation & Depth

层级主要由白色表面、灰色画布、低对比 1px 边框和间距形成；次要数据优先使用行分隔，避免层层套框。结论卡允许一条细语义色顶边和略强的轮廓，但不得做成报警弹窗。静态面板只允许克制阴影；侧栏和顶部栏不使用玻璃模糊。模拟手表是唯一允许立体深度的核心对象，因为外壳、表带、表冠、屏幕和状态灯共同承担“正在操作设备”的产品语义，而不是装饰。模型状态和边界说明保持平面。

## Shapes

普通导航和控件使用 `sm` 或 `md` 小圆角，面板保持 10–14px 的有限圆角。胶囊形仅用于短状态标签；圆形仅用于状态点和线性步骤编号。手表外壳采用真实设备比例的圆角矩形，不能扩散成整页卡片语言。

## Components

### Foundational visual states

所有真实链接和按钮必须有默认、悬停、键盘焦点和按下状态。暂未开放的功能显示为非交互文字并明确写“未开放”，不能伪装成可点击链接。加载、空数据、无结果和错误状态必须使用文字说明。系统总览现在显示真实健康检查的检查中、已连接、部分可用和未连接状态；案例与模型区域仍保留诚实空状态。

### Buttons and actions

`AppButton` 按“强调程度 × 语义意图”实现，并首先用于真实的“刷新状态”操作。一个决策区域只有一个主要操作，危险操作与普通操作分离，忙碌时尺寸稳定。不得添加没有作用的“开始体验”或“连接设备”。

### Navigation and data display

三模型产品的 `AppShell` 仍是其页面壳和主导航唯一所有者。独立校赛工作台使用隔离的原生应用壳，导航分“总览”和“数据与设置”两组，七个真实锚点依次为“样本总览、模拟手表、判断过程、信号证据、新数据检测、模型状态、说明与边界”；每项使用一行主名称和一行简体中文用途说明，并以 `aria-current` 标记唯一当前区域，顶栏当前位置同步更新。案例类型按钮使用 `aria-pressed`；切换类型或有效搜索结果时，手表与判断区同步到当前可见首个案例。模型状态用一条连续模块带呈现，并为四个模型分别提供一句中文释义，避免 KPI 墙。

案例库借鉴照护工作台的“先总览、再进入单条记录”信息层级，但保留研究软件语义：六个类型按钮只是数据筛选；记录网格同时显示动作名称、案例编号、来源与采样条件；选中边框只表示当前记录。点击记录卡打开原生样本详情对话框，关闭后焦点回到原按钮；点击“查看并运行检测”关闭对话框并转到模拟手表操作。受控跌倒的登记标签使用中性色，不能借用现实告警的整卡红色。“需要复核”用琥珀色，“发现跌倒候选”用红色，二者都须写清研究边界，不能成为现实报警。

`StatusBadge` 统一正常、信息、关注、危险和中性状态；状态点始终配文字。`EmptyState` 说明缺少什么、为什么缺少，以及何时会有内容，但不展示虚构数字。

### Forms and overlays

三模型产品总览继续使用既有共享组件。独立校赛工作台新增一个由 `#upload-form` 拥有的 canonical 文件表单：原生文件选择器必须有可见标签和拖放替代，原生单位 `select` 明确列出选项；客户端先检查扩展名和 5 MB 上限，服务器再检查表头、数值、时间、六轴、采样率和单位。提交忙碌时按钮尺寸稳定、阻止重复提交、保留所选文件；失败使用相邻文字错误并聚焦错误区；成功聚焦结果标题。上传内容只在内存中分析，不写 SQLite。`build_analysis_pipeline` 是两种来源共同的六步数据合同，前端 `renderSharedPipeline` 是唯一六步视觉所有者。WEDA 六轴案例真实运行满足条件的三个传感器模型；CAPTURE-24 三轴活动案例真实运行活动模型，跌倒与提前风险步骤显示“未运行”及缺少陀螺仪原因；合成规律案例真实运行规律规则且不生成波形。两个界面都禁止浏览器原生 `alert`、`confirm` 和 `prompt`；任何会写个人数据、改变通知、授权收件人或产生外部副作用的控件仍不属于当前系统。

### Iconography

统一使用 `@tabler/icons-vue` 的 24px 网格线性图标，常用尺寸为 18–24px，线宽约 1.7–1.8。图标用于帮助识别模块，不替代关键文字；装饰图标使用 `aria-hidden`，未来图标按钮必须有简体中文可访问名称。

### Motion

不使用环境动画、呼吸动画、漂浮或脉冲。悬停颜色变化保持约 160ms，只表达可交互状态。`prefers-reduced-motion: reduce` 下关闭平滑滚动并把过渡时间压缩到近乎即时。

### Content and data visualization

使用“正在读取”“模型正在运行”“数据不足”“未运行”“需要复核”“更接近日常活动”等主动、可核验的表述。连接状态来自本机接口，不从静态文案推断。不使用“开启守护”“智慧洞察”“临床级准确率”等宣传词。案例人物统一称“参与者”，不在主要操作界面用年龄称谓暗示能力范围。跌倒输出在界面中称“跌倒特征匹配度”，必须解释它不是现实跌倒概率。结果分析固定采用大陆简体中文评委的扫描顺序：先给结论，再列三条实际依据和适用边界；需要复核时展开全部依据，逐项核对各模型的通俗作用、实际发现、是否参与和交叉核对规则。三条摘要依据只做从本次解释合同中选取和标注，不重新推断或改写数字；无陀螺仪、无连续传感器或时长不足的案例必须在摘要里写明相关模型未运行。临时上传文件不足跌倒动作模型最低窗口时，醒目摘要优先显示服务端的“数据不足”筛查状态，不放大较强的日常活动概括。判断依据只能由本次计算的质量、峰值、模型窗口、阈值、后续运动和逐秒分数组合生成；禁止静态预写结论或编造身体部位原因。风险图必须同时显示 1/2/3 秒曲线、各自阈值、代理锚点（如存在）、精确提前时间快照的分子/分母和非颜色文字摘要；不得显示“综合风险分”。没有实际输入时不画随机波形或虚构风险曲线，未运行也不等于零风险。

## Do's and Don'ts

- **Do：** 让用户在同一阅读路径中看到连接状态、四个模型职责、输入形状、数据来源和代理锚点。
- **Do：** 让评委从样本总览选一条记录、打开详情、运行模拟手表、看双证据图并核对生成结论；新文件上传保留为同样真实计算的第二条演示路径。
- **Do：** 把受控跌倒、日常活动、活动识别和合成规律分开筛选，并始终显示来源边界。
- **Do：** 把自主采集状态显示为 30/约30组，并把工程验证发现的误判和漏判如实保留。
- **Don't：** 把参与者的受控模拟跌倒写成现实环境中的意外跌倒，或展示没有实际运行的模型指标。
- **Don't：** 把公开受控数据代理基线当成现实意外跌倒预测证据，或把数据集区间开始写成真实失稳起点。
- **Don't：** 用 PPT 章节、长篇产品介绍、随机波形、持续动画、悲情老人素材、装饰性风险分数和过度卡片化制造“AI 概念稿”感。
- **Don't：** 因为界面像成品就把锁定的 P3–P9、现实环境提前预测或现实报警写成已完成。
