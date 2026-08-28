# Tabler 前端迁移完整交接

> 本文是新对话的首要入口。接手者必须先完整阅读本文，再按下文列出的顺序阅读其他项目文档，并先做只读 Git 检查。

## 1. 项目位置与 Git 状态

- 实际项目目录：`C:\Users\yangxinyi\Documents\Codex\2026-08-27\smartwatch-health-simulator`
- 当前功能分支：`codex/tabler-ui-migration`
- 本轮起点提交：`4d53e93 docs: hand off Tabler migration context`
- 更早的基础提交：`57034ba chore: establish smartwatch simulator foundation`
- 当前没有配置 Git 远程仓库；不得自行创建或推送 GitHub 远程。
- Tabler 迁移的最终提交以 `git log -1 --oneline` 的实际输出为准，不在本文预写提交哈希。

新对话开始后，必须在上述目录执行并向用户报告：

```powershell
git status --short
git log -3 --oneline
git remote -v
```

## 2. 必须按顺序阅读的文件

1. `TABLER_MIGRATION_HANDOFF.md`（本文）
2. `CONTEXT_HANDOFF.md`
3. `PRODUCT.md`
4. `DATA_AND_MODEL_NOTICE.md`
5. `TASK_STATE.md`
6. `DESIGN.md`
7. `UX-CONTRACT.md`
8. `THIRD_PARTY_NOTICES.md`

阅读和只读检查完成后，先用简体中文向用户通俗总结现状。不要仅凭交接文档假定工作树状态，必须以现场 Git 输出为准。

## 3. 产品目标与当前边界

这是一个“老年人 AI 模拟智能手表平台”的研究原型，当前前端用于表达设备状态、回放状态、数据来源与三个模型的职责，不是已经接通真实设备和真实模型的医疗产品。

当前已经完成的大关只有“Tabler 前端迁移”：

- 保留 Vue 3、TypeScript、Vite。
- 采用 Tabler 的基础视觉、布局和图标。
- 保留简体中文、三模型职责、数据真实性、来源追溯和所有“未连接 / 暂无数据 / 待训练”状态。
- 移除了巨大宣传口号、宋体主标题、方格背景、巨大装饰手表、呼吸动画、无流程含义的编号和过度卡片化。

本轮明确没有开始：

- FastAPI
- SQLite
- WebSocket
- 数据导入
- 真实设备接入
- 三个模型的代码接入
- 模型训练或指标计算
- GitHub 远程创建或推送

这些工作属于后续大关，必须由用户再次确认具体范围后才能开始。

## 4. 数据真实性与模型表述红线

所有后续页面、文档、演示和代码都必须遵守以下边界：

- 本项目是研究与演示原型，不是医疗诊断、急救或照护替代品。
- 不得编造或声称未实际测得的准确率、召回率、误报率、延迟、覆盖率等指标。
- 不得用随机数伪装真实传感器数据，不得用全零陀螺仪等方式伪造完整样本。
- 每条可用数据都应保留来源、采集或生成方式、时间、参与者或数据集边界等追溯信息。
- 三个模型职责不同，输出必须分开展示，不能把结果平均成一个貌似可靠的总分。
- 模型一是跌倒检测；现有跌倒素材边界是年轻参与者在受控条件下模拟跌倒，不是真实老年人跌倒。老年参与者只涉及日常活动（ADL）边界。不得把受控模拟结果改写成真实老人跌倒证据，也不得声称能预测未来跌倒。
- 模型二是个人日常行为偏离识别；当前只是基于合成日常规律的原型设想，尚未由真实老年人长期数据训练或验证。
- 模型三是异常风险评估；当前处于待训练状态，没有可发布的模型指标。
- “未连接”“暂无数据”“待训练”等状态必须真实保留，不能为了界面好看而假装已经接通。

更完整的事实边界以 `PRODUCT.md` 和 `DATA_AND_MODEL_NOTICE.md` 为准。

## 5. Tabler 依赖与许可证

依赖已经固定为精确版本：

- `@tabler/core`：`1.4.0`
- `@tabler/icons-vue`：`3.46.0`

项目只引入 Tabler 官方 CSS 和 Vue 图标组件，没有引入 Tabler 演示页脚本。`@tabler/core` 的传递依赖包含 Bootstrap 与 Popper，实际锁定版本以 `frontend/package-lock.json` 为准。

许可证材料：

- `licenses/TABLER_CORE_LICENSE.txt`
- `licenses/TABLER_ICONS_LICENSE.txt`
- `THIRD_PARTY_NOTICES.md`

继续升级依赖前，必须重新核对官方包版本、许可证和构建结果，不能把范围符号改回浮动版本而不说明原因。

## 6. 本轮前端实现

主要文件：

- `frontend/src/App.vue`：系统总览页面，包含桌面侧栏、移动端横向导航、顶部工具栏、状态条、设备与回放状态、来源追溯、三模型职责和真实空状态。
- `frontend/src/main.ts`：引入 Tabler 官方 CSS。
- `frontend/src/style.css`：项目级设计令牌、布局、响应式、焦点、滚动条、强制颜色和减少动态效果规则。
- `frontend/index.html`：中文页面标题。
- `frontend/src/components/AppShell.vue`：应用外壳。
- `frontend/src/components/AppCard.vue`：统一内容容器。
- `frontend/src/components/StatusBadge.vue`：统一状态标签。
- `frontend/src/components/EmptyState.vue`：统一空状态。

关键设计选择：

