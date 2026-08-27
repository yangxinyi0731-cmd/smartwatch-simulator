---
version: alpha
name: "守望台"
description: "面向比赛展示与零基础学习的老年人模拟智能手表守护台"
colors:
  ink: "#17313a"
  ink-muted: "#5d7278"
  canvas: "#eef4f1"
  surface: "#f9fcfa"
  surface-strong: "#ffffff"
  line: "#cbd9d4"
  primary: "#0f766e"
  primary-soft: "#d9eee9"
  accent: "#d98b2b"
  accent-soft: "#f8ead2"
  danger: "#bd3f50"
  focus: "#155e75"
typography:
  display:
    fontFamily: "STZhongsong, Songti SC, Noto Serif CJK SC, serif"
  body:
    fontFamily: "Microsoft YaHei UI, PingFang SC, Noto Sans CJK SC, system-ui, sans-serif"
  data:
    fontFamily: "Cascadia Mono, SFMono-Regular, Consolas, monospace"
rounded:
  DEFAULT: "0.85rem"
  sm: "0.45rem"
  md: "0.85rem"
  lg: "1.4rem"
  watch: "3.1rem"
spacing:
  page-inline: "3.25rem"
  section-gap: "4.5rem"
  panel-gap: "1rem"
components:
  navigation: {}
  watch-orbit: {}
  model-card: {}
  status-badge: {}
  scrollbar: {}
---

# 守望台设计系统

## Overview

### Creative North Star

界面像“家中安静的守护工作台”与“机械手表时间刻度”的结合：有医疗监护设备的可信、清楚和可追溯，但没有医院仪器的冰冷；有手表的时间感，但不模仿消费电子广告。

### Product context and register

- **受众与主要任务：** 比赛评委和零代码基础的项目成员，需要迅速看懂当前数据、三个模型的职责、告警原因和真实性边界。
- **目标市场与证据：** 当前为中国大陆简体中文比赛演示；业务范围来自 `PRODUCT.md`，数据真实性来自 `DATA_AND_MODEL_NOTICE.md`。
- **语言策略：** 首版只提供 `zh-CN`；技术名词第一次出现时同时给出通俗解释。
- **使用场景：** Windows 笔记本或投影大屏，短时演示与较长时间调试并存，信息密度中等。
- **界面类型：** 产品工具，不是营销落地页。
- **记忆点：** 中央“24 小时守护轨道”将时间、活动和告警统一到一块虚拟手表上。
- **克制区域：** 数据表、模型卡、来源与错误状态保持平静，不使用装饰性动态图形干扰读数。
- **反例：** 不使用常见深色霓虹科技大屏，不使用夸张医疗红，不把每个数字做成渐变 KPI 卡，不使用儿童化养老插画。
- **令牌归属与映射：** Model B。`frontend/src/style.css` 是当前运行时令牌源；本文件镜像并解释已接受值。每次系统级变更必须同时修改两处并通过 lint、构建和浏览器检查。

## Colors

`canvas` 是矿物浅灰绿，提供长时间观看的低刺激背景；`surface` 与 `surface-strong` 分隔内容层；`ink` 提供主要文字与手表深色屏幕。`primary` 只用于正常、可信和主要导航；`accent` 只用于时间节点与需要关注；`danger` 只用于真实紧急或不可逆危险，不用于一般装饰。焦点统一使用 `focus` 并同时提供轮廓，不依靠颜色单独表达状态。

首版为浅色主题。高对比模式使用系统强制色，不强行覆盖。黑暗模式在完成主要数据页并验证图表语义后再评估，不在第 1 步自动跟随系统切换。

## Typography

展示标题使用中文宋体类系统字体，强调“时间记录和可信档案”的气质；正文使用系统中文无衬线字体，保证 Windows 可读性和无需联网；时间、模型形状、版本和状态使用等宽字体。正文基准不小于 16px，说明文字最低约 12px，仅用于非关键辅助内容。中文不使用全大写和斜体；重要解释允许换行，不以省略号隐藏。

