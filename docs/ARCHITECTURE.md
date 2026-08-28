# 系统结构（最小本地数据闭环）

```text
Windows 浏览器中的 Vue 前端
       │
       ├─ GET /api/health ──────────────┐
       └─ WS /ws/system ────────────────┤
                                        ↓
                              FastAPI 本地服务
                                        │
                                        ↓
                             SQLite 结构版本 1
                              ├─ schema_migrations
                              └─ cases（当前 0 条）

模型适配器（尚未接入）
├─ 跌倒检测 ONNX
├─ 个人规律异常
└─ 腕部活动识别 ONNX
```

## 当前数据流

1. 前端加载后向同源 `/api/health` 发起真实健康检查；
2. Vite 开发服务器将 `/api` 转发到 `127.0.0.1:8000`；
3. FastAPI 读取 SQLite 的 `PRAGMA user_version` 和 `cases` 实际数量；
4. 健康检查成功后，前端连接同源 `/ws/system`；
5. WebSocket 立即发送一次状态，并每 15 秒发送新快照；
6. 前端断线后使用有上限的退避时间自动重试，旧请求会被取消或忽略；
7. 用户也可以使用顶部“刷新状态”手动重新检查。

## HTTP 状态合同

`GET /api/health` 返回：

- 服务名、版本和 `ready / degraded`；
- SQLite 的 `ready / unavailable` 和结构版本；
- 案例实数以及 `empty / available / unavailable`；
- WebSocket 路径；
- UTC 检查时间和不含内部堆栈的中文说明。

SQLite 正常时返回 HTTP 200；后端仍能响应但数据库不可用时返回 HTTP 503，并保留同一结构的降级响应。
健康检查使用 `Cache-Control: no-store`；前端确认离线时清空旧快照，避免把上一次连接结果误认为当前状态。

## SQLite 结构版本 1

- `schema_migrations` 记录已应用结构版本；
- `cases` 只建立案例身份和最低来源约束，当前为 0 条；
- `truth_category` 只允许项目真实性声明中的五类值；
- `source_sha256` 必须为 64 字符；
- 数据库启用外键、5 秒忙碌等待和 WAL 日志；
- 程序拒绝打开比自身更新的数据库，避免无提示降级破坏数据。

当前没有传感器、回放、模型、告警或报告表。完整案例和三模型输入输出 schema 属于下一大关。

## 本地边界

- 默认数据库：`backend/runtime/smartwatch.sqlite3`，不进入 Git；
- 可用 `SMARTWATCH_DATABASE_PATH` 指定绝对路径；
- Uvicorn 只监听 `127.0.0.1`；
- 当前无账号、权限、局域网服务或互联网发布；
- 当前无模型推理和真实设备流，WebSocket 只发送系统状态。
