# FastAPI 本地后端

当前后端已经建立统一领域合同和 SQLite 结构版本 2，但仍不包含模型推理、案例导入或真实设备通信。

## 已实现

- `GET /api/health`：返回后端、SQLite、结构版本和案例实数；
- `GET /api/contracts`：返回真实性、三模型输入输出和回放事件合同；
- `GET /api/cases`：返回服务端分页、筛选和排序后的只读案例目录；
- `WS /ws/system`：连接后立即发送状态，此后每 15 秒更新；
- SQLite 结构版本 2：来源、案例、传感器流、manifest、回放事件和三模型独立输出；
- Pydantic 合同导出为 OpenAPI、JSON Schema 和前端 TypeScript 类型；
- 数据库版本保护：发现比程序更新的结构时拒绝自动降级；
- 自动测试：健康检查、WebSocket 和结构版本保护。

响应不会暴露本机数据库路径或原始异常堆栈。数据库不可用时，接口返回可读的降级状态，而不是伪装为正常。

## 目录

```text
backend/
├─ app/
│  ├─ config.py       # 本地数据库路径配置
│  ├─ contracts.py    # 统一领域合同与真实性硬约束
│  ├─ database.py     # SQLite 迁移、状态快照和案例分页
│  ├─ main.py         # FastAPI、HTTP 与 WebSocket
│  └─ schemas.py      # 对外状态结构
├─ scripts/           # OpenAPI 与领域 JSON Schema 生成
├─ runtime/           # 默认运行时数据库目录，数据库文件不提交
├─ tests/             # 后端自动测试
├─ requirements.txt
├─ requirements-dev.txt
└─ requirements-lock.txt
```

## 运行和测试

请始终从项目根目录执行：

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
.\.venv\Scripts\python.exe -m pytest .\backend\tests -q
.\.venv\Scripts\python.exe -m backend.scripts.export_contracts
```

后端明确绑定 `127.0.0.1`，避免在没有认证和发布安全设计的情况下暴露到局域网。

## SQLite 结构版本 2 的边界

结构版本 2 已固定来源、案例、传感器、manifest、回放会话、有序事件和三个模型独立输出的保存边界。当前不会写入任何案例或模型结果；这些空表是后续导入和推理的受控入口，不表示能力已经接入。告警确认、批量测试和报告会在后续迁移中扩展。
