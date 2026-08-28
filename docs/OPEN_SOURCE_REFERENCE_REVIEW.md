# 近期相似开源项目核验记录

核验日期：2026-08-28

## 为什么做这次检索

本项目需要同时处理传感器来源、案例回放、三个独立模型、研究真实性和 Windows 本地演示。没有一个开源项目能原样满足全部边界，因此采用“核验后组合思路”的方式：只吸收成熟架构与合同设计，不复制未经验证的指标，也不把公开下载误写成可重新分发。

检索先通过网页搜索定位候选，再通过 GitHub API 核对默认分支、最近推送时间、归档状态和 GitHub 可识别许可证，最后用 `git ls-remote <url> HEAD` 固定当日远程 HEAD。下表中的日期和提交是本次实际查询结果，不代表未来自动更新。

## 采用与排除结论

| 项目 | 2026-08-28 固定 HEAD | GitHub 许可状态 | 本项目参考内容 | 明确不照搬的内容 |
|---|---|---|---|---|
| [RADAR-base/RADAR-Kubernetes](https://github.com/RADAR-base/RADAR-Kubernetes) | `f1a6aab14ee103852af9dd400bd3b1456dc9c566` | Apache-2.0；未归档；最近推送 2026-08-25 | 采集、流、存储、监控分层；数据源独立登记 | Kubernetes、Kafka 等集群复杂度不适合本地比赛演示，不引入 |
| [openmhealth/schemas](https://github.com/openmhealth/schemas) | `df386000a93a35c1d7f33a023f759e41202a7d3d` | Apache-2.0；未归档；最近推送 2026-08-26 | 数据点头部的来源、时间、schema 版本与 acquisition provenance 思路 | 不声称本项目已符合完整 Open mHealth 或 FHIR；上游已注明部分睡眠/活动 schema 被 IEEE 1752.1 取代 |
| [awareframework/aware-client](https://github.com/awareframework/aware-client) | `f77e873baaedfc649fd39ca8f3547f914c3e6b32` | Apache-2.0；未归档；最近推送 2026-08-07 | 传感器采集、本地保存、同步和研究配置分离 | 当前范围没有手机端与真实设备采集，不复制权限或后台常驻逻辑 |
| [fastapi/full-stack-fastapi-template](https://github.com/fastapi/full-stack-fastapi-template) | `2ccfa25845dec4c70b8a7b653ed347b2905240b6` | MIT；未归档；最近推送 2026-08-27 | OpenAPI 生成前端类型、Pytest 与端到端验证路线 | 该模板使用 React、PostgreSQL、认证和容器部署；本项目保留 Vue、SQLite、本地单用户 |
| [the-momentum/open-wearables](https://github.com/the-momentum/open-wearables) | `f766b5a0a45b091828317d30c5e516574adfbe61` | MIT；未归档；最近推送 2026-08-28 | 自托管 FastAPI、统一可穿戴数据 API、来源适配器与人工反馈边界 | 当前项目是离线模拟研究平台，不引入厂商 OAuth、云同步或把样例数据冒充真实设备记录 |
| [DevGurav/fall-detect-system](https://github.com/DevGurav/fall-detect-system) | `5879f92c5643f97a32302f4eb74b05a3fb07929a` | MIT；未归档；最近推送 2026-08-22 | 最相似的“腕部跌倒 + 虚拟设备回放 + 事件流”拆分，可作为回放边界检查清单 | 不复制其自报指标、目标阈值或数据许可结论；这些都不是本项目实测证据 |
| [joaojtmarques/WEDA-FALL](https://github.com/joaojtmarques/WEDA-FALL) | `74e0b93cb061d4ecbca12628f2d47090e97fbeea` | GitHub API 未识别到许可证；最近推送 2026-08-24 | 腕部 50 Hz 六轴来源、年轻模拟跌倒与老人 ADL 误报分析 | 原始数据不进本仓库，不默认允许再分发或商用；老人没有执行跌倒 |
| [CAPTURE-24 数据与工具](https://doi.org/10.1038/s41597-024-03960-3) | 工具参考仓库 `f861b44f5675cb3e8294cd3d560d7a71a749616f` | 论文明确数据为 CC BY 4.0；GitHub 工具代码为 Oxford Academic Use Licence，不是同一许可 | 参与者分组后切窗、100 Hz 腕部自由生活活动标签、活动识别基线 | 不复制工具代码；不把以年轻参与者为主的自由生活活动描述为老人数据；原始数据不进 Git |
| [Forsad/Stable-Polynomial-Train](https://github.com/Forsad/Stable-Polynomial-Train) | `9a6fee44f84a7eeb941e731e9d960c66297fd655` | MIT；2025-06-04 固定提交 | 近期 CAPTURE-24 参与者分组、稳定训练与隐私计算路线；公开 Google Drive 包用于结构交叉核验 | 该包只有 sleep/sedentary/light/moderate-vigorous 四个强度标签和手工特征，没有本项目需要的细粒度进食标签与原始 `400×3` 窗口，因此不拿它替代真实训练来源，也不复制其论文指标 |
| [OxWearables/pyfew](https://github.com/OxWearables/pyfew) | `21acc0ddd53dace211ab3a3bdea1d5d2586c147f` | MIT；未归档；远程 HEAD 较旧 | 轻量腕部加速度特征抽取的可复现接口 | 不把旧项目当作当前最佳模型，也不直接引入未验证特征 |

## 本阶段实际采用

1. `data_sources` 与 `cases` 分离，来源固定版本、许可状态、是否允许再分发和核验时间单独保存；这借鉴了 Open mHealth/RADAR-base 的可追溯思想，但字段由本项目真实性合同决定。
2. Pydantic 生成 OpenAPI 和独立领域 JSON Schema；Vue 端通过固定版本的生成器产出 TypeScript 类型，避免前后端手写字段漂移。
3. 回放按 `session → ordered event → sensor window / model output / alert candidate` 分层；事件只表示候选和证据，不代表真实救援结论。
4. 三模型各自保存输出，数据库没有综合医学风险字段或聚合表。
5. 固定 WEDA-FALL 来源在本机导入 100 个案例；原始与处理数组均留在 Git 忽略目录，只提交哈希与合同。
6. 用户自有跌倒 ONNX 已按来源提交与 SHA-256 接入；100 案例重放结果只作为同源行为核验。
7. CAPTURE-24 数据使用论文与 ORA DOI 作为 CC BY 4.0 许可依据；官方 6.90 GB 下载因服务器连接中断，只从本机前缀恢复 48 个完整参与者成员并逐一核验解压长度和 CRC-32，绝不描述为完整 151 人包。本项目独立实现读取、低通降采样、参与者分组与 NumPy/ONNX 训练，不复制学术许可工具代码。
8. 对 Open Wearables 仅吸收“来源适配器与统一合同”思路；当前阶段保持完全本地、无需账号、无厂商云连接，避免把未来真实设备范围混进已完成演示。

## 当前许可结论

- 架构参考不等于复制代码；当前新增的跌倒权重来自用户自己的固定模型仓库，不是把外部开源项目权重冒充为本项目成果。
- WEDA-FALL 许可仍未核验，因此不重新上传其原始或处理数据。CAPTURE-24 数据许可已由数据论文明确核验为 CC BY 4.0；训练目录将保存 DOI、归因文本、恢复前缀子集目录与 SHA-256、实际参与者清单和处理配置，不把恢复 ZIP 称为完整压缩包。
- FARSEEING 属于申请访问资料，且官方页面说明研究者需提出申请；本项目不会在未获用户本人申请与许可前下载或声称使用其真实跌倒数据。
