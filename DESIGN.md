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
  simulator-sidebar: "#13232f"
  simulator-canvas: "#eef2f4"
  simulator-teal: "#0b6e69"
  simulator-watch: "#071b22"
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
    textColor: "{colors.surface}"
  simulator-primary-action:
    backgroundColor: "{colors.simulator-teal}"
    textColor: "{colors.surface}"
  simulator-watch-device:
    backgroundColor: "{colors.simulator-watch}"
    textColor: "{colors.surface}"
---

# 模拟智能手表设计系统

## Overview

### Creative North Star

现有三模型产品继续以“医院或研究机构里的健康监测工作台”为参照：导航明确、密度适中、状态可以快速扫描，证据比装饰更醒目。独立 E0 页面改为“设备实验室里的可操作模拟手表检测台”：评委先选择案例，在可见的手表界面上开始、暂停或重置检测，再从同一屏核对读取、窗口、独立模型判断和结果复核。页面首先要像可以操作的成品软件，而不是 PPT、产品介绍或长篇研究汇报；真实性边界仍与结果同屏出现。

### Product context and register

- **受众与主要任务：** 三模型产品面向比赛评委、项目成员和研究人员；独立 E0 检测台面向现场评委和项目成员，主要任务是从 105 组已登记案例中选择一组，并操作模拟手表完成前端检测流程。研究人员仍可核对来源、已保存摘要和能力边界。
- **目标市场与证据：** 中国大陆简体中文比赛演示；产品范围来自 `PRODUCT.md`，真实性边界来自 `DATA_AND_MODEL_NOTICE.md`。
- **语言策略：** 首版只提供 `zh-CN`；普通中文是默认层，技术名放在次要说明或展开区，例如“只演示、不报警（dry-run）”“进入下一步前必须满足的条件（Gate）”。不要求公众先理解 E0、AUPRC 或校准术语，也不使用含糊宣传词。
- **使用场景：** Windows 笔记本、1024 像素宽的小屏和投影大屏；短时演示与长时间调试并存。
- **界面类型：** 三模型产品和独立 E0 页面都是产品工具；后者是可操作的模拟腕表与案例回放台，不是营销落地页或说明书首页。
- **记忆点：** 三模型产品以“真实性与来源状态条”串起来源与回放；独立 E0 检测台以居中的功能性手表设备串起案例输入、检测控制和结果。105 组案例库与四步判断过程始终可见，未来数秒风险能力明确锁定。
- **克制区域：** 侧栏、案例列表、模型状态和边界说明采用普通软件布局；只让真正承担检测状态的手表设备具有较强视觉识别，不使用装饰性图表、随机波形或持续动画。
- **反例：** 不做 PPT 分页、产品介绍长卷、AI 概念海报、医疗级宣传、深色霓虹数据大屏、渐变 KPI 墙，或把前端阶段动画写成真实预测结果。
- **令牌归属与映射：** Model B。`frontend/src/tokens.css` 是两个本机界面的运行时令牌源；`frontend/src/style.css` 和 `research/early_risk/workbench/app.css` 分别实现产品界面与独立研究工作台，本文件镜像并解释已经接受的值。Tabler Core 是产品基础 CSS 层；全局令牌变更必须先修改唯一令牌源，再同步本文件并通过 lint、严格审计、构建和浏览器检查。

## Colors

`canvas` 使用 Tabler 式冷灰页面背景，`surface` 与 `surface-subtle` 形成白色工作区和轻微分组。`ink`、`ink-muted` 和 `line` 建立清楚但不过重的文字层级。`primary` 只用于当前导航、信息状态和焦点；`success` 表示已完成或正常；`warning` 表示未连接、待处理或需要关注；`danger` 仅用于真实紧急或不可逆危险。所有状态同时显示文字或图标，不以颜色作为唯一信息。

首版为浅色主题。forced-colors 模式允许系统接管颜色和滚动条对比度。暗色主题需要在图表和告警语义完成后单独验证，本次迁移不自动加入。

## Typography

标题和正文统一使用适合 Windows 与简体中文的无衬线系统字体，删除原有宋体展示标题。公众页面允许在第一屏使用较大的单一主标题帮助快速理解，但必须控制行长、自然换行，并让真实性边界同时出现在首屏；其余层级靠字重、大小和间距建立。时间、采样率、输入形状、版本和哈希使用 `data` 等宽字体。正文基础在手机上不小于 16px，关键说明不低于正文；更小字号只用于非关键元信息。中文不使用斜体、全大写或过宽字距。

## Layout

桌面使用 `sidebar-width` 为 15rem 的固定语义侧栏、56px 左右的顶部工具栏和自然滚动的中央工作区。总览先显示一个四列系统状态条，再显示回放与来源两栏，最后用一个连续列表展示三个模型，避免把每条信息都做成独立卡片。

独立 E0 检测台使用固定深色侧栏、顶部设备状态栏和浅色主画布。首屏核心是三列操作区：左侧案例搜索、类型筛选和分页；中间是模拟手表、当前案例与开始/暂停/重置；右侧是所选案例事实、已保存摘要、四步检测流程和外部通知计数。三类现有模块与锁定的未来预测能力紧随主操作区；长篇数据边界放入原生 `details` 渐进展开。

