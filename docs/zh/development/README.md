# 开发（Development）指南

本文档汇集了本地开发与调试 `openclaw-agent-hub` 相关的常见操作与文档指引。

## 本地极速启动 (Local Quickstart)

如果你刚刚克隆了该项目并希望直接在本地分别拉起前后端观察实际运行效果，不需要复杂的 Docker 配置。请确保你有 `uv` 和 `Node.js (npm)`。

### 1. 启动后端 (API 服务)
后端负责管理心跳、钱包和记忆，并对前端提供数据接口。

```bash
# 进入后台目录（通常即项目根目录下的 src/ 或直接在项目根目录使用 --app 启动）
# 推荐先建立虚拟环境
uv venv .venv
# Windows : .venv\Scripts\activate | Unix: source .venv/bin/activate
uv pip install -e .[dev]

# 启动服务并在 8000 端口提供监控 (默认使用本地 SQLite)
cd src
uvicorn agent_hub.main:app --host 127.0.0.1 --port 8000 --reload
```
后端服务现已拉起。你可以访问 [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) 观察 Swagger UI。

### 2. 启动前端 (Admin UI)
前端为基于 React + Vite 构建的全景 Agent 仪表盘。

```bash
# 开启一个新的终端进程进入前端目录
cd frontend

# 安装依赖
npm install

# 启动 Vite 的本地开发服务器
npm run dev
```
按照终端提示，通常会在 [http://127.0.0.1:5173/](http://127.0.0.1:5173/) 为您服务网络页面。由于后端运行在 `:8000` 端口上，请确保您的 `.env` 或 `vite.config.ts` 中的代理端口与您的 uvicorn 端口完全吻合。

## 目录索引
具体的设计原理或其他更复杂的部署指南请参考：
- [系统架构与数据模型概述](../design/architecture.md)
- [API 文档与快速调试说明](../api/README.md)
- [架构决策记录](../adr/README.md)
