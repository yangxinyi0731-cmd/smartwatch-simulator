---
version: alpha
name: "模拟智能手表"
description: "面向比赛展示与研究复现的静谧健康研究台"
colors:
  ink: "#253247"
  ink-muted: "#66758d"
  canvas: "#f5f7f6"
  surface: "#ffffff"
  surface-subtle: "#f6f9f8"
  line: "#dfe8e5"
  primary: "#0b7d4d"
  primary-bright: "#18c86b"
  primary-soft: "#e6f7ed"
  secondary: "#4fb9dc"
  secondary-soft: "#e8f7fb"
  success: "#0b7d4d"
  success-soft: "#e6f7ed"
  warning: "#945f00"
  warning-soft: "#fff4d8"
  danger: "#ba3d4a"
  danger-soft: "#fdecef"
  focus: "#0b7d4d"
  scrollbar-thumb: "#9daca8"
  scrollbar-track: "#edf2f0"
typography:
  display:
    fontFamily: "Cambria, Noto Serif SC, Source Han Serif SC, STZhongsong, Songti SC, serif"
    fontSize: "4.35rem"
    fontWeight: "700"
    lineHeight: "1.08"
  heading:
    fontFamily: "Cambria, Noto Serif SC, Source Han Serif SC, STZhongsong, Songti SC, serif"
    fontSize: "1.125rem"
    fontWeight: "700"
    lineHeight: "1.35"
  body:
    fontFamily: "Segoe UI, Microsoft YaHei UI, PingFang SC, Noto Sans CJK SC, system-ui, sans-serif"
    fontSize: "0.875rem"
    fontWeight: "400"
    lineHeight: "1.65"
  body-large:
    fontFamily: "Segoe UI, Microsoft YaHei UI, PingFang SC, Noto Sans CJK SC, system-ui, sans-serif"
    fontSize: "1rem"
    fontWeight: "400"
    lineHeight: "1.85"
  metadata:
    fontFamily: "Segoe UI, Microsoft YaHei UI, PingFang SC, Noto Sans CJK SC, system-ui, sans-serif"
    fontSize: "0.75rem"
    fontWeight: "500"
    lineHeight: "1.55"
  data:
    fontFamily: "Cascadia Mono, SFMono-Regular, Consolas, monospace"
    fontSize: "0.75rem"
    fontWeight: "600"
    lineHeight: "1.5"
rounded:
  DEFAULT: "0.75rem"
  sm: "0.5rem"
  md: "0.75rem"
  lg: "1.125rem"
  xl: "1.5rem"
  pill: "999px"
spacing:
  xs: "0.25rem"
  sm: "0.5rem"
  md: "0.75rem"
  lg: "1rem"
  xl: "1.5rem"
  2xl: "2rem"
  3xl: "3rem"
  page-inline: "2rem"
  section-gap: "1.5rem"
  panel-gap: "1.25rem"
components:
  app-shell:
    backgroundColor: "{colors.canvas}"
    textColor: "{colors.ink}"
  floating-header:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.xl}"
  navigation:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink-muted}"
    rounded: "{rounded.md}"
  navigation-current:
    backgroundColor: "{colors.primary-soft}"
    textColor: "{colors.primary}"
  app-card:
    backgroundColor: "{colors.surface}"
    rounded: "{rounded.xl}"
  data-panel:
    backgroundColor: "{colors.surface-subtle}"
    rounded: "{rounded.lg}"
  divider:
    backgroundColor: "{colors.line}"
  app-button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.surface}"
    rounded: "{rounded.md}"
  app-button-secondary:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.md}"
  status-success:
    backgroundColor: "{colors.success-soft}"
    textColor: "{colors.success}"
  status-info:
    backgroundColor: "{colors.secondary-soft}"
    textColor: "{colors.ink}"
  status-warning:
    backgroundColor: "{colors.warning-soft}"
    textColor: "{colors.warning}"
  status-danger:
    backgroundColor: "{colors.danger-soft}"
    textColor: "{colors.danger}"
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

界面采用“静谧健康研究台”方向：借鉴参考图的明亮近白画布、青蓝到薄荷绿的清新点缀、墨蓝衬线标题、白色大圆角卡片和宽松留白，同时保留研究工具需要的数据密度、真实性边界与可追溯证据。它应像一间安静、可信、光线充足的健康研究室，而不是传统后台，也不是消费级冥想产品的营销落地页。

### Product context and register