- 产品形态是研究与健康监测工作台，不是营销落地页。
- 页面签名特征是“真实性与来源状态条”，而不是装饰性视觉特效。
- 桌面端使用语义侧栏；窄屏使用可横向滚动的导航，避免压缩成不可读的小按钮。
- 未开放的“案例库 / 告警记录 / 测试报告”是带“未开放”说明的非交互文本，不伪装成可点击链接。
- 页面没有持续动画；键盘焦点清晰，并提供跳到主内容的链接。
- 运行时设计令牌与 `DESIGN.md` 同步维护，避免文档和实际界面漂移。

## 7. 同步更新的文档

- `DESIGN.md`：Tabler 设计方向、颜色与排版令牌、组件映射、响应式行为和禁用的反模式。
- `UX-CONTRACT.md`：应用外壳、导航、状态、空状态、交互和浏览器行为契约。
- `THIRD_PARTY_NOTICES.md`：依赖版本、官方仓库、用途和许可证路径。
- `TASK_STATE.md`：本大关完成状态、验证证据、浏览器限制、下一授权边界。
- `CONTEXT_HANDOFF.md`：从“准备迁移”更新为“迁移完成并等待下一大关”。
- `premium-audit.json`：严格设计审计结果（如审计脚本生成内容发生变化，以 Git 中最终版本为准）。

## 8. 已完成的验证

迁移完成后已执行以下验证：

```powershell
npm --prefix frontend run build
npm --prefix frontend audit
npx -p @google/design.md designmd lint DESIGN.md
python C:\Users\yangxinyi\.codex\plugins\cache\openai-curated-remote\frontend-design-premium\1.4.0\skills\frontend-design-premium\scripts\audit_project.py C:\Users\yangxinyi\Documents\Codex\2026-08-27\smartwatch-health-simulator --mode strict
git diff --check
```

已获得的结果：

- Vite 生产构建成功。
- npm 安全审计为 0 个已知漏洞。
- DESIGN lint 为 0 errors、0 warnings。
- 严格设计审计为 0 findings、0 errors、0 warnings、0 unresolved。
- Git 空白检查没有错误；PowerShell/Git 可能只提示未来换行符转换，不等同于校验失败。
- 反模式检查未发现原生 `alert / confirm / prompt`、伪造 `href="#"`、无动作按钮、危险 HTML、浏览器存储滥用、旧版巨大手表或呼吸动画残留。

提交前应再执行一次最终构建、DESIGN lint、严格设计审计和 Git 检查，以最终输出为准。

## 9. 真实浏览器验证结果与限制

已经在真实 Chromium 浏览器页面中验证：

- `1440 × 900`：桌面侧栏、顶部工具栏和双栏工作区正常，无页面级横向溢出，控制台无错误或警告。
- `1024 × 768`：状态条切为两列，主内容切为单列，无页面级横向溢出，控制台无错误或警告。
- 约 `390 × 844`：状态、主内容和回放区为单列；导航在自身容器内横向滚动，页面本身不横向溢出；三模型职责可完整阅读，控制台无错误或警告。
- 键盘跳转主内容链接可见，焦点轮廓清晰。
- 页面只有一个 `main`、一个主导航和一个 `aside`；没有重复 ID，页面内锚点都有真实目标。
- 页面没有运行中的动画；样式中保留 `prefers-reduced-motion` 规则。

重要限制：用户 Chrome 和 Edge 的 Codex 控制扩展当时不可用，因此以上验证使用 Codex 应用内的真实 Chromium 浏览器完成。它证明了真实浏览器布局、交互、溢出和控制台状态，但不能被表述为“已经完成 Chrome 专属兼容性验证”。如后续要发布，应在用户可用的目标 Chrome、Edge 和真实移动设备上再做一轮发布级验收。

## 10. 已修复的浏览器实测问题

真实浏览器验证期间发现并修复了：

- Tabler 基础样式曾让桌面工作区掉到侧栏下方；通过明确应用外壳为横向布局修复。
- 页面标题区曾受基础样式影响排列方向；已明确桌面标题区布局。
- 1024 像素宽度下第一项系统状态文字过度换行；已提前进入两列状态布局。

这些问题说明后续修改仍必须经过真实浏览器验证，不能只依赖构建成功。

## 11. 下一大关建议

Tabler 迁移提交后必须停止，不要直接编码后端。新对话先报告当前状态并等待用户选择下一大关。

如果用户授权进入后端，建议先把下一大关定义为“最小本地数据闭环的技术设计与骨架”，再明确是否包含：

- FastAPI 服务骨架
- SQLite 数据结构
- WebSocket 消息协议
- 前后端连接的最小真实状态流
- 测试与启动说明

即使授权后端，也不要顺带开始数据集导入、模型训练或真实设备接入，除非用户明确把它们纳入同一个大关。

## 12. 协作节奏

用户没有代码基础，解释应使用简体中文和通俗语言。用户已明确不希望每个小步骤都反复确认：

- 一个“大关”开始前确认一次范围。
- 大关内部可连续完成代码、文档、测试和小修复，无需逐步打断。
- 大关完成后立即停止，给出改了什么、为什么、验证结果、限制、Git 提交和下一大关选项。
- 未经新确认，不进入下一大关。

## 13. 新对话启动检查表

- [ ] 位于正确项目目录，而不是 Codex 自动生成的空目录。
- [ ] 完整阅读本文及第 2 节列出的全部文档。
- [ ] 报告 `git status --short`、`git log -3 --oneline`、`git remote -v`。
- [ ] 确认 Tabler 迁移提交存在、工作树状态明确、没有远程仓库。
- [ ] 用简体中文说明真实性边界和当前未完成范围。
- [ ] 不重复 Tabler 迁移，不自动开始后端或模型工作。
- [ ] 等待用户确认下一大关。