## Layout

桌面采用左侧固定语义导航、中央工作区和可选右侧溯源栏。首屏用一大一小两栏：虚拟手表是主叙事，系统状态是证据。页面自然滚动，不为表格需求给公共页面添加固定视口高度。小于 760px 时改为顶部横向导航与单列内容，以便窄窗口和 200% 缩放仍可阅读。

运行时映射：

| DESIGN.md | CSS 变量 | 主要使用者 |
|---|---|---|
| `colors.primary` | `--color-primary` | 当前导航、正常状态、主要标记 |
| `colors.accent` | `--color-accent` | 时间节点、需要关注 |
| `colors.danger` | `--color-danger` | 真正紧急告警 |
| `typography.body` | `--font-body` | 页面正文与控件 |
| `typography.data` | `--font-data` | 时间、版本、模型形状 |
| `rounded.md` | `--radius-md` | 导航与信息块 |
| `spacing.section-gap` | section `padding-top` / `margin-top` | 主页面分段 |

## Elevation & Depth

层级主要靠表面颜色、细边框与间距形成。主面板允许一个低对比大范围阴影，用于从方格背景中分离；静态小卡片不叠加多层阴影。虚拟手表允许内阴影与实体感，因为它是唯一的表现性对象。告警、表格和表单不使用玻璃模糊，以免降低可读性。

## Shapes

普通控件和信息块使用 `sm` 或 `md` 圆角，主面板用 `lg`；胶囊形只用于短状态标签；圆形只用于时间轨道、状态点与身份明确的图标。虚拟手表使用 `watch` 大圆角作为唯一例外。

## Components

### Foundational visual states

所有交互需要默认、悬停、键盘焦点、按下、禁用和忙碌状态。首选稳定空间中的应用加载指示器，不默认使用骨架屏。空数据必须写“暂无数据”，错误必须说明失败对象和下一步。状态除颜色外必须有文字或图标。

### Buttons and actions

后续共享按钮采用“强调程度 × 意图”体系。一个决策区域只有一个主要按钮。危险操作与普通操作分开，忙碌时保持尺寸。第 1 步没有需要按钮的业务动作，导航使用真实锚点，避免假按钮。

### Navigation and data display

导航使用真实链接并标记 `aria-current`。模型卡按 01—03 表示真实处理顺序。未来案例表使用服务端分页；窄屏保留可见横向滚动或转入详情，不静默隐藏来源字段。图表必须有文字摘要和原始值访问路径。

### Forms and overlays

未来表单统一使用应用校验和 `noValidate`。选择器、日期、对话框、通知和搜索建立共享组件后才允许页面使用。浏览器原生 `alert`、`confirm`、`prompt` 禁止进入产品界面。

### Iconography

首版使用简单几何线条和文字标签，不引入不必要图标库。图标不能代替关键文字。后续若引入图标，统一使用 1.75px 左右线性风格，并保留可访问名称。

### Motion

唯一环境动画是守护轨道的缓慢呼吸，表达系统持续观察。一般状态反馈 160—240ms；页面不使用连续漂浮、粒子或脉冲警报。`prefers-reduced-motion` 下立即停止位移与循环动画。

### Content and data visualization

文字使用主动、通俗、可验证的表达：“后端未连接”“暂无数据”“模型待接入”。不使用“全方位守护”“医学级准确”等没有证据的宣传。图表颜色固定含义：青绿为正常、琥珀为关注、红色为紧急；合成、受控和真实类别必须显示文字标签。

## Do's and Don'ts

- **Do：** 让用户随时知道数据来源、模型版本和当前是否真的运行。
- **Do：** 使用时间、轨道和事件证据构成界面结构，而不是无意义装饰。
- **Don't：** 用随机数字、静态截图或动画假装模型已经接入。
- **Don't：** 让视觉冲击压过输入质量、真实性和错误恢复信息。

