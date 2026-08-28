# Windows 一键运行

首次使用前，先按项目根目录 `README.md` 的“首次安装”完成 Python 与前端依赖安装。之后普通使用不需要输入命令。

## 三个可双击入口

- `start-smartwatch.cmd`：自动构建最新前端，启动只监听 `127.0.0.1:8000` 的本机服务，并用默认浏览器打开页面；
- `stop-smartwatch.cmd`：核对 PID、Python 路径和进程启动时间后，只停止本项目记录的进程；SQLite 和日志不会删除；
- `diagnose-smartwatch.cmd`：只读检查项目目录、Python、依赖、Node.js、前端构建、数据库、模型资产与健康接口。

## 运行文件

状态与日志保存在 `backend/runtime/local-delivery/`，该目录被 Git 忽略：

- `server-state.json`：当前进程标识、项目目录、数据库绝对路径和页面地址；
- `server.stdout.log`：服务标准输出；
- `server.stderr.log`：启动或运行错误。

启动脚本不会开放局域网端口，不会上传数据，也不会创建 GitHub 远程仓库。页面、API 与 WebSocket 都由同一个本机进程提供。