- **受众与主要任务：** 比赛评委、无代码基础项目成员和研究人员需要在几分钟内选择案例、开始回放、理解三个模型，并判断结论来自哪里、适用到哪里。
- **目标市场：** 中国大陆简体中文比赛演示；首版 locale 为 `zh-CN`，默认时区为 `Asia/Shanghai`。
- **界面类型：** 产品工具。参考图只提供视觉语言，不提供业务文案、用户评价、下载按钮或虚构运营数据。
- **签名特征：** 青蓝—薄荷绿“健康光谱”只出现在品牌标记、标题强调、主进度和少量图标底色；所有来源、真实性与模型限制仍在同一阅读路径中。
- **克制区域：** 表单、长说明、报告限制、哈希和波形保持安静、中性、易读；不让渐变遮盖数据，也不把每个数字都做成高饱和 KPI 卡。
- **反例：** 不做深色霓虹大屏、AI 紫粉渐变、医疗级宣传、儿童化养老插画、玻璃拟态堆叠或带虚假数据的营销组件。
- **令牌归属：** Model B。`frontend/src/style.css` 是运行时 canonical token source；本文镜像已经接受的值并解释使用规则。任何全局颜色、字体、圆角、间距或阴影变化必须在同一 changeset 中修改 CSS 与本文。

### Reference adaptation

参考截图的可迁移视觉信号如下：

1. 近白冷灰背景与纯白表面形成低对比层级；
2. 墨蓝衬线标题与蓝灰无衬线正文形成明显角色分工；
3. 明亮绿色承担主要操作，青蓝—薄荷绿承担品牌强调；
4. 卡片使用 18–24px 大圆角、极浅边框和宽而轻的羽化阴影；
5. 模块之间留白大于模块内部间距，内容区保持居中且不贴屏边；
6. 顶部导航是悬浮白色容器，移动端变为两行并让导航在自身区域横向滚动。

## Colors

### 核心色值

| 角色 | 色值 | 用途 |
|---|---|---|
| 主文字 `ink` | `#253247` | 标题、重要数值、关键标签 |
| 次文字 `ink-muted` | `#66758D` | 正文、解释、元信息 |
| 页面背景 `canvas` | `#F5F7F6` | 应用画布与滚动条轨道基底 |
| 主表面 `surface` | `#FFFFFF` | 顶栏、卡片、控件 |
| 次表面 `surface-subtle` | `#F6F9F8` | 卡片内部小分组、只读数据块 |
| 边框 `line` | `#DFE8E5` | 普通 1px 边框和分隔线 |
| 主色 `primary` | `#0B7D4D` | 主按钮、当前导航、键盘焦点；与白字保持可读对比 |
| 亮主色 `primary-bright` | `#18C86B` | 进度和非文字装饰，不直接承载小号白字 |
| 主色浅底 `primary-soft` | `#E6F7ED` | 选中项、成功背景、轻提示 |
| 辅助色 `secondary` | `#4FB9DC` | 信息图标、波形、证据提示 |
| 辅助色浅底 `secondary-soft` | `#E8F7FB` | 中性信息块和活动识别摘要 |
| 警示 `warning` | `#945F00` | 合成数据、待处理和受限证据 |
| 危险 `danger` | `#BA3D4A` | 真实错误、不可逆危险和候选告警 |

健康光谱固定为 `linear-gradient(105deg, #63C5E5 0%, #7CE2BA 52%, #7EE896 100%)`。它只能用于品牌标记、标题文字裁切、图标底色和进度填充；正文、表格和长说明不得使用渐变文字。

### 语义规则

- `primary` 表示当前路径或主要安全操作，不等于“医疗正常”。
- `success` 只表示系统就绪、任务完成或已通过当前范围的技术检查。
- `warning` 表示合成数据、受控模拟、待处理或需要注意的限制。
- `danger` 只用于真实错误、不可逆危险或明确的告警候选；不得用红色制造紧张感。
- 颜色必须配合文字、图标或形状，不得成为唯一状态信号。
- forced-colors 模式允许系统接管颜色、边框与滚动条对比度；本阶段不提供暗色主题。

## Typography

### 字体角色

- **展示/标题：** `Cambria, Noto Serif SC, Source Han Serif SC, STZhongsong, Songti SC, serif`。只用于品牌名、页面主标题、模块标题和卡片标题，传递参考图的安静、可信感。
- **正文/控件：** `Segoe UI, Microsoft YaHei UI, PingFang SC, Noto Sans CJK SC, system-ui, sans-serif`。用于所有说明、导航、按钮与表单。
- **数据：** `Cascadia Mono, SFMono-Regular, Consolas, monospace`。只用于时间、采样率、输入形状、版本、案例 ID 与哈希。
- 使用系统字体栈，不依赖联网字体下载，避免离线演示时发生字体闪动或布局偏移。

