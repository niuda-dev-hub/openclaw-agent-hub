# Project Overview (Handoff-Ready)

## 1. 项目定位

`openclaw-agent-hub` 是系统后端权威状态中心，负责：

- Task / Run / Submission / Evaluation / Decision 主流程
- Agent Automaton 状态（wallet / heartbeat / memory / soul）
- Web 管理界面后端 API

## 2. 系统边界

- 上游/配套仓库：`openclaw-automaton-lifecycle`（插件 thin client）
- 本仓库职责：状态持久化、API 一致性、安全边界

## 3. 关键目录

- `src/agent_hub/`：后端主代码
- `frontend/`：管理界面前端
- `docs/`：中文/英文文档
- `.github/workflows/`：CI 与发布流程

## 4. 运行与部署

- 本地开发：Python + Node 双进程
- 容器部署：`docker-compose.yml` 同时启动 backend + frontend

## 5. 版本与发布

- 版本策略：`VERSIONING.md`
- 变更日志：`CHANGELOG.md`
- Tag 发布：`.github/workflows/release.yml`

## 6. 可移交要求

任何功能改动必须同时更新：

1. 对应功能文档/README
2. `DEVELOPMENT_RECORDS.md` 索引
3. `docs/dev-records/` 详细记录
