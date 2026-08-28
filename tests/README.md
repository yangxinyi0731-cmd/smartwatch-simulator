# 测试目录

当前自动测试位于 `backend/tests/`，覆盖健康检查、WebSocket 状态和 SQLite 结构版本保护。

```powershell
.\.venv\Scripts\python.exe -m pytest .\backend\tests -q
```

这里仍预留给后续跨模块测试。模型输入输出、案例格式、回放、前端端到端和完整回归测试尚未建立，不得把当前四个后端测试描述成系统级完整测试。