### 字号层级

| 角色 | 字号 | 字重 | 行高 | 规则 |
|---|---:|---:|---:|---|
| 页面主标题 | `clamp(2.5rem, 5vw, 4.35rem)` | 700 | 1.08 | 仅一处；可分两行，第二行可用健康光谱 |
| 模块标题 | `1.125rem` | 700 | 1.35 | 卡片与主模块标题 |
| 内容标题 | `1rem` | 700 | 1.4 | 案例、模型、报告标题 |
| 大正文 | `1rem` | 400 | 1.85 | 页面导语和重要解释 |
| 标准正文 | `0.875rem` | 400/500 | 1.65 | 普通说明和状态内容 |
| 元信息 | `0.75rem` | 500/600 | 1.55 | 次要标签、限制数量、图例；不得小于 12px |
| 数据文字 | `0.75–0.8125rem` | 600 | 1.5 | 时间、ID、哈希与测量值 |

中文不使用斜体、全大写或过宽字距。长来源、限制和错误优先换行，不用省略号隐藏关键信息；哈希可显示短预览，但完整值必须仍可读取。

## Layout

### 页面骨架

```text
┌──────────────────── 浮动顶栏：品牌 / 页面锚点 / 连接状态 / 刷新 ────────────────────┐
└──────────────────────────────────────────────────────────────────────────────────┘

  本地优先标签
  系统总览
  健康数据，有据可查                         研究与比赛演示 / 非医疗边界

  ┌──────────────────────────── 四项系统状态条 ───────────────────────────────────┐
  └───────────────────────────────────────────────────────────────────────────────┘

  ┌────────────────────────── 回放与证据 ─────────────────────┐  ┌── 数据与来源 ──┐
  └───────────────────────────────────────────────────────────┘  └───────────────┘

  ┌──────────────────────── 三个模型卡片并排 ──────────────────────────────────────┐
  └───────────────────────────────────────────────────────────────────────────────┘

  ┌──────────────────────── 批量回放 / 测试报告 ───────────────────────────────────┐
  └───────────────────────────────────────────────────────────────────────────────┘
```

- 内容最大宽度为 `80rem`；桌面页边距最多 `2rem`，窄屏至少 `1rem`。
- 浮动顶栏距视口上边 `1rem`，高度约 `4.75rem`；小屏距上边 `0.5rem`。
- 模块间距 `1.5rem`，双栏面板间距 `1.25rem`，卡片内部常用 `1–1.25rem`。
- 模块间留白必须大于同一模块内部间距；不要用分隔线替代全部留白。
- 页面自然滚动，不对共享页面壳使用固定 `100vh` 或 `overflow: hidden`。

### 响应式规则

- `≤1180px`：浮动顶栏换成两行，导航在自己的区域横向滚动；四项状态变为两列；回放、来源与波形面板变为单列。
- `≤980px`：模型卡变为两列。
- `≤760px`：模型卡变为单列；设备与回放状态先变为紧凑双列，再按内容继续收敛。
- `≤540px`：主标题、状态条、卡片头、设备区、证据格和报告操作全部单列；页面本身不得横向滚动。

### Runtime mapping

| DESIGN.md | CSS 变量 | 主要使用者 |
|---|---|---|
| `colors.canvas` | `--color-canvas` | 页面背景、滚动条轨道 |
| `colors.surface` | `--color-surface` | 顶栏、卡片、控件 |
| `colors.primary` | `--color-primary` | 主按钮、当前导航、焦点 |
| `colors.secondary` | `--color-secondary` | 信息图标、波形和提示 |
| `typography.display` | `--font-display` | 品牌、H1、H2、H3 |
| `typography.body` | `--font-body` | 正文、导航与控件 |
| `typography.data` | `--font-data` | 时间、输入形状与校验值 |
| `rounded.md/lg/xl` | `--radius-md/lg/xl` | 控件、内部面板、主卡片 |
| 阴影规则 | `--shadow-soft` / `--shadow-float` | 卡片 / 浮动顶栏 |

## Elevation & Depth

