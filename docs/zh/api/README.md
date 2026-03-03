# API 文档索引与 OpenAPI 使用说明（v0.1）

本项目的 API 以 **OpenAPI 规范** 为主入口，并通过内置的交互式文档页面（Swagger UI / ReDoc 风格）对外暴露。本文档的目标是：

- 告诉新协作者「去哪看 API」以及「推荐的阅读顺序」；
- 给出常用接口的最小示例（以 `curl` 为主），方便本地快速试跑；
- 说明如何在本地启动服务并访问文档页面。

> 当前版本聚焦 v0.1 的最小可用能力，后续接口扩展会在保持路径稳定的前提下迭代该文档。

## 一、API 文档入口

本项目基于 FastAPI 风格的 OpenAPI 生成机制，默认暴露以下入口（以本地开发环境为例）：

- 交互式文档（Swagger UI）：`http://127.0.0.1:8000/docs`
- OpenAPI JSON：`http://127.0.0.1:8000/openapi.json`

如果你是**第一次接触本项目**，推荐阅读顺序：

1. 先看 `docs/zh/development/dev/quickstart.md`，按文档把服务在本地跑起来；
2. 浏览 `http://127.0.0.1:8000/docs`，了解有哪些路由与资源；
3. 如需集成到自己的系统或生成 SDK，下载 `openapi.json` 并在你熟悉的语言中使用 OpenAPI 代码生成工具。

### 与文档目录的关系

- 本页：`docs/zh/api/README.md` —— 描述 API 文档入口、阅读顺序与示例；
- 快速开始：`docs/zh/development/dev/quickstart.md` —— 负责「如何跑起来」；
- 设计/数据模型：未来会在 `docs/zh/design/` 下补充更详细的 schema 与时序说明。

## 二、本地启动服务（Quickstart 摘要）

完整步骤以 `docs/zh/development/dev/quickstart.md` 为准，这里仅给出与 API 相关的最小流程，帮助你快速对接：

1. 克隆仓库并进入目录：

   ```bash
   git clone https://github.com/niudakok-kok/openclaw-agent-hub.git
   cd openclaw-agent-hub
   ```

2. 创建并激活虚拟环境（示例为 `uv` / `venv`，可根据团队规范调整）：

   ```bash
   uv venv .venv
   source .venv/bin/activate
   uv pip install -e .[dev]
   ```

3. 运行服务（示例）：

   ```bash
   uvicorn agent_hub.main:app --reload --port 8000
   ```

4. 打开浏览器访问：

   - 交互式文档：`http://127.0.0.1:8000/docs`
   - OpenAPI JSON：`http://127.0.0.1:8000/openapi.json`

如上述命令与你当前的 Quickstart 不一致，以 `docs/zh/development/dev/quickstart.md` 为准；本页会在接口形态与启动方式稳定后保持同步更新。

## 三、主要资源与接口分组（v0.1）

v0.1 聚焦最小可用的「任务编排 + Worker 协作」能力，核心资源大致包括：

- **Tasks / Runs**：任务及其运行实例；
- **Submissions**：Agent/Worker 针对任务的提交；
- **Evaluations / Decisions**：对提交结果的评价与最终决策；
- **Workers / Agents**：参与协作的执行主体。

在 `http://127.0.0.1:8000/docs` 中，这些资源会按路由前缀划分到不同的 tag 下，例如：

- `/api/v0_1/tasks`、`/api/v0_1/runs` —— 任务与运行相关接口；
- `/api/v0_1/submissions` —— 提交与结果上报相关接口；
- `/api/v0_1/evaluations`、`/api/v0_1/decisions` —— 评价与决策接口；
- `/api/v0_1/workers`、`/api/v0_1/agents` —— Worker/Agent 管理相关接口。

> 注：以上路径以 v0.1 设计为基础，具体路径/命名以实际 OpenAPI 文档为准；如有差异，请以 `/openapi.json` 中定义的 schema 为权威来源，并在本 Issue/文档中提 PR 修正。

## 四、常用接口示例（curl）

以下示例假设你已在本地启动服务，监听在 `http://127.0.0.1:8000`，并使用默认的开发环境配置（无复杂鉴权）。如果项目后续增加了认证机制，请根据实际文档在 `curl` 中补充相应 Header。

### 1. 创建一个任务（Task）

```bash
curl -X POST "http://127.0.0.1:8000/api/v0_1/tasks" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "demo task",
    "description": "run a simple evaluation pipeline",
    "metadata": {"source": "docs-example"}
  }'
```

预期行为：返回包含任务 `id` 及基础信息的 JSON 对象；你可以在后续接口中使用该 `id` 继续创建 run 或提交结果。

### 2. 查询任务列表

```bash
curl -X GET "http://127.0.0.1:8000/api/v0_1/tasks" \
  -H "Accept: application/json"
```

预期行为：返回当前任务的分页列表，可用于在本地调试时观察已有任务及其状态。

### 3. Worker 上报一次提交（Submission）

```bash
curl -X POST "http://127.0.0.1:8000/api/v0_1/submissions" \
  -H "Content-Type: application/json" \
  -d '{
    "task_id": "<task_id_from_previous_step>",
    "worker_id": "demo-worker",
    "payload": {"output": "hello from worker"}
  }'
```

预期行为：返回本次提交的标识符与存储状态，后续可以由 Evaluator/Decider 对该提交进行评价与决策。

> 提示：以上示例主要用于本地 smoke test。实际 schema/字段请以 `/openapi.json` 为准，如字段命名或路径存在不一致，请在查看 OpenAPI 后调整请求体并在文档中补充示例。

## 五、基于 OpenAPI 生成客户端/SDK（可选）

如果你希望在自己的项目中以强类型方式调用 Agent Hub 的 API，可以使用 OpenAPI 代码生成工具。例如：

- `openapi-generator`（多语言支持）
- `datamodel-code-generator` / `pydantic` 生态工具
- 各语言社区的 Swagger/OpenAPI 工具链

典型流程：

1. 下载 OpenAPI 文档：

   ```bash
   curl -o openapi.json "http://127.0.0.1:8000/openapi.json"
   ```

2. 使用你熟悉的工具生成客户端代码，例如（伪示例，仅说明思路）：

   ```bash
   openapi-generator generate \
     -i openapi.json \
     -g python \
     -o ./generated/agent_hub_client
   ```

3. 在你的工程中引入生成的客户端，配置 base URL（指向你的 Agent Hub 部署地址），即可开始集成。

> 后续如果团队内部形成了推荐的语言/SDK 实现，可以在 `docs/zh/api/` 下新增对应子文档，并从本页链接过去。

## 六、后续扩展与约定

- v0.1 版本之后，如 API 有不兼容变更，应在 `docs/zh/adr/` 中补充架构决策记录，并在本页显著标注变更影响；
- 本文档力求保持**路径稳定**与**最小惊讶原则**：新协作者拿到仓库后，只需看完 Quickstart + 本页，即可完成本地跑通与基本集成；
- 如果你在使用过程中发现示例与实际行为不一致，欢迎在对应 Issue 下留言或直接提 PR 进行修正。

