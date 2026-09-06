# 守望台 UX 合同

## Product context

- Audience：现有三模型产品面向比赛评委、无代码基础项目成员和研究开发人员；独立校赛风险评估台面向现场评委和项目成员，同时保留研究核对入口。
- Primary jobs：上传新的六轴记录或从 105 组公开案例中选择一组，以同一套六步判断框架完成输入检查、标准化、适用模型实算和结果生成；按“结论—依据—模型推导—边界”核对实际波形与逐秒 1/2/3 秒研究曲线。自主采集区显示 P01 的30组接入与工程验证状态，并保留单参与者限制。
- Target market(s)：中国大陆简体中文比赛演示。
- Active locales：`zh-CN`。
- Language/content register：通俗、诚实、可验证；公众层先用生活语言，E0、Gate、dry-run、AUPRC、ECE 等技术词只能放在次要说明或展开区，并必须给出简体中文含义。
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
- Runtime design-system/token source：`frontend/src/tokens.css` 是两个本机界面的唯一共享令牌源；Tabler Core 与 `frontend/src/style.css` 实现三模型产品，`research/early_risk/workbench/app.css` 实现隔离的 E0 研究工作台。
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
| Select/Listbox | 当前版本使用浏览器原生 `select` | `premium-ui.json` + 本合同 | native | keyboard + popup |
| Date | 第 12 步 `DateField`，优先键盘输入 | 本合同 | typed | locale + keyboard + E2E |
| Form | 校赛工作台 `#upload-form`；产品后续共享 `FormField` | 本合同 + `docs/early_risk/NEW_DATA_FORMAT.md` | local file analysis / future create-edit | client + server validation E2E |
| Scrollbar | 每个文档的全局样式消费 `frontend/src/tokens.css` | DESIGN.md | stable-gutter | computed style |
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
| 测试报告 | `frontend/src/composables/useReports.ts` 与 `#reports` | 只读已保存报告；显示证据范围、解释、限制与 SHA-256；JSON 下载使用真实 GET 端点 |
| 校赛模拟手表风险评估台 | `research/early_risk/workbench_server.py` 与 `research/early_risk/workbench/` | 独立回环服务；上传表单与 105 组案例共用六步分析合同、六步视觉组件和结果阅读顺序。WEDA 运行满足条件的三个传感器模型；CAPTURE-24 运行真实活动模型并把另外两项标为不适用；规律案例运行真实规则模型；不写 SQLite、不保存上传文件、不启用外部通知；不挂载到产品 UI |
| 校赛六步判断流程 | `research/early_risk/upload_analysis.py::build_analysis_pipeline` + `research/early_risk/workbench/app.js::renderSharedPipeline` | 固定顺序为检查输入、统一标准、识别动作或规律、筛查跌倒、分析提前风险、生成结果；上传与案例只允许改变来源详情和实际状态，禁止复制出第二套流程 |
| 校赛结果分析 | `analysis.interpretation` + `renderReasonedAnalysis` | 固定顺序为结论先看、关键实测依据、各模型如何参与、交叉核对过程、最终结论、计算规则和适用边界；状态必须使用文字，未运行不等于零风险 |

## Component behavior

| Component | Default | Hover | Focus | Active | Disabled | Busy | Error |
|---|---|---|---|---|---|---|---|
| Link | 明确文本与真实目标 | 背景/文字变化 | 3px 可见轮廓 | 轻微色阶 | 未开放功能改为非交互文字并说明原因 | 不适用 | 不适用 |
| Button（未来） | 语义意图 | 色阶变化 | 3px 可见轮廓 | 按下反馈 | 不触发 | 尺寸稳定 | 邻近说明 |
| StatusBadge | 状态点 + 文字 | 不交互 | 不获取焦点 | 不适用 | 不适用 | 文字显示处理中 | 文字说明错误对象 |
| EmptyState | 缺少内容 + 原因 | 不交互 | 内部真实操作才获取焦点 | 不适用 | 不适用 | 与加载状态分开 | 失败状态提供恢复说明 |
| E0 Search | 输入即筛选 + 显式清除按钮 | 字段边框强调 | 3px 可见轮廓 | 匹配时同步首个可见案例 | 不适用 | 保留尺寸 | 无结果文字状态 |
| E0 Case list | 类型总数 + 6 条/页 | 行背景与边框强调 | 行按钮可见轮廓 | `aria-pressed` 当前选择 | 翻页边界禁用 | 选择时尺寸稳定 | 保留已选案例并允许重新读取 |
| E0 Watch controls | 开始、暂停、重置 | 色阶变化 | 3px 可见轮廓 | 当前阶段与共用六步流程同步 | 实际案例依据未读取时不启动 | 已知六步确定进度 | 页面级连接错误提供重新连接 |
| New-data upload | 可见文件标签、拖放区、两个单位选择器 | 边框强调 | 3px 可见轮廓 | 显示文件名和大小 | 忙碌时禁用更换与重复提交 | 稳定按钮文字“正在运行全部模型” | 相邻持久文字错误，保留文件并可重试 |

