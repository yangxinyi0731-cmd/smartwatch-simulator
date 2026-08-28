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
| [DevGurav/fall-detect-system](https://github.com/DevGurav/fall-detect-system) | `5879f92c5643f97a32302f4eb74b05a3fb07929a` | MIT；未归档；最近推送 2026-08-22 | 最相似的“腕部跌倒 + 虚拟设备回放 + 事件流”拆分，可作为回放边界检查清单 | 不复制其自报指标、目标阈值或数据许可结论；这些都不是本项目实测证据 |
| [joaojtmarques/WEDA-FALL](https://github.com/joaojtmarques/WEDA-FALL) | `74e0b93cb061d4ecbca12628f2d47090e97fbeea` | GitHub API 未识别到许可证；最近推送 2026-08-24 | 腕部 50 Hz 六轴来源、年轻模拟跌倒与老人 ADL 误报分析 | 原始数据不进本仓库，不默认允许再分发或商用；老人没有执行跌倒 |
| [OxWearables/capture24](https://github.com/OxWearables/capture24) | `f861b44f5675cb3e8294cd3d560d7a71a749616f` | GitHub API 返回 `NOASSERTION`；远程 HEAD 最近提交早于本次检索 | 参与者分组后切窗、腕部自由生活活动标签、活动识别基线 | 不把自由生活活动描述为真实老人跌倒；数据下载与再利用许可单独核验 |
| [OxWearables/pyfew](https://github.com/OxWearables/pyfew) | `21acc0ddd53dace211ab3a3bdea1d5d2586c147f` | MIT；未归档；远程 HEAD 较旧 | 轻量腕部加速度特征抽取的可复现接口 | 不把旧项目当作当前最佳模型，也不直接引入未验证特征 |

## 本阶段实际采用

1. `data_sources` 与 `cases` 分离，来源固定版本、许可状态、是否允许再分发和核验时间单独保存；这借鉴了 Open mHealth/RADAR-base 的可追溯思想，但字段由本项目真实性合同决定。
2. Pydantic 生成 OpenAPI 和独立领域 JSON Schema；Vue 端通过固定版本的生成器产出 TypeScript 类型，避免前后端手写字段漂移。
3. 回放按 `session → ordered event → sensor window / model output / alert candidate` 分层；事件只表示候选和证据，不代表真实救援结论。
4. 三模型各自保存输出，数据库没有综合医学风险字段或聚合表。

## 当前许可结论

- 架构参考不等于复制代码；本阶段除已登记的 npm/Python 依赖外，没有复制上述仓库源码、模型权重或数据。
- WEDA-FALL 与 CAPTURE-24 的“网页可访问”不构成重新上传许可。进入数据导入阶段前，仍需逐项保存数据下载页、引用要求、文件哈希和使用条件。
- FARSEEING 属于申请访问资料，且官方页面说明研究者需提出申请；本项目不会在未获用户本人申请与许可前下载或声称使用其真实跌倒数据。
