# 项目持续状态

更新时间：2026-08-28

## 总目标

完成一个可在 Windows 电脑上直接打开的三模型模拟智能手表平台，并保留数据来源、模型卡、测试报告和可复现命令。

## 当前步骤

第 1 步补充任务“Tabler 前端迁移”已经完成，保存在 `codex/tabler-ui-migration` 分支。当前必须停止并等待用户确认下一大关，不能自动进入后端或模型阶段。

## 本步已完成

- 保留 Vue 3、TypeScript 和 Vite；
- 精确锁定 `@tabler/core@1.4.0` 和 `@tabler/icons-vue@3.46.0`；
- 保存 Tabler Core 与 Tabler Icons 的 MIT 许可证文本；
- 建立共享 `AppShell`、`AppCard`、`StatusBadge` 和 `EmptyState`；
- 建立桌面侧栏、顶部工具栏和窄屏横向导航；
- 将巨大装饰手表改为小型设备与回放状态面板；
- 将三张独立模型卡改为连续三模型状态列表；
- 建立数据真实性与来源面板；
- 删除巨大宣传口号、宋体主标题、方格背景、呼吸动画、装饰编号和过度卡片化；
- 保留三模型职责、输入形状、来源追溯以及“未连接 / 暂无数据 / 待训练”等真实状态；
- 更新 `CONTEXT_HANDOFF.md`、`DESIGN.md`、`UX-CONTRACT.md` 与 `THIRD_PARTY_NOTICES.md`。

## 本步验证结果

- npm：54 个软件包审计，0 个已知漏洞；
- `npm --prefix frontend run build`：成功；Vue 类型检查和 Vite 生产构建均通过；
- 最终前端产物：CSS 约 544.45 kB（gzip 约 70.20 kB），JavaScript 约 77.34 kB（gzip 约 29.87 kB）；
- `designmd lint DESIGN.md`：0 个错误、0 个警告、1 条令牌汇总信息；
- Premium 严格审计：0 个错误、0 个警告、0 个未解决项；
- 反模式检查：没有原生 `alert` / `confirm` / `prompt`、假链接、非语义点击、未归属表单控件或旧 AI 风格关键词；
- 1440×900：桌面侧栏与两栏工作区，无页面级横向溢出，控制台 0 错误 / 0 警告；
- 1024×768：两列系统状态与单列工作区，无页面级横向溢出，控制台 0 错误 / 0 警告；
- 390×844：顶部横向导航与单列内容，无页面级横向溢出，控制台 0 错误 / 0 警告；
- 键盘焦点：首个“跳到主要内容”链接有清楚的 3px 蓝色焦点轮廓；
- 语义检查：1 个主区域、1 个主导航、1 个一级标题；没有重复 ID；所有锚点都有真实目标；未开放功能均为非交互文字；
- 动画检查：页面没有持续动画；存在 `prefers-reduced-motion` 降级规则；
- 滚动条：根页面与移动导航均继承全局令牌化滚动条，forced-colors 模式交还系统处理；
- 浏览器限制：实际验证使用 Codex 应用内 Chromium；用户侧 Chrome 和 Edge 扩展在本任务中不可连接，因此没有声称完成用户 Chrome 专项验收。

## 明确未完成

- 没有 FastAPI；
- 没有 SQLite；
- 没有 WebSocket；
- 没有下载或导入 100 个测试案例；
- 没有解压、重构或接入模型二；
- 没有训练模型三；
- 没有接入跌倒 ONNX；
- 没有创建或推送 GitHub 远程仓库；
- 没有新增任何模型指标。

## 运行命令

```powershell
cd "C:\Users\yangxinyi\Documents\Codex\2026-08-27\smartwatch-health-simulator"
npm --prefix frontend install
npm --prefix frontend run dev
```

默认本地地址：`http://127.0.0.1:5173/`

生产构建：

```powershell
npm --prefix frontend run build
```

## 下一大关（等待用户确认）

建议建立 FastAPI、SQLite 和 WebSocket，并让前端当前的“后端未连接”状态来自真实健康检查。没有得到用户明确确认前，不开始这一阶段。

## 用户约定

后续按“大关确认”协作：一个完整阶段实现、验证并提交后停止，不再为阶段内部的小步骤频繁请求确认。
