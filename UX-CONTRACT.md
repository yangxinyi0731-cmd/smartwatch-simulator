# 守望台 UX 合同

## Product context

- Audience：比赛评委、无代码基础项目成员、研究开发人员。
- Primary jobs：选择案例、播放数据、理解三个模型、追溯来源、导出报告。
- Target market(s)：中国大陆简体中文比赛演示。
- Active locales：`zh-CN`。
- Language/content register：通俗、诚实、可验证；关键技术词给出简体中文解释。
- Timezone/calendar policy：默认 `Asia/Shanghai`、公历；源数据保留原始时区和时间戳。
- Accessibility target：WCAG 2.2 AA。

## Business-context sources

| Domain / scope | Authoritative source | Source type | Reviewed date |
|---|---|---|---|
| 产品范围与三模型职责 | `PRODUCT.md` | 产品范围 | 2026-08-28 |
| 数据与模型真实性 | `DATA_AND_MODEL_NOTICE.md` | 真实性合同 | 2026-08-28 |
| 跌倒模型输入与审批状态 | 现有跌倒模型仓库 `models/fall_detector/tcn_final_candidate/manifest.json` | 模型合同，待第 11 步复制并固定哈希 | 2026-08-28 |
| 权限模型 | 本地单用户演示，首版无账号和角色 | 产品决定 | 2026-08-28 |
| 数据生命周期 | `docs/ARCHITECTURE.md` 的 SQLite 结构版本 4；来源、案例、导入批次、质量、真实标签、合成规律、manifest、回放和三模型独立输出 | 已实现并同步两个模型 | 2026-08-28 |
| 删除 / 保留 | 首版不提供删除原始来源数据的界面 | 产品决定 | 2026-08-28 |
| 计费 / 支付 | 不适用 | 不在范围 | 2026-08-28 |
| 法律 / 监管文案 | `DATA_AND_MODEL_NOTICE.md`；非医疗诊断 | 产品边界 | 2026-08-28 |
| 市场 / 内容约定 | `DESIGN.md` | 内容与视觉合同 | 2026-08-28 |

## Visual contract

- Project `DESIGN.md`：`DESIGN.md`。
- Token ownership model：运行时 CSS 为 canonical；DESIGN.md 镜像并解释。
- Runtime design-system/token source：Tabler Core 提供基础 CSS；`frontend/src/style.css` 的 `:root` 变量和共享组件提供本项目语义与最终覆盖。
- Mapping/export/adapters：`DESIGN.md` Layout 映射表。
- Token drift gate：`designmd lint`、静态审计、前端构建、浏览器检查。
- Supported themes：首版浅色；系统 forced-colors；不自动启用暗色。
- Design-context owner/review policy：任何全局颜色、字体、圆角和空间变化必须同时修改 CSS 与 DESIGN.md。
- Typography：标题与正文统一使用简体中文无衬线系统字体；不再使用宋体展示标题。
- Motion：不使用持续环境动画；只有表达交互状态的短过渡，并支持 `prefers-reduced-motion`。

## Canonical UI Map

| Capability | Canonical owner | Source of truth | Allowed variants | Verification |
|---|---|---|---|---|
| Table Selection | 第 12 步 `DataTable` 共享组件 | 本合同 | page / all-results | component + E2E |
| Select/Listbox | 第 12 步 `AppSelect` 共享组件 | DESIGN + 本合同 | authored | keyboard + popup |
| Date | 第 12 步 `DateField`，优先键盘输入 | 本合同 | typed | locale + keyboard + E2E |
| Form | 第 12 步共享 `FormField` 与 schema 适配器 | 本合同 | create / edit | validation E2E |
| Scrollbar | `frontend/src/style.css` 全局基线 | DESIGN.md | stable-gutter | computed style |
| Toast | 第 12 步共享 `AppToast` provider | 本合同 | success / warning / info / error | live-region test |
| CRUD | 首版案例为只读；未来共享 route/service 行为 | 本合同 | return / stay | full-flow E2E |

### 当前共享前端原语

