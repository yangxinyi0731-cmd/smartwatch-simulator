# 系统结构（统一合同与 SQLite 结构版本 2）

```text
Windows 浏览器中的 Vue 前端
       │
       ├─ GET /api/health ──────────────┐
       ├─ GET /api/contracts ───────────┤
       ├─ GET /api/cases ───────────────┤
       └─ WS /ws/system ────────────────┤
                                        ↓
                              FastAPI 本地服务
                                        │
                Pydantic 统一合同 ───────┤
                                        ↓
                             SQLite 结构版本 2
       ┌────────────────────────────────┼────────────────────────────┐
       ↓                                ↓                            ↓
来源与案例                       回放会话与有序事件               三模型独立输出
data_sources                     replay_sessions                  model_manifests
cases                            replay_events                    model_outputs
sensor_streams

模型适配器（尚未接入）
├─ 跌倒检测 ONNX
├─ 个人规律异常统计规则
└─ 腕部活动识别 ONNX
```

## 当前数据流

1. 前端加载后向同源 `/api/health` 发起真实健康检查；
2. Vite 开发服务器将 `/api` 转发到 `127.0.0.1:8000`；
3. FastAPI 读取 SQLite 的 `PRAGMA user_version` 和 `cases` 实际数量；
4. 健康检查成功后，前端连接同源 `/ws/system`；
5. WebSocket 立即发送一次状态，并每 15 秒发送新快照；
6. 前端断线后使用 1/2/5/10 秒有上限退避自动重试，旧请求会被取消或忽略；
7. `/api/contracts` 返回五种真实性类别、三模型固定输入输出职责和回放事件类型；
8. `/api/cases` 使用服务端分页与白名单排序；当前数据库仍为 0 个案例；
9. 传感器回放和模型事件表已建立，但没有数据就不发送随机波形或模型结果。

## HTTP 合同

### `GET /api/health`

返回：

- 服务名、版本和 `ready / degraded`；
- SQLite 的 `ready / unavailable` 和结构版本；
- 案例实数以及 `empty / available / unavailable`；
- WebSocket 路径；
- UTC 检查时间和不含内部堆栈的中文说明。

SQLite 正常时返回 HTTP 200；后端仍能响应但数据库不可用时返回 HTTP 503，并保留同一结构的降级响应。健康检查使用 `Cache-Control: no-store`；前端确认离线时清空旧快照，避免把上一次连接结果误认为当前状态。

### `GET /api/contracts`

返回合同版本 `1.0.0` 和以下稳定规则：

- 五种真实性类别；
- 跌倒模型 `50 Hz × 4 秒 × 6 轴 = 200×6`；
- 规律异常模型使用 100 天合成生活事件，事件类型为用餐、午睡和散步；
- 活动模型 `20 Hz × 20 秒 × 3 轴 = 400×3`；
- 回放状态、传感器窗口、三模型输出、告警候选和错误事件类型；
- 三模型不得合并成未经校准的医学风险分数。

### `GET /api/cases`

当前提供只读案例目录：

- 默认每页 20，可选范围 1–50；前端约定只展示 10/20/50；
- 支持案例 ID、标题、来源和活动标签搜索；
- 支持真实性类别、适用模型筛选；
- 排序字段只允许 `case_id / title / created_at`，方向只允许升序或降序；
- 过大页码会收敛到最后有效页；空库固定返回第 1 页、总页数 0；
- 查询参数始终绑定，不把用户输入拼进 SQL。

## SQLite 结构版本 2

### `data_sources`

保存数据集名称、来源 URL、固定版本、许可状态、许可依据、是否允许重新分发、核验时间和说明。`UNVERIFIED` 表示不能因为文件公开就假定可以商用或上传。

### `cases`

保存真实性类别、来源记录路径与哈希、匿名参与者 ID、年龄组、设备、佩戴位置、原始采样率、活动标签、真实存在的传感器类型、允许进入的模型和可复现处理命令。`DERIVED_PERTURBATION` 必须指向父案例。

### `sensor_streams`

保存流的采样率、通道、单位、样本数、时长、存储格式、仓库相对路径和内容哈希。数据库拒绝绝对路径和明显的父目录逃逸路径。大数组后续保存在经过哈希核验的 CSV/NPY/NPZ 文件中，不塞进 SQLite 单元格。

### `model_manifests`

每个模型版本保存类型、格式、源提交、模型文件哈希、输入输出合同、训练来源、评估引用、限制、外部验证状态和部署审批。数据库和 Pydantic 均拒绝“未完成外部验证但已通过部署审批”的组合。

### `replay_sessions` 与 `replay_events`

回放会话使用客户端请求 ID 防止重复创建；状态只允许已创建、运行、暂停、完成、失败和重置。有序事件按 `(session_id, sequence)` 唯一，事件负载必须是合法 JSON。

### `model_outputs`

每条输出保留模型 manifest、案例、会话、输入窗口、时间边界和完整 JSON。没有综合风险列；三个模型的语义分别保存。

## 迁移与生成物

- 新数据库依次应用结构版本 1 和 2；
- 真实存在的结构版本 1 案例会被保留，但缺失信息明确迁移为 `UNKNOWN / UNVERIFIED / legacy-unrecorded`，不会编造设备、许可或处理命令；
- 发现高于程序支持版本的数据库时拒绝自动降级；
- `backend/app/contracts.py` 是领域合同代码源；
- `docs/contracts/domain-contract.schema.json` 是案例、窗口、manifest、三模型输出和回放事件的 JSON Schema；
- `docs/contracts/openapi.json` 是 HTTP OpenAPI 快照；
- `frontend/src/api/generated/` 从 OpenAPI 自动生成，禁止手工修改。

重新生成：

```powershell
.\.venv\Scripts\python.exe -m backend.scripts.export_contracts
npm --prefix frontend run generate:api
```

## 本地边界

- 默认数据库：`backend/runtime/smartwatch.sqlite3`，不进入 Git；
- 可用 `SMARTWATCH_DATABASE_PATH` 指定绝对路径；
- Uvicorn 只监听 `127.0.0.1`；
- 当前无账号、权限、局域网服务或互联网发布；
- 当前仍无模型推理和真实设备流，WebSocket 只发送系统状态；
- GitHub 远程仓库仍未配置，本阶段只有公开资料检索，没有发布项目。
