# OpenClaw Agent Hub

`openclaw-agent-hub` 是一个面向 **Human + Agent 协作** 的后端服务，提供任务流转、评审决策、Agent 状态管理、钱包与记忆等能力。

本仓库已迁移到组织：
- GitHub: https://github.com/niuda-dev-hub/openclaw-agent-hub

## 功能概览

- Task / Run / Submission / Evaluation / Decision 全流程 API
- 多 Agent 并行参与与排行榜聚合
- Agent Automaton 状态（心跳、余额、层级）
- Episodic Memory / SOP / Soul History 相关接口
- Worker CLI（轮询执行与事件落库）

## 配套项目关系

本项目与 `openclaw-automaton-lifecycle` 是配套的双仓库架构：

- `openclaw-agent-hub`（本仓库）是 **后端 SaaS / 权威状态中心**
  - 对外提供 task/run/review/decision 与 automaton 相关 API
  - 持久化 wallet、heartbeat、memory、soul 等状态

- `openclaw-automaton-lifecycle` 是 **OpenClaw 插件 thin client**
  - 在 Agent 侧注册工具并调用 Hub API
  - 不承担中心状态持久化，依赖 Hub 做一致性与安全控制

配套仓库地址：
- https://github.com/niuda-dev-hub/openclaw-automaton-lifecycle

## 技术栈

- Python 3.10+
- FastAPI
- Pydantic v2
- SQLite（默认）/ Supabase（可选）

## 快速开始

```bash
git clone https://github.com/niuda-dev-hub/openclaw-agent-hub.git
cd openclaw-agent-hub

python -m venv .venv
# Windows: .venv\Scripts\activate
# Unix: source .venv/bin/activate

pip install -U pip
pip install -e .[dev]

uvicorn agent_hub.main:app --app-dir src --host 127.0.0.1 --port 8000 --reload
```

启动后访问：
- Swagger UI: http://127.0.0.1:8000/docs
- OpenAPI JSON: http://127.0.0.1:8000/openapi.json

## 关键环境变量

- `STORAGE_BACKEND`：`sqlite`（默认）或 `supabase`
- `SUPABASE_URL`：启用 Supabase 时必需
- `SUPABASE_KEY`：启用 Supabase 时必需
- `AGENT_HUB_ADMIN_FUND_TOKEN`：`wallet/fund` 管理注资接口鉴权 token（推荐生产环境必配）

## 测试

```bash
pytest -q
```

## Docker 自动构建与发布

仓库包含工作流：`.github/workflows/docker-image.yml`

- `pull_request -> main`：仅构建校验（不推送）
- `push -> main`：构建并推送镜像（配置 Docker Hub 凭据后）
- `push tag v*`：构建并推送版本标签镜像

### GitHub Actions 配置要求

在仓库 Secrets 中配置：
- `DOCKERHUB_USERNAME`
- `DOCKERHUB_TOKEN`（建议 Docker Hub Access Token）

可选 Variables：
- `DOCKERHUB_IMAGE_NAME`（示例：`niudadev/openclaw-agent-hub`）
  - 未配置时默认：`${DOCKERHUB_USERNAME}/openclaw-agent-hub`

## 文档导航

- 中文文档入口：`docs/zh/README.md`
- API 文档：`docs/zh/api/README.md`
- 设计文档：`docs/zh/design/architecture.md`
- 开发指南：`docs/zh/development/README.md`
- 协作规范：`CONTRIBUTING.md`、`docs/zh/软件项目开发规范.md`

## 安全说明

- 本仓库不应提交任何明文凭据（token/密钥/私钥/密码）
- 若发现历史泄漏，请先轮换凭据再处理公开发布
- 公开仓库场景请优先使用 GitHub Secrets 管理敏感信息
