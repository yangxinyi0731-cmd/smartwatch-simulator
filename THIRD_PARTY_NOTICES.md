# 第三方项目与技术参考登记

这份清单用于记录后续开发可能参考的开源项目，方便比赛答辩时说明“思路来自哪里”。

> 当前第 1 步只完成平台空壳，没有复制下列项目的代码，也没有把下列项目的模型权重当成本项目成果。

| 项目 | 用途参考 | 固定版本（Git 提交） | 许可证/使用边界 |
|---|---|---|---|
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