## Dataset navigation

- Admin tables：100 案例库与事件日志使用服务端分页。
- Exploratory lists：小型演示故事可以全部渲染；上限由后端合同固定。
- URL state：提交后的搜索、来源、真实性、适用模型、排序、页码和页大小进入 URL。
- Page size：默认 20，可选 10/20/50。
- E0 case page size：前端固定 6 条/页；105 组登记案例按类型显示 `105 / 40 / 60 / 4 / 1` 总数。切换筛选、翻页或有效搜索结果后，如果原选中项不可见，手表和判断区同步到首个可见案例。
- E0 search state：搜索仅在当前类型中按案例 ID、短标题或参与者匹配；清除后留在当前类型并重新同步选择；无匹配时保留手表当前案例并明确显示空结果。
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
| 分析新数据 | “开始分析新数据” | 六步阶段名，不显示假百分比；按钮尺寸稳定 | 当前上传结果区 | 四项事实、双证据图、生成结论 | 保留文件和单位；相邻错误说明后重试 | 成功聚焦结果标题，失败聚焦错误区 | `docs/early_risk/WORKBENCH.md` |
| Cancel/back | “返回案例库” | 无 | 来源页面 | 通常无 | 未保存时应用对话框 | 原触发位置 | 本合同 |
| 刷新系统状态 | “刷新状态” | 按钮保持尺寸并显示“检查中” | 当前总览 | 状态条和连接说明更新 | 保留空状态并自动重试 | 原按钮 | `docs/ARCHITECTURE.md` |
| 下载报告 | “下载 JSON” | 浏览器原生下载 | 当前页面 | 获得统一报告快照 | 后端错误响应保留可重试说明 | 原链接 | `docs/ARCHITECTURE.md` |
| 筛选 E0 案例 | 全部/受控跌倒/日常活动/活动识别/生活规律 | 无网络等待 | 当前检测台 | 列表总数、分页、手表和判断区同步 | 无匹配时显示空结果；不伪造案例 | 原筛选按钮 | `docs/early_risk/WORKBENCH.md` |
| 选择 E0 案例 | 案例行按钮 | 立即重置上次前端阶段；判断依据区显示文件核对状态 | 当前检测台 | 手表编号、输入规格、事实标签、判断过程和依据图同步 | 读取失败时明确显示“依据不可用”，不生成替代曲线；仍可选择其他案例或重新读取 | 原案例行 | `docs/early_risk/WORKBENCH.md` |
| 开始模拟检测 | “开始检测” | 共用六步依次显示，按钮尺寸稳定；实际依据未就绪时不提前运行 | 当前检测台 | WEDA 显示三个传感器模型实算；CAPTURE-24 显示活动模型实算及两项不适用原因；规律案例显示规则实算 | 可暂停、继续或重置；依据缺失时停止并显示原因；不创建后端写入 | 检测控制区 | `docs/early_risk/WORKBENCH.md` |
| 暂停/继续模拟检测 | “暂停检测”/“继续检测” | 前端计时器停止或继续 | 当前检测台 | 阶段编号与状态文字保持一致 | 可重置到等待状态 | 原控制按钮 | `docs/early_risk/WORKBENCH.md` |
| 重置模拟检测 | “重置本次检测” | 立即停止前端阶段 | 当前检测台 | 当前案例保持，结果回到等待运行 | 可重新开始；不改变保存结果 | 开始检测 | `docs/early_risk/WORKBENCH.md` |
| 读取 E0 判断依据 | 选择案例自动触发 `GET /api/case-evidence/{case_id}` | 保留区域尺寸并显示“正在核对” | 当前检测台 | 返回共用六步状态和结构化解释；WEDA/CAPTURE-24 显示经哈希与形状核对的真实合量波形，规律案例显示固定种子事件时间图 | 404/503 时显示文字错误态；禁止示意曲线、静态结论或旧案例响应覆盖新选择 | 原案例行 | `docs/early_risk/WORKBENCH.md` |
| 移除新文件 | 文件行关闭按钮 | 立即取消当前可选状态 | 当前上传表单 | 回到空文件状态，清除旧结果 | 不适用 | 文件选择器 | `docs/early_risk/NEW_DATA_FORMAT.md` |