| 能力 | Canonical owner | 当前规则 |
|---|---|---|
| 页面壳与主导航 | `frontend/src/components/AppShell.vue` | 桌面固定侧栏；窄屏顶部品牌区和横向导航；未开放功能不是假链接 |
| 内容分组 | `frontend/src/components/AppCard.vue` | 只包装真实信息组，不把每个数字做成独立卡片 |
| 状态标签 | `frontend/src/components/StatusBadge.vue` | neutral / info / success / warning / danger；颜色必须配文字 |
| 空状态 | `frontend/src/components/EmptyState.vue` | 说明缺少的内容和原因；不得提供无作用按钮或虚构数据 |
| 全局滚动条 | `frontend/src/style.css` | 根级标准属性 + WebKit 回退；forced-colors 交还系统处理 |
| 按钮 | `frontend/src/components/AppButton.vue` | 强调程度 × 语义意图；忙碌时尺寸稳定；当前用于真实刷新状态 |
| 系统连接状态 | `frontend/src/composables/useSystemConnection.ts` | HTTP 健康检查后建立 WebSocket；旧请求取消；断线有上限地自动重试 |
| HTTP 类型 | `frontend/src/api/generated/` | 从 `docs/contracts/openapi.json` 自动生成，不手工修改；构建时做 TypeScript 检查 |

## Component behavior

| Component | Default | Hover | Focus | Active | Disabled | Busy | Error |
|---|---|---|---|---|---|---|---|
| Link | 明确文本与真实目标 | 背景/文字变化 | 3px 可见轮廓 | 轻微色阶 | 未开放功能改为非交互文字并说明原因 | 不适用 | 不适用 |
| Button（未来） | 语义意图 | 色阶变化 | 3px 可见轮廓 | 按下反馈 | 不触发 | 尺寸稳定 | 邻近说明 |
| StatusBadge | 状态点 + 文字 | 不交互 | 不获取焦点 | 不适用 | 不适用 | 文字显示处理中 | 文字说明错误对象 |
| EmptyState | 缺少内容 + 原因 | 不交互 | 内部真实操作才获取焦点 | 不适用 | 不适用 | 与加载状态分开 | 失败状态提供恢复说明 |
| Search（未来） | 清除按钮 + 300ms debounce | 共享字段状态 | IME 安全 | Enter 非合成态提交 | 说明原因 | 保留尺寸 | 区域内恢复 |
| Table/list（未来） | 有标题/总数 | 行强调 | 行内目标可见 | 当前选择 | 说明原因 | 保留表框 | 重试状态 |

## Dataset navigation

- Admin tables：100 案例库与事件日志使用服务端分页。
- Exploratory lists：小型演示故事可以全部渲染；上限由后端合同固定。
- URL state：提交后的搜索、来源、真实性、适用模型、排序、页码和页大小进入 URL。
- Page size：默认 20，可选 10/20/50。
- Empty/no-results/error/loading：分别显示“尚未导入”“没有匹配”“加载失败 + 重试”“稳定区域加载中”。
- Back/scroll restoration：浏览器返回恢复筛选、页码和滚动位置。
- Selection scope：默认当前页；全结果选择必须明确总数并二次确认批量高风险操作。

## Flow ledger

| Operation | Trigger | Pending | Success destination | Success feedback | Failure recovery | Focus outcome | Source ref |
|---|---|---|---|---|---|---|---|
| 开始回放 | “开始回放” | 初次读取时按钮稳定忙碌 | 当前回放区 | 状态区、时钟和真实游标显示运行中 | 保留案例并可重新读取 | 回放控制区 | PRODUCT.md |
| 暂停回放 | “暂停” | 同步按钮状态 | 当前回放页 | 时间轴停止 | 显示失败原因 | 原按钮 | PRODUCT.md |
| 重置回放 | “重置回放” | 悲观等待 | 当前案例起点 | 状态区确认 | 保留当前状态并重试 | 开始回放 | PRODUCT.md |
| Search | 案例搜索框 | 保留列表框架 | 当前路由查询 | 结果数状态 | 搜索区重试 | 搜索框 | 本合同 |
| Upload/background job | “运行全部案例” | 持久阶段进度 | 报告详情 | 报告已生成 | 可恢复/重试失败案例 | 报告标题 | PRODUCT.md |
| Cancel/back | “返回案例库” | 无 | 来源页面 | 通常无 | 未保存时应用对话框 | 原触发位置 | 本合同 |
| 刷新系统状态 | “刷新状态” | 按钮保持尺寸并显示“检查中” | 当前总览 | 状态条和连接说明更新 | 保留空状态并自动重试 | 原按钮 | `docs/ARCHITECTURE.md` |

## Navigation and responsive behavior

