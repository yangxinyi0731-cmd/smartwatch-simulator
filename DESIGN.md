---
version: alpha
name: "模拟智能手表"
description: "面向比赛展示与研究复现的 Tabler 风格三模型健康监测工作台"
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
---

# 模拟智能手表设计系统

## Overview

### Creative North Star

界面以“医院或研究机构里的健康监测工作台”为参照：导航明确、密度适中、状态可以快速扫描，证据比装饰更醒目。Tabler 提供成熟后台软件的基础语言，腕部传感器、模型输入和来源追溯让它保持本项目身份。它不是消费电子广告页，也不是深色霓虹数据大屏。

### Product context and register

- **受众与主要任务：** 比赛评委、无代码基础项目成员和后续研究人员，需要迅速看懂数据是否已接入、三个模型分别做什么，以及结论从哪里来。
- **目标市场与证据：** 中国大陆简体中文比赛演示；产品范围来自 `PRODUCT.md`，真实性边界来自 `DATA_AND_MODEL_NOTICE.md`。
- **语言策略：** 首版只提供 `zh-CN`；技术词首次出现时用通俗中文说明，不使用含糊宣传词。
- **使用场景：** Windows 笔记本、1024 像素宽的小屏和投影大屏；短时演示与长时间调试并存。
- **界面类型：** 产品工具，不是营销落地页。
- **记忆点：** “真实性与来源状态条”把案例来源、真实性类别、文件校验和 manifest 与回放放在同一阅读路径中；它表达可验证性，不承担装饰任务。
- **克制区域：** 导航、模型列表、空状态和来源信息采用普通后台布局；不使用巨大主标题、巨大设备外壳、方格背景、装饰编号或持续动画。
- **反例：** 不做 AI 概念海报、医疗级宣传、深色科技大屏、渐变 KPI 墙或儿童化养老插画。
- **令牌归属与映射：** Model B。`frontend/src/style.css` 是运行时令牌源，本文件镜像并解释已经接受的值。Tabler Core 是基础 CSS 层，自定义令牌和共享组件负责项目语义；全局令牌变更必须同时修改两处并通过 lint、严格审计、构建和浏览器检查。

## Colors

`canvas` 使用 Tabler 式冷灰页面背景，`surface` 与 `surface-subtle` 形成白色工作区和轻微分组。`ink`、`ink-muted` 和 `line` 建立清楚但不过重的文字层级。`primary` 只用于当前导航、信息状态和焦点；`success` 表示已完成或正常；`warning` 表示未连接、待处理或需要关注；`danger` 仅用于真实紧急或不可逆危险。所有状态同时显示文字或图标，不以颜色作为唯一信息。

首版为浅色主题。forced-colors 模式允许系统接管颜色和滚动条对比度。暗色主题需要在图表和告警语义完成后单独验证，本次迁移不自动加入。

## Typography

标题和正文统一使用适合 Windows 与简体中文的无衬线系统字体，删除原有宋体展示标题。标题通过字重、大小和间距建立层级，不依赖广告式大字号。时间、采样率、输入形状、版本和哈希使用 `data` 等宽字体。正文基础保持可读，关键说明不小于约 14px；更小字号只用于非关键元信息。中文不使用斜体、全大写或过宽字距。

## Layout

桌面使用 `sidebar-width` 为 15rem 的固定语义侧栏、56px 左右的顶部工具栏和自然滚动的中央工作区。总览先显示一个四列系统状态条，再显示回放与来源两栏，最后用一个连续列表展示三个模型，避免把每条信息都做成独立卡片。

小于 1180px 时回放与来源变为单列；小于 980px 时系统状态条为两列；小于 760px 时侧栏转为顶部品牌区和可横向滚动的功能导航；小于 540px 时状态条、来源条和模型内容改为单列。横向滚动只属于窄屏导航或未来真实数据表，页面本身不得横向溢出。

运行时映射：