- 浮动顶栏使用 `0 20px 50px rgba(50, 68, 78, 0.11), 0 4px 12px rgba(50, 68, 78, 0.06)`。
- 主卡片使用 `0 18px 45px rgba(50, 68, 78, 0.08), 0 3px 10px rgba(50, 68, 78, 0.05)`。
- 内部数据块最多使用 `0 10px 28px rgba(50, 68, 78, 0.06)`，大多数内部块只用 1px 边框。
- 阴影必须宽、轻、低透明度；不使用黑色硬阴影、内发光或多层玻璃模糊。
- 页面背景允许两个静态低透明度径向色晕；不得漂浮、脉冲或跟随鼠标。

## Shapes

- 主卡片与浮动顶栏：`24px`（`--radius-xl`）。
- 内部面板与报告/模型子卡：`18px`（`--radius-lg`）。
- 按钮、输入框与普通控件：`12–14px`（`--radius-md`）。
- 小标签/紧凑控件：`8px`（`--radius-sm`）。
- 胶囊形仅用于短状态、筛选标签和进度轨道；圆形仅用于状态点或无交互图标背景。

## Components

### Navigation

`AppShell` 是浮动顶栏和主导航的唯一所有者。桌面一行展示品牌、真实页面锚点、连接状态和“刷新状态”；`≤1180px` 时导航单独占第二行并横向滚动。未开放功能保留“未开放”文字且不可点击，不使用空 `href` 或无效果按钮。

### Buttons

- 主按钮：背景 `#0B7D4D`、白字、1px 同色边框、约 44px 高、14px 圆角、轻绿色阴影。
- 次按钮：白底、`#DFE8E5` 边框、墨蓝文字、同等高度和圆角。
- 每个决策区域只保留一个高强调主操作；危险操作不与普通主操作并排使用相同强调。
- 默认、hover、focus-visible、active、disabled 和 busy 都必须有明确状态；busy 时按钮宽高不得变化。

### Cards

- `AppCard`：白底、1px `#DFE8E5` 边框、24px 圆角和 `--shadow-soft`。
- 卡片标题区与正文用边框分隔，但标题区仍保持白底；内边距为 18–20px。
- 模型和报告子卡使用 18px 圆角与更轻阴影；不把每个单一数值独立升格为悬浮卡。
- 真实性、限制和来源说明不得被折叠成只有颜色的徽章。

### Status badges and alerts

`StatusBadge` 使用胶囊形、状态点和文字。成功用绿、信息用青蓝、限制用琥珀、错误用红；状态点永远配文字。页面级连接异常使用持续消息块，不用瞬时 toast 代替。

### Selects and filters

当前 `Select/Listbox` canonical owner 为原生 `<select>`；接受 Windows/浏览器拥有的打开态几何和选项样式。闭合态使用 44px 高、12px 圆角、1px 中性边框。筛选按钮使用 35px 左右紧凑高度、12px 圆角；选中态为主色浅底和主色文字。若未来要求控制打开弹层的宽度、边框、圆角或碰撞行为，必须先引入维护良好的可访问 Select/Listbox 共享原语。

### Data visualization

波形保留真实数据、单位和图例。青蓝、研究绿、告警红、紫、琥珀和青绿构成六轴序列；任何颜色都不能取代文字图例。图表背景只允许低对比网格，候选告警与真实标签必须分开显示。

### Iconography

统一使用 `@tabler/icons-vue` 的 24px 网格线性图标，常用尺寸 18–24px、线宽 1.7–1.8。图标帮助识别模块，不替代关键文字；装饰图标使用 `aria-hidden`，图标按钮必须有简体中文可访问名称。

### Motion

不使用环境动画、呼吸动画、漂浮或视差。hover/active 过渡为 `160ms` 左右，只表达交互状态。`prefers-reduced-motion: reduce` 下关闭平滑滚动并把过渡压缩到近乎即时。

## Do's and Don'ts

- **Do：** 先读本文，再创建或调整任何页面；所有新页面复用相同令牌、顶栏、按钮、卡片、状态和空状态原语。
- **Do：** 保持大量留白，但让回放、来源、模型限制和真实数值始终可以直接阅读。
- **Do：** 在桌面 1440×900、平板 1024×768 和手机 390×844 验证布局、焦点与页面级横向溢出。
- **Don't：** 把年轻参与者受控模拟跌倒写成真实老人跌倒，或把三个模型平均成综合医学风险。
- **Don't：** 复制参考图中的下载按钮、用户评价、运营数字或健康承诺。
- **Don't：** 使用 AI 紫粉渐变、深色科技大屏、巨型装饰手表、持续动画、无流程编号或过度卡片化。
