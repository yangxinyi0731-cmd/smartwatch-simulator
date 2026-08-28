# 第三方项目与技术参考登记

这份清单用于记录后续开发可能参考的开源项目，方便比赛答辩时说明“思路来自哪里”。

> 当前前端使用 Tabler 的官方 npm 样式包和 Vue 图标组件。下列模型与数据项目仍只作为路线参考，没有把其代码、权重或指标当成本项目成果。

| 项目 | 用途参考 | 固定版本（Git 提交） | 许可证/使用边界 |
|---|---|---|---|
| [tabler/tabler](https://github.com/tabler/tabler) / `@tabler/core` | 前端页面框架、基础视觉和布局 | npm `1.4.0`（精确锁定） | MIT；Copyright (c) 2018-2026 The Tabler Authors；许可证保存在 `licenses/TABLER_CORE_LICENSE.txt` |
| [tabler/tabler-icons](https://github.com/tabler/tabler-icons) / `@tabler/icons-vue` | Vue 3 线性图标组件 | npm `3.46.0`（精确锁定） | MIT；Copyright (c) 2020-2026 Paweł Kuna；许可证保存在 `licenses/TABLER_ICONS_LICENSE.txt` |
| [fastapi/fastapi](https://github.com/fastapi/fastapi) | 本地 HTTP 与 WebSocket 应用框架 | PyPI `0.141.1`（直接依赖精确锁定） | MIT；包元数据与上游仓库为准 |
| [encode/uvicorn](https://github.com/encode/uvicorn) | 只监听本机的 ASGI 开发服务器 | PyPI `0.52.4`（直接依赖精确锁定） | BSD-3-Clause；包元数据与上游仓库为准 |
| [pydantic/httpx2](https://github.com/pydantic/httpx2) | FastAPI/Starlette 测试客户端依赖 | PyPI `2.12.0`（开发依赖精确锁定） | BSD-3-Clause；只用于自动测试 |
| [pytest-dev/pytest](https://github.com/pytest-dev/pytest) | 后端自动测试 | PyPI `9.1.1`（开发依赖精确锁定） | MIT；只用于自动测试 |
| [hey-api/hey-api](https://github.com/hey-api/hey-api) / `@hey-api/openapi-ts` | 从后端 OpenAPI 生成 Vue 可用的 TypeScript 类型 | npm `0.99.0`（开发依赖精确锁定） | MIT；许可证保存在 `licenses/HEY_API_OPENAPI_TS_LICENSE.txt`；仅处理本仓库生成的 JSON，不处理不可信 YAML |
| [RADAR-base/RADAR-Kubernetes](https://github.com/RADAR-base/RADAR-Kubernetes) | 可穿戴数据采集、流、存储和监控分层参考 | `f1a6aab14ee103852af9dd400bd3b1456dc9c566` | Apache-2.0；仅参考架构，不引入 Kubernetes/Kafka 代码 |
| [openmhealth/schemas](https://github.com/openmhealth/schemas) | 来源、schema 版本和 acquisition provenance 字段参考 | `df386000a93a35c1d7f33a023f759e41202a7d3d` | Apache-2.0；不声称本项目完整兼容 Open mHealth/FHIR |
| [awareframework/aware-client](https://github.com/awareframework/aware-client) | 传感器采集、本地保存和同步职责分离参考 | `f77e873baaedfc649fd39ca8f3547f914c3e6b32` | Apache-2.0；当前不接入手机或真实设备代码 |
| [fastapi/full-stack-fastapi-template](https://github.com/fastapi/full-stack-fastapi-template) | OpenAPI 前端类型和端到端测试路线参考 | `2ccfa25845dec4c70b8a7b653ed347b2905240b6` | MIT；不复制 React、PostgreSQL、认证或部署结构 |
| [DevGurav/fall-detect-system](https://github.com/DevGurav/fall-detect-system) | 腕部跌倒、虚拟设备回放和事件流的相似项目参考 | `5879f92c5643f97a32302f4eb74b05a3fb07929a` | MIT；不采用其自报指标、目标阈值或数据许可结论 |
| [joaojtmarques/WEDA-FALL](https://github.com/joaojtmarques/WEDA-FALL) | 腕部 50 Hz 六轴案例来源与跌倒模型研究数据 | `74e0b93cb061d4ecbca12628f2d47090e97fbeea` | GitHub API 未识别到许可证；只允许本地研究核验，不默认允许再分发或商用；老人只执行 ADL |
| [OxWearables/capture24](https://github.com/OxWearables/capture24) | 可穿戴设备活动数据处理与标签组织 | `f861b44f5675cb3e8294cd3d560d7a71a749616f` | 学术研究项目；使用前需再次核对仓库的数据与许可说明 |
| [OxWearables/actinet](https://github.com/OxWearables/actinet) | 可穿戴活动识别模型路线 | `0f7848f31efb54079752e43e5b5a2efcac0c2b68` | 学术研究项目；不得把其指标直接写成本项目指标 |
| [OxWearables/ssl-wearables](https://github.com/OxWearables/ssl-wearables) | 可穿戴传感器自监督学习路线 | `150550ea5d41800229c95e36f88f5bf0d2e7cf04` | 学术研究项目；只作为路线参考 |
| [dapowan/LIMU-BERT-Public](https://github.com/dapowan/LIMU-BERT-Public) | IMU 时序预训练与下游分类 | `decffee7ecb4e2e5d7244b1a759cb80b752dc6c2` | MIT |
| [yolish/har-with-transformers](https://github.com/yolish/har-with-transformers) | Transformer 人体活动识别结构 | `28583242e2928d7a2c1314432cafbeba9651eb8a` | MIT |
| [guillaume-chevalier/LSTM-Human-Activity-Recognition](https://github.com/guillaume-chevalier/LSTM-Human-Activity-Recognition) | LSTM 活动识别基线 | `5864e44a4cde5f790e91c853b2f3725617ee649f` | MIT |

## 使用规则

1. 真正引入任何代码、模型或数据前，重新核验许可证、数据来源、参与者信息和引用要求。
2. 所有外部项目固定到具体提交，避免“最新版变化后无法复现”。
3. 外部项目的测试结果不能冒充本项目实测结果。
4. 若后续修改或分发第三方代码，在对应目录保留原许可证与版权声明。

## 当前实际引入方式

- `@tabler/core@1.4.0`：只在 `frontend/src/main.ts` 导入官方压缩 CSS；不加载 Tabler 演示站页面，也不启用当前页面不需要的 Tabler JavaScript 交互。
- `@tabler/icons-vue@3.46.0`：只按名称导入页面实际使用的 Vue 图标组件，未使用图标由构建工具移除。
- 精确版本同时写入 `frontend/package.json` 和 `frontend/package-lock.json`，避免比赛前自动升级。
- Tabler Core 依赖 Bootstrap `5.3.7` 与 Popper；依赖树及完整性校验由 npm 锁文件记录。
- FastAPI 与 Uvicorn 的直接依赖写入 `backend/requirements.txt`，测试依赖写入 `backend/requirements-dev.txt`。
- `backend/requirements-lock.txt` 保存 2026-08-28 在 Windows CPython 3.14 上实际解析和测试的完整 Python 环境版本；跨 Python 或跨平台安装仍需重新验证。
- `@hey-api/openapi-ts@0.99.0` 只用于从 `docs/contracts/openapi.json` 生成 `frontend/src/api/generated/`；该目录视为生成物，不手工修改。
- 上游生成器依赖的 `js-yaml` 被 npm `overrides` 固定为 `4.3.1`，用于避开截至 2026-08-28 npm audit 报告的旧版拒绝服务漏洞；本项目输入为本地生成的 JSON。
- 更完整的候选项目、最近推送时间、采用与排除理由见 `docs/OPEN_SOURCE_REFERENCE_REVIEW.md`。