## Navigation and responsive behavior

- Route document title policy：`{页面} — 模拟智能手表`；三模型页固定为“系统总览 — 模拟智能手表”，独立 E0 页固定为“模拟手表检测台 — 模拟智能手表”；未来路由、加载、错误、403/404 使用各自诚实标题。
- Route error / 403：首版本地单用户无 403；404 和 5xx 保留应用导航、说明原因与返回/重试。
- Breadcrumb/tab/route state：顶层页面使用路由链接；同一案例的同级视图才使用 route-backed tabs。
- Sidebar transformation：桌面固定侧栏；小于 760px 转为顶部品牌区和可横向滚动导航，不隐藏当前项。三模型子项在窄屏收拢到“三模型中心”顶层入口，内容区仍保留三个模型锚点。
- Unavailable navigation：尚未实现的案例库和告警记录显示“未开放”，使用非交互元素并附原因，不使用空 `href`、`href="#"` 或无效果按钮；测试报告使用真实 `#reports` 锚点。
- 校赛页面导航：桌面侧栏只使用“新数据检测、实时检测、案例回放、判断过程、模型状态、说明与边界”六个真实锚点；小于 820px 转成可横向滚动的顶部导航。公开代理模型显示“已接入”，现实预测证据与 P3–P9 仍只在边界区说明，不伪装成已完成产品能力。
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
- 校赛页面：重新读取会取消旧 GET；切换案例会取消旧判断依据请求；新上传会取消上一条上传请求，旧响应不得覆盖新状态。`POST /api/analyze-upload` 只接受 5 MB 内标准 CSV/JSON，经客户端扩展名检查和服务端表头、数值、时间、六轴、采样率、单位检查后在内存中运行模型；不写 SQLite、不进入案例登记。WEDA 六轴案例通过 `GET /api/case-evidence/{case_id}` 真实运行跌倒与提前风险模型；CAPTURE-24 和合成规律仍按其独立输入边界展示。策略模拟端继续拒绝关闭 dry-run。
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
- Current page states：总览必须验证检查中、后端未连接、HTTP 成功但实时通道断开、完整连接、SQLite 结构版本 5、105 案例、三个已登记研究模型、案例读取失败、回放读取失败、WEDA 六轴回放、100 天合成规律回放和 CAPTURE-24 三轴活动回放。波形只能来自已核验文件，规律时间线必须标记合成，活动数据必须标明恢复前缀子集和人群限制。
- 校赛 page states：验证本机内容读取中、读取失败/重试；上传空状态、合法 CSV、合法 JSON、缺少陀螺仪、错误编码、超大文件、短于 1 秒拒绝、1–4 秒部分模型降级、4–20 秒活动模型降级、20 秒以上全部模型完成、移除和重试；自主采集显示 30/约30组和“已完成质量与工程复核”。成功结果必须显示数据质量、当前动作候选、跌倒筛查、未持久化、加速度/角速度实际波形、1/2/3 秒逐秒曲线、各自阈值、代理锚点说明、判断依据和最终结论。继续验证 105 组公开案例分类、搜索、分页、手表控制、真实 WEDA 模型响应、CAPTURE-24、合成规律、依据失败、六项导航唯一 `aria-current`、四个模型中文释义和外部通知 0 次。人物统一称“参与者”，不得显示“综合风险分”。1440×900 与 390×844 均不得页面级横向溢出，所有可见操作目标至少 44×44px。
- Component-state：后续组件建立 Vitest、Playwright 与视觉状态覆盖。
- Canonical sibling：第 1 步为新项目无 sibling；以后以守望台总览为视觉基线。
- CRUD/failure evidence：当前无 CRUD；第 2 步开始记录 API 失败路径。