三模型产品继续使用既有侧栏断点。独立 E0 检测台在约 1220px 收窄侧栏并让判断区换到下一行；在 820px 将侧栏变成顶部导航；在 660px 将主操作区改为单列，并把模拟手表排到案例库之前，保证现场首先看见可操作设备。筛选标签可局部横向滚动，页面本身不得横向溢出；所有触控目标至少 44×44px。

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
| `colors.simulator-sidebar` | `research/early_risk/workbench/app.css` → `--sim-sidebar` | 模拟器侧栏与窄屏顶部导航 |
| `colors.simulator-canvas` | `--sim-canvas` | 模拟器主画布 |
| `colors.simulator-teal` | `--sim-teal` | 模拟器当前选择、主要操作和完成流程 |
| `colors.simulator-watch` | `--sim-watch` | 功能性腕表显示屏与外壳基色 |

## Elevation & Depth

层级主要由白色表面、灰色画布、1px 边框和间距形成。静态面板只允许克制阴影；侧栏和顶部栏不使用玻璃模糊。模拟手表是唯一允许立体深度的核心对象，因为外壳、表带、表冠、屏幕和状态灯共同承担“正在操作设备”的产品语义，而不是装饰。模型状态和边界说明保持平面。

## Shapes

普通导航和控件使用 `sm` 或 `md` 小圆角，面板保持 10–14px 的有限圆角。胶囊形仅用于短状态标签；圆形仅用于状态点和线性步骤编号。手表外壳采用真实设备比例的圆角矩形，不能扩散成整页卡片语言。

## Components

### Foundational visual states

所有真实链接和按钮必须有默认、悬停、键盘焦点和按下状态。暂未开放的功能显示为非交互文字并明确写“未开放”，不能伪装成可点击链接。加载、空数据、无结果和错误状态必须使用文字说明。系统总览现在显示真实健康检查的检查中、已连接、部分可用和未连接状态；案例与模型区域仍保留诚实空状态。

### Buttons and actions

`AppButton` 按“强调程度 × 语义意图”实现，并首先用于真实的“刷新状态”操作。一个决策区域只有一个主要操作，危险操作与普通操作分离，忙碌时尺寸稳定。不得添加没有作用的“开始体验”或“连接设备”。

### Navigation and data display

三模型产品的 `AppShell` 仍是其页面壳和主导航唯一所有者。独立 E0 检测台使用隔离的原生应用壳，导航只链接“实时检测、案例回放、判断过程、模型状态、说明与边界”，并以 `aria-current` 标记当前区域。案例类型按钮使用 `aria-pressed`；切换类型或有效搜索结果时，手表与判断区同步到当前可见首个案例。模型状态用一条连续模块带呈现，避免 KPI 墙。

`StatusBadge` 统一正常、信息、关注、危险和中性状态；状态点始终配文字。`EmptyState` 说明缺少什么、为什么缺少，以及何时会有内容，但不展示虚构数字。

### Forms and overlays

三模型产品总览继续使用既有共享组件。独立 E0 检测台只提供无持久化副作用的搜索、筛选、分页和播放控制。开始/暂停/重置只驱动前端阶段状态；WEDA 案例完成后显示仓库已保存摘要，CAPTURE-24 与合成规律只显示“案例就绪”，不得伪造逐样本结果。后端继续强制只演示、不报警。两个界面都禁止浏览器原生 `alert`、`confirm` 和 `prompt`；任何会写个人数据、改变通知、授权收件人或产生外部副作用的控件仍不属于当前系统。

### Iconography

统一使用 `@tabler/icons-vue` 的 24px 网格线性图标，常用尺寸为 18–24px，线宽约 1.7–1.8。图标用于帮助识别模块，不替代关键文字；装饰图标使用 `aria-hidden`，未来图标按钮必须有简体中文可访问名称。

### Motion

不使用环境动画、呼吸动画、漂浮或脉冲。悬停颜色变化保持约 160ms，只表达可交互状态。`prefers-reduced-motion: reduce` 下关闭平滑滚动并把过渡时间压缩到近乎即时。

### Content and data visualization

使用“正在读取”“案例已就绪”“等待检测”“检测完成”“未触发跌倒候选”等主动、可核验的表述。连接状态来自真实本机接口，不从静态文案推断。不使用“开启守护”“智慧洞察”“临床级准确率”等宣传词。WEDA 概率必须标记为已保存同源回放摘要；受控模拟跌倒、日常活动误报、CAPTURE-24 恢复子集和合成规律必须分别标记。未来数秒风险预测固定显示“后端尚未接入 / 锁定”；没有真实输入时不画随机波形或虚构风险曲线。

## Do's and Don'ts

- **Do：** 让用户在同一阅读路径中看到连接状态、三模型职责、输入形状和数据来源。
- **Do：** 让评委在首屏完成选案例、操作手表、看判断过程和核对保存结果。
- **Do：** 把受控跌倒、日常活动、活动识别和合成规律分开筛选，并始终显示来源边界。
- **Do：** 在说明展开区保留起身、散步、弯腰、坐车、快速坐下和摘表等未来生活逻辑，但不让说明取代软件操作。
- **Don't：** 把年轻参与者的受控模拟跌倒写成真实老人跌倒，或展示没有实际运行的模型指标。
- **Don't：** 把工程演示阶段 E0 当成 P9 老人风险界面，或用阈值滑块和生活场景制造“预测已经有效”的视觉暗示。
- **Don't：** 用 PPT 章节、长篇产品介绍、随机波形、持续动画、悲情老人素材、装饰性风险分数和过度卡片化制造“AI 概念稿”感。
- **Don't：** 因为界面像成品就把锁定的 P3–P9、真实老人提前预测或现实报警写成已完成。