| DESIGN.md | CSS 变量 | 主要使用者 |
|---|---|---|
| `colors.canvas` | `--color-canvas` | 页面背景、滚动条轨道 |
| `colors.surface` | `--color-surface` | 侧栏、工具栏、卡片 |
| `colors.primary` | `--color-primary` | 当前导航、信息状态、品牌标记 |
| `colors.success` | `--color-success` | 已就绪与正常状态 |
| `colors.warning` | `--color-warning` | 未连接、待接入和关注状态 |
| `colors.danger` | `--color-danger` | 真正紧急或危险状态 |
| `typography.body` | `--font-body` | 标题、正文与控件 |
| `typography.data` | `--font-data` | 时间、输入形状与校验值 |
| `rounded.md` | `--radius-md` | 导航、状态面板与普通容器 |
| `spacing.sidebar-width` | `--sidebar-width` | 桌面导航宽度 |

## Elevation & Depth

层级主要由白色表面、灰色画布、1px 边框和间距形成。静态卡片只允许一个极轻的 1px 阴影；侧栏和顶部栏不使用玻璃模糊。设备状态屏可使用深色平面来区分传感器显示区，但不模拟立体手表外壳。空状态、模型列表和来源说明不添加装饰阴影。

## Shapes

普通导航和控件使用 `sm` 或 `md` 小圆角，卡片最多使用 `lg` 的 8px 圆角。胶囊形仅用于短状态标签；圆形仅用于状态点和无交互的图标背景。页面不再使用巨型圆环、轨道、手表圆角或无流程意义的圆形编号。

## Components

### Foundational visual states

所有真实链接和按钮必须有默认、悬停、键盘焦点和按下状态。暂未开放的功能显示为非交互文字并明确写“未开放”，不能伪装成可点击链接。加载、空数据、无结果和错误状态必须使用文字说明。系统总览现在显示真实健康检查的检查中、已连接、部分可用和未连接状态；案例与模型区域仍保留诚实空状态。

### Buttons and actions

`AppButton` 按“强调程度 × 语义意图”实现，并首先用于真实的“刷新状态”操作。一个决策区域只有一个主要操作，危险操作与普通操作分离，忙碌时尺寸稳定。不得添加没有作用的“开始体验”或“连接设备”。

### Navigation and data display

`AppShell` 是页面壳和主导航唯一所有者，使用真实锚点跳转到本页已有区域，并用 `aria-current` 标记系统总览。未开放页面不提供假链接。`AppCard` 只用于真实分组；四项连接状态合并为一个 `system-strip`，三个模型合并为一个 `model-list`。未来数据表继续遵守 `UX-CONTRACT.md` 的服务端分页和窄屏横向滚动约定。

`StatusBadge` 统一正常、信息、关注、危险和中性状态；状态点始终配文字。`EmptyState` 说明缺少什么、为什么缺少，以及何时会有内容，但不展示虚构数字。

### Forms and overlays

当前总览没有表单、选择器、搜索、对话框或通知。后续必须先建立共享组件并按 `UX-CONTRACT.md` 验证，禁止浏览器原生 `alert`、`confirm` 和 `prompt`。

### Iconography

统一使用 `@tabler/icons-vue` 的 24px 网格线性图标，常用尺寸为 18–24px，线宽约 1.7–1.8。图标用于帮助识别模块，不替代关键文字；装饰图标使用 `aria-hidden`，未来图标按钮必须有简体中文可访问名称。

### Motion

不使用环境动画、呼吸动画、漂浮或脉冲。悬停颜色变化保持约 160ms，只表达可交互状态。`prefers-reduced-motion: reduce` 下关闭平滑滚动并把过渡时间压缩到近乎即时。

### Content and data visualization

使用“正在检查”“本地服务已连接”“后端未连接”“尚未导入”“暂无数据”“待训练”等主动、可核验的表述。连接状态来自 HTTP 健康检查和 WebSocket，不从静态文案推断。不使用“开启守护”“智慧洞察”“临床级准确率”等宣传词。未来图表必须有文字摘要、单位、来源和原始值访问路径；没有真实输入时显示空状态，不画随机波形。

## Do's and Don'ts

- **Do：** 让用户在同一阅读路径中看到连接状态、三模型职责、输入形状和数据来源。
- **Do：** 使用共享壳、状态标签、卡片和空状态，保持未来页面行为一致。
- **Don't：** 把年轻参与者的受控模拟跌倒写成真实老人跌倒，或展示没有实际运行的模型指标。
- **Don't：** 用巨大标题、宋体、方格背景、巨型装饰手表、持续动画、装饰编号和过度卡片化制造“AI 概念稿”感。
