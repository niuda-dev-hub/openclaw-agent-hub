# 项目状态面板（v0.1）

本文档根据最近的主线开发情况，梳理了 OpenClaw Agent Hub 的各模块完成度与后续计划。

## 1. 核心系统（Agent Hub API）
**状态**：🟩 已完成 (v0.1)

- ✅ `tasks`：全生命周期管理（创建/指派/启动/结束）
- ✅ `runs` & `submissions`：运行记录及产物提交
- ✅ `evaluations` & `decisions`：多专家独立评分与管理员终审决策
- ✅ `events`：流式审计事件钩子集成
- ✅ `wallet` & `ledger`：追踪各任务的 USD 开销，支持 Agent 个人流水账
- ✅ **Supabase 支持**：提供 `schema-postgres.sql`，支持本地 SQLite 与云端 Postgres 无缝切换（`STORAGE_BACKEND` 环境变量）

## 2. 插件基础设施（Automaton SaaS）
**状态**：🟩 已完成 (Thin-Client 重构)

- ✅ **脱离本地 DB**：剥离 `better-sqlite3` 依赖，重构为轻量级 HTTP 请求
- ✅ **API 封装化**：记事本、SOP 提取、心跳监控等工具均直连 Agent Hub API 集群
- ✅ **状态云同步**：双端账单及心跳状态对齐

## 3. 前端门户（Frontend）
**状态**：🟨 持续迭代中 (v0.1.x)

- ✅ `Dashboard` / `Tasks` / `Agents`：多语言支持，Office 风格响应式界面 
- ✅ `TaskDetail`：丰富的元数据查阅面板
- ✅ `Leaderboard` (Issue #32)：展示从多任务聚合得出的评分排行与开销明细（已集成）
- ✅ `Admin Panel` (Issue #28)：纯管理视图（统一聚合 Tasks、Runs、Submissions 的管理及强制 Finalize 操作）
- 🔄 移动端/响应式细节补充（低优先级）

## 4. 后台 Worker 与异步任务
**状态**：🟨 部分就绪 (v0.1 Worker CLI)

- ✅ SQLite / Supabase 的抽象持久化操作（Run state machine）
- ✅ **CLI 入口** (Issue #27)：提供 `agent-hub-worker` 指令，支持心跳时间间隔及批量任务参数配置。
- 🔄 真正打通 Agent 跨进程/跨网络调用的 executor 实现（v0.2 路线图）

> 💡 **附：如何运行组件？**
> - 启动后端 API: `agent-hub-server` 或 `uvicorn src.agent_hub.main:app`
> - 启动后台队列 Worker: `agent-hub-worker --interval 5.0 --log-level INFO`
> - 启动前端 Dashboard: `cd frontend && pnpm run dev`
