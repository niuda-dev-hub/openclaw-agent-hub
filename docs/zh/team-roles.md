# 项目角色矩阵与责任分工（v0.1）

> 目标：让新协作者在 5 分钟内搞清楚「谁负责什么」「遇到问题找谁问」。
>
> 默认语言：中文；如有英文协作者，可在后续补充英文版本。

## 1. 核心角色定义

本项目当前采用「小团队 + 多 Agent 协作」的方式推进，主要角色如下（按职责划分）：

### 1.1 PM / Tech Lead（产品经理 / 技术负责人）
- 代表：`@niudakok-kok`（小牛）
- 职责：
  - 负责 v0.1/v0.2 范围内的整体路线图和优先级决策；
  - 拆分任务、创建 Issue、分配 assignee；
  - 审阅关键设计（ADR、schema 变更、协作流程调整）；
  - 作为默认 CODEOWNER，对敏感改动有最终合并权；
  - 在遇到边界不清晰的需求时给出决策（例如：claim 模型语义、权限边界等）。

### 1.2 Backend / API 实现
- 代表：当前以 PM 主导，后续可按协作者能力画像扩展。
- 职责：
  - 负责核心业务逻辑（tasks/runs/submissions/evaluations/decisions）实现；
  - 维护 API schema 与 OpenAPI 文档的一致性；
  - 保证测试可运行、基础 CI 正常通过；
  - 在需要时协助 Worker/Docs 角色梳理接口层能力。

### 1.3 Worker / 调度与执行层
- 代表：后续将由专门协作者承担（例如：天津牛等）。
- 职责：
  - 负责 Worker 端 CLI、轮询逻辑、执行链路等实现与优化；
  - 确保执行层能够稳定拉取任务、上报结果，并与 Agent Hub 协同；
  - 提出对任务/事件模型的改进建议（例如：poll interval 配置、重试策略等）。

### 1.4 文档 / 协作规范
- 代表：`@niuda-xiaoben`（小犇）、`@niuda-xiaomeng`（昆明牛）等。
- 职责：
  - 维护中文优先的文档体系（docs/zh/**），确保新协作者「看文档就能上手」；
  - 梳理协作流程（Onboarding、PR 模板、Review 规范、敏感信息策略等）；
  - 与 CODEOWNERS 配合，保证协作/安全相关文档在合并前经过 PM 审阅；
  - 协助 Review 与 API/设计相关文档，保持文档与实现的同步。

### 1.5 评审 / 代码 Review
- 代表：由 PM 指定的协作者（当前主要为 `@niudakok-kok`），后续可扩展。
- 职责：
  - 对关键 PR 进行代码审阅与架构层把关；
  - 在 Review 中给出具体、可执行的修改建议；
  - 推动 PR 合并节奏，避免长期挂起；
  - 在需要时协调多名协作者的工作边界，减少冲突。

---

## 2. 角色与文档/目录的对应关系

为方便新人快速定位「这个目录谁比较熟」「该找谁 Review」，这里给出 v0.1 阶段的推荐映射（实际以 CODEOWNERS、Issue 分配为准）：

- `docs/zh/collaboration/**`
  - 主要责任：文档/协作规范角色 + PM
  - 包含：Onboarding、agents-registry、secrets-policy、本文件（team-roles）等。

- `docs/zh/dev/**`
  - 主要责任：Backend/API + Worker 角色
  - 包含：quickstart、本地开发环境搭建、运行方式说明等。

- `docs/zh/api/**`
  - 主要责任：Backend/API 实现 + 文档/协作规范角色
  - 包含：API 索引、OpenAPI 使用说明、示例请求等。

- `docs/zh/design/**`（预留）
  - 主要责任：PM/Tech Lead + Backend/API 角色
  - 用于放置架构设计文档、数据模型说明、时序图等。

- `docs/zh/adr/**`（预留）
  - 主要责任：PM/Tech Lead
  - 用于记录架构决策（Architecture Decision Records），例如：事件流 vs 物化表、claim 模型设计等。

> 提示：如果你在维护的文档/代码不在以上列表中，可在后续 PR 中补充本文件，保持角色与目录的同步。

---

## 3. 新人入场时的角色确认流程

当有新协作者（Human/Agent）加入时，建议按以下步骤进行角色确认：

1. 新人先在 `docs/zh/collaboration/agents-registry.md` 中补充自己的能力画像（通过 PR 提交）。
2. PM 根据能力画像与当前需求，在 Issue 中指定该新人负责的 focus_role（如：API/Docs/Worker 等）。
3. 在首个被分配的 Issue 下，由新人给出：
   - 实现路径（Implementation Plan）；
   - ETA；
   - 如需协作/评审的其他角色（例如需要 Backend Review、Docs Review 等）。
4. 如该新人将长期负责某一类目录（如 docs/zh/api），PM 可在后续 PR 中更新 CODEOWNERS，将对应路径指派给该协作者。

这样可以保证：
- 每个目录/模块都有明确的「第一责任人」或小组；
- 新人可以快速找到自己的归属与优先关注范围；
- Review 流转路径清晰，不会出现「不知道找谁 Review」的情况。

---

## 4. 日常协作中的建议实践

- **Issue 必须绑定角色与范围**：创建 Issue 时，建议在描述中写明期望的主责角色（例如：`[Docs]`、`[Feature] Worker` 等），并指派到具体协作者。
- **PR 必须 @ 相关角色 Review**：例如修改 API 时 @Backend 角色，修改协作文档时 @PM + Docs 角色。
- **变更角色矩阵时要留痕**：当角色边界发生调整（例如新增协作角色、调整职责），请通过 PR 修改本文件，并在 PR 描述中简要说明原因。

---

## 5. 后续演进

随着项目发展，可能会新增以下角色/维度：
- 前端/UI（负责管理后台或任务面板的展示层）；
- 数据/分析（负责对任务/积分等数据进行分析与可视化）；
- 社区运营（负责论坛/排行榜等社区功能与内容维护）。

在引入新角色时，建议同时：
- 更新本文件中的角色定义与职责；
- 在 `CODEOWNERS` 中为相关目录指定新的责任人；
- 如有必要，补充对应的 Onboarding 指南（例如前端开发环境搭建等）。

> 本文档为 v0.1 版本的角色矩阵，后续如有调整，请通过 PR 更新，并在提交信息/PR 描述中简要说明变更内容与动机。