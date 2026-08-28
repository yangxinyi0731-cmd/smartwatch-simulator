# FastAPI 本地后端

当前后端已经建立统一领域合同、SQLite 结构版本 3，并已从固定版本 WEDA-FALL 本机检出导入 100 个可追溯案例；仍不包含模型推理或真实设备通信。

## 已实现

- `GET /api/health`：返回后端、SQLite、结构版本和案例实数；
- `GET /api/contracts`：返回真实性、三模型输入输出和回放事件合同；
- `GET /api/cases`：返回服务端分页、筛选和排序后的只读案例目录；
- `WS /ws/system`：连接后立即发送状态，此后每 15 秒更新；
- SQLite 结构版本 3：来源、案例、传感器流、导入批次、原始文件哈希、质量记录、真实标签、manifest、回放事件和三模型独立输出；
- WEDA-FALL 确定性导入器：40 条年轻参与者受控模拟跌倒、30 条老人日常活动、30 条年轻人日常活动；
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
├─ scripts/           # 合同生成与 WEDA-FALL 导入命令
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

## SQLite 结构版本 3 的边界

结构版本 3 在版本 2 的基础上增加 `import_runs`、`case_import_runs`、`case_source_files`、`sensor_quality` 和 `ground_truth_events`。同一标识的等价导入可以安全重跑；只要哈希或元数据冲突，整批事务就会回滚。当前已写入 100 个案例，但没有写入任何模型输出；案例存在不表示模型能力已经接入。告警确认、批量测试和报告会在后续迁移中扩展。

导入命令必须指向保留 `.git` 元数据且 HEAD 为固定提交的本机 WEDA-FALL 检出：

```powershell
.\.venv\Scripts\python.exe -m backend.scripts.import_weda_cases `
  --raw-root 'D:\path\to\WEDA-FALL' `
  --database '.\backend\runtime\smartwatch.sqlite3'
```

导入器不修改来源仓库。传感器数组写入 `data/processed/` 并被 Git 忽略；可提交的目录只保存来源路径、SHA-256、处理合同、质量标记和标签。
