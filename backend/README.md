# FastAPI 本地后端

当前后端只负责最小本地数据闭环，不包含模型推理、案例导入或真实设备通信。

## 已实现

- `GET /api/health`：返回后端、SQLite、结构版本和案例实数；
- `WS /ws/system`：连接后立即发送状态，此后每 15 秒更新；
- SQLite 结构版本 1：迁移记录和带来源约束的空 `cases` 表；
- 数据库版本保护：发现比程序更新的结构时拒绝自动降级；
- 自动测试：健康检查、WebSocket 和结构版本保护。

响应不会暴露本机数据库路径或原始异常堆栈。数据库不可用时，接口返回可读的降级状态，而不是伪装为正常。

## 目录

```text
backend/
├─ app/
│  ├─ config.py       # 本地数据库路径配置
│  ├─ database.py     # SQLite 初始化、结构版本和状态快照
│  ├─ main.py         # FastAPI、HTTP 与 WebSocket
│  └─ schemas.py      # 对外状态结构
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
```

后端明确绑定 `127.0.0.1`，避免在没有认证和发布安全设计的情况下暴露到局域网。

## SQLite 结构版本 1 的边界

`cases` 表只保存案例身份和最低限度的来源字段，并强制使用项目规定的真实性类别。当前不会写入任何案例。传感器窗口、模型输入输出、回放会话和报告结构必须在下一大关中另行定义、迁移和测试，不能把本表当作完整业务 schema。