- Route document title policy：`{页面} — 模拟智能手表`；当前单页固定为“系统总览 — 模拟智能手表”，未来路由、加载、错误、403/404 使用各自诚实标题。
- Route error / 403：首版本地单用户无 403；404 和 5xx 保留应用导航、说明原因与返回/重试。
- Breadcrumb/tab/route state：顶层页面使用路由链接；同一案例的同级视图才使用 route-backed tabs。
- Sidebar transformation：桌面固定侧栏；小于 760px 转为顶部品牌区和可横向滚动导航，不隐藏当前项。三模型子项在窄屏收拢到“三模型中心”顶层入口，内容区仍保留三个模型锚点。
- Unavailable navigation：尚未实现的案例库、告警记录和测试报告显示“未开放”，使用非交互元素并附原因，不使用空 `href`、`href="#"` 或无效果按钮。
- Responsive table：优先横向滚动并保留案例 ID 与来源；详情页显示全部字段。
- Truncation：来源、错误与真实性说明不截断；长哈希可显示短预览并提供复制。
- Focus restoration：路由后聚焦主标题；对话框关闭回到触发器；sticky 区域不得遮挡焦点。

## Overlays and feedback

- Dialog primitive：第 12 步使用验证过的 Vue 可访问对话框共享组件。
- Destructive confirmation：首版无删除；未来可恢复为 warning，不可恢复为 danger。
- Toast：右上稳定位置、去重；成功约 4 秒，错误不只放在 toast。
- Alert/banner：连接中断使用持续页级 banner；紧急跌倒使用可访问 alert 与事件详情。
- Tooltip：辅助信息才使用；悬停和键盘焦点均打开，Escape 关闭。
- Unsaved changes：设置和注释表单变脏时使用应用对话框；浏览器关闭只用 narrow `beforeunload`。
- Layer：dialog > drawer > popover > toast；具体 z-index 在共享令牌建立时固定。

## Async and resilience

- Mutation default：悲观确认。
- Idempotency：当前只读预览在浏览器内播放，不创建后端写会话；未来回放持久会话和报告任务必须使用客户端请求 ID，按钮阻止重复提交。
- Auto-save：首版不自动保存敏感设置；本地草稿必须明确标记。
- Offline：保留已加载案例，显示持续连接状态；后端写操作不静默排队。
- Retry：健康检查只重试安全 GET，使用 1/2/5/10 秒有上限退避；切换页面可见性或手动刷新时取消旧请求并重新核验。其他操作提供明确重试。
- Conflict：首版本地单进程；版本冲突时重新读取，不覆盖较新记录。
- Session：首版无账号；未来认证另行更新合同。
- Progress：已知总数用确定进度，未知使用阶段名称，不显示假百分比。
- Stale request：搜索和切换案例取消旧请求；旧响应不得覆盖新状态。
- Dialog/form failure：失败时保持打开并保留非敏感输入。

## Validation

- Schema：后端 `backend/app/contracts.py` 为 Pydantic 合同源，导出 `docs/contracts/openapi.json` 与 `domain-contract.schema.json`，前端类型自动生成到 `frontend/src/api/generated/`；表单使用共享 schema 适配层。
- Timing：首次提交后显示错误，错误字段再在 change/blur 校验。
- Error：长表单有摘要，所有字段错误有文字、`aria-invalid` 和有效 `aria-describedby`。
- Server error：字段错误映射字段，全局错误持久显示且不暴露原始堆栈。
- Sensitive value：首版无密钥输入；未来默认遮罩并提供可访问显示/隐藏。
- 所有产品表单 `noValidate`，无效提交聚焦首个错误，阻止重复提交，失败后保留非敏感输入。

## Permission and clipboard

- Permission UI：首版不适用；后续有权限时明确区分隐藏、禁用和 403。
- Clipboard：哈希、案例 ID 可复制；toast 只确认“已复制”，不重复显示敏感内容。
- Disabled explanation：不可用模型和案例显示明确原因，不只变灰。

## Verification

- Required static commands：DESIGN lint、premium strict audit、anti-pattern rg、前端构建。
- Browser matrix：Windows Chrome/Edge；1440×900、1024×768、窄窗口 390×844；200% zoom 为扩展检查。
- Accessibility：键盘、可见焦点、语义、对比度、reduced motion、forced colors。
- Current page states：总览必须验证检查中、后端未连接、HTTP 成功但实时通道断开、完整连接、SQLite 结构版本 4、101 案例、两个已登记研究模型、活动模型待训练、案例读取失败、回放读取失败、WEDA 六轴回放和 100 天合成规律回放。波形只能来自已核验文件，规律时间线必须标记合成。
- Component-state：后续组件建立 Vitest、Playwright 与视觉状态覆盖。
- Canonical sibling：第 1 步为新项目无 sibling；以后以守望台总览为视觉基线。
- CRUD/failure evidence：当前无 CRUD；第 2 步开始记录 API 失败路径。
