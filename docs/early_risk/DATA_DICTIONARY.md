# 提前风险研究数据字典（P1 v1）

## 1. 分层与不可变性

| 层 | 代码 | 规则 |
|---|---|---|
| 原始不可变层 | `RAW_IMMUTABLE` | 保存来源哈希与安全相对路径；`raw_immutable=true`；不能有父派生段 |
| 规范化派生层 | `NORMALIZED_DERIVED` | 必须指向父原始段；`raw_immutable=false`；处理命令与版本由外部 manifest 记录 |

原始采集压缩包、视频、设备信息、绝对采集时间、个人映射和运行数据库不进入 Git。当前分支除确定性小夹具外，新增 `data/cases/self_collected_p01/` 下 30 组去标识化六轴标准文件，用于复现 P01 工程验证；这些文件只保留相对时间和六轴数值，不包含可直接识别个人的信息。

## 2. 标识符

| 字段 | 含义 | 强制规则 |
|---|---|---|
| `participant_id` | 去标识化参与者 | 不能使用姓名、电话、身份证或可直接识别值 |
| `site_id` | 采集机构/地点 | 与参与者拆分共同审计 |
| `device_id` | 去标识化设备实例 | 换设备必须生成新实例或保存明确映射 |
| `session_id` | 一次连续记录会话 | 不能跨参与者或设备混合 |
| `segment_id` | 传感器段 | 仓库内唯一 |
| `event_id` | 裁决事件 | 仓库内唯一 |
| `withdrawal_locator` | 撤回索引 | 只引用受控映射，不保存直接身份 |

`ResearchRecordBundle` 会拒绝参与者、地点、设备或会话混淆，也拒绝事件标签与传感器段身份不一致。

## 3. 设备与传感器配置

`SensorProfile` 必填：

- 配置 ID、设备型号、佩戴侧、时区和标定版本；
- 名义采样率；
- 通道顺序、物理量和单位；
- 三轴加速度必须是 `ax/ay/az` 与 `m/s^2`；
- 六轴 IMU 必须是 `ax/ay/az/gx/gy/gz`，加速度为 `m/s^2`，角速度为 `rad/s`。

缺少陀螺仪的三轴数据不能补零冒充六轴。P1 夹具配置保存在 `configs/early_risk/sensor_profiles/`，只用于合同验证，不代表真实设备已经接入。

## 4. 采样记录

每个 `SensorSample` 包含：

- 从 0 开始连续的 `sequence`；
- `utc_timestamp_ns`；
- `monotonic_timestamp_ns`；
- 与配置通道数完全相同的有限数值数组。

UTC 与单调时间都必须严格递增。乱序、重复时间戳、错误列数、NaN、Infinity、错误单位和路径逃逸全部拒绝。

## 5. 质量与同步

`QualityAssessment` 保存：

- 缺失样本比例；
- 重复时间戳数；
- 乱序数；
- 设备—标签同步误差；
- 时钟漂移；
- 质量标记；
- 是否允许进入数秒级研究。

数秒级工程 Gate 要求重复数和乱序数均为 0，同步误差与时钟漂移均不超过 100 ms。未通过者可以在未来原始受控存储中保留，但当前 `ResearchRecordBundle` 会拒绝把它加入数秒级研究包。

## 6. 事件标签

`EventAnnotation` 必填参与者、地点、设备、会话、事件类型、`t_instability`、`t_recovery_or_assist`、标签来源、至少两名不同裁决者、置信等级、同步误差和说明。`t_impact` 按事件类型可选；近跌倒和失稳明确禁止填入撞击锚点。

## 7. 撤回、删除与访问边界

`WithdrawalIndexEntry` 只保存去标识化 locator、参与者 ID、段/事件 ID 和受控映射引用，访问范围固定为 `DATA_CONTROLLER_ONLY`。真实直接身份映射、同意书和删除凭证不得进入 Git 或普通研究包。

当前实现只是合同，不代表数据控制者、保留期、密钥、访问角色或删除流程已经获得机构批准；这些属于 P3 外部 Gate。

## 8. JSON Schema

代码源：`research/early_risk/contracts.py`

生成物：`docs/contracts/early-risk-domain.schema.json`

生成或检查：

```powershell
.\.venv\Scripts\python.exe -m research.early_risk.export_contracts
.\.venv\Scripts\python.exe -m research.early_risk.export_contracts --check
```
