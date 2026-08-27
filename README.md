# 老年人 AI 模拟智能手表

英文仓库名：`smartwatch-health-simulator`

这是一个只在电脑端运行的三模型模拟智能手表平台。它将逐步接入：

1. 腕部跌倒检测模型；
2. 个人用餐、午睡和散步规律异常模型；
3. 腕部走路、进食候选和睡眠/躺卧候选识别模型。

## 当前完成到哪里

已完成第 1 步：独立本地 Git 仓库、Vue 前端空壳、虚拟手表首页、项目范围、真实性声明、视觉规范和交互规范。

尚未开始：FastAPI、SQLite、WebSocket、数据下载、模型训练和模型接入。界面中这些部分必须显示“未连接”或“暂无数据”，不能展示随机数字冒充结果。

## 第 1 步本地查看

```powershell
cd frontend
npm install
npm run dev
```

浏览器访问终端显示的本地地址。当前只有静态前端，不需要后端。

Windows PowerShell 也可以从项目根目录直接运行：

```powershell
npm --prefix frontend run dev
```

第 1 步已实测通过前端生产构建、严格界面审计、1440 × 900 桌面窗口、375 × 812 窄窗口和键盘焦点检查。详细记录见 [TASK_STATE.md](TASK_STATE.md)。

## 真实性边界

请先阅读 [DATA_AND_MODEL_NOTICE.md](DATA_AND_MODEL_NOTICE.md)。任何模拟数据、受控活动、模拟跌倒和真实自由生活数据都必须在界面中分别标记。

## 开发状态

持续状态记录在 [TASK_STATE.md](TASK_STATE.md)。下一步只做前后端、数据库和实时连接，不提前训练模型。
