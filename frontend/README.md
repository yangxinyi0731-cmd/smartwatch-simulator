# 前端说明

这是“守望台”电脑端可视化程序的 Vue 3 + TypeScript 前端。

前端会通过 `/api/health` 检查 FastAPI 和 SQLite，再通过 `/ws/system` 接收实时系统状态。Vite 会把这两个同源路径转发到 `127.0.0.1:8000`。

请先从项目根目录启动后端，再从同一根目录运行：

```powershell
npm --prefix frontend install
npm --prefix frontend run dev
```

生产构建检查：

```powershell
npm --prefix frontend run build
```

界面显示的案例数量来自 SQLite 实数。当前为 0；回放和三个模型仍没有数据。后端停止时，页面会显示未连接并自动重试，不会用静态成功状态掩盖故障。
