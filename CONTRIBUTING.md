# 贡献指南（CONTRIBUTING）

> 默认语言：中文。英文内容作为补充（见 docs/en）。

本文档为 **openclaw-agent-hub** 的协作开发规范，供人类开发者与 Agent 开发者共同遵守。

---

## 0. 总原则（必须遵守）

- **一切皆 Issue**：任何需求/缺陷/重构/疑问/决策，都必须先有 Issue。
- **主干永远可发布**：禁止直接 push main，必须走 PR。
- **可追溯**：关键决策写入 ADR，重要变更写入 docs/。
- **中文优先**：README 与核心文档以中文为主；英文为补充。

---

## 1. Issue 规范（强制）

### 1.1 何时需要 Issue
- 新功能（Feature）
- Bug 修复（Fix）
- 重构（Refactor）
- 文档（Docs）
- 决策（Decision/ADR）
- 问题（Question）

### 1.2 Issue 标题格式

```
[类型] 简短描述
```

类型限定：
- `[Feature]` `[Fix]` `[Refactor]` `[Docs]` `[Chore]` `[Question]` `[Decision]` `[Security]`

### 1.3 Issue 必备结构

```md
## 目标
一句话说明要达成什么

## 验收标准
- 用 bullet list 写清楚可验证的完成条件
- 写明非功能要求（性能/安全/兼容等）

## 相关链接
- （后续填写 PR 链接）
```

---

## 2. 分支规范（强制）

分支命名：

```
<type>/<short-desc>-<issue_id>
```

示例：
- `feat/task-claim-12`
- `fix/sqlite-migration-7`
- `docs/api-quickstart-5`

> 说明：issue_id 以 GitHub issue 编号为准。

---

## 3. Commit 规范（强制：Conventional Commits）

格式：

```
type(scope): subject
```

允许的 type：
- `feat` `fix` `refactor` `docs` `test` `chore` `style` `perf` `ci` `build`

scope 建议：
- `api` `db` `worker` `review` `ui` `docs` `infra`

示例：
- `feat(api): add task claim endpoint`
- `fix(db): handle missing meta table on first run`

---

## 4. PR 规范（强制）

### 4.1 PR 标题
PR 标题 = 第一条 commit 标题（必须符合 Conventional Commits）。

### 4.2 PR 描述模板（强制）

```md
Closes #<issue号>

## 变更说明
- 做了什么（简短 bullet）

## 测试情况
- 本地验证通过
- 单元测试：通过/不适用

## 风险点
- 无 / 说明风险与回滚方式
```

### 4.3 合并方式
- 使用 **Squash and merge**（保持线性历史）。
- PR 必须填写 `.github/pull_request_template.md`（仓库内置模板）。
- `docs/zh/collaboration/*` 相关变更建议由项目主管 review（见 CODEOWNERS）。

---

## 5. 文档与 ADR（强制）

### 5.1 文档目录
- `docs/zh`：中文主文档（默认）
- `docs/en`：英文补充文档
- `docs/adr`：架构决策记录（ADR）

### 5.2 何时需要 ADR
- 技术选型变更（例如 SQLite -> Postgres、raw sqlite -> SQLAlchemy）
- 安全策略/鉴权模型变更
- 数据模型重大调整

ADR 文件命名建议：
- `ADR-0001-xxx.md`

---

## 6. 测试与质量（强制最低要求）

- 新增/修改核心逻辑必须补测试
- 至少保证冒烟路径：create -> start -> submit -> evaluate -> decide
- `pytest -q` 必须本地通过

---

## 7. Agent 参与开发的额外约定

- Agent 必须把关键讨论放在 Issue/PR 评论中（不要只在聊天里说）
- Agent 生成的代码必须可运行、可测试、可复现
- 禁止把密钥/Token/真实 IP 等敏感信息写入仓库

---

## 8. Compliance Checklist（Agent 输出自检）

每次 Agent 完成一个开发动作（创建分支、提交 PR、合并等），需要自检：

- 已创建/关联 Issue：是/否/#号
- 分支命名符合规范：是/否
- Commit 符合 Conventional Commits：是/否
- PR 关联 Issue 并使用模板：是/否
- 本地测试通过：是/否
- docs/zh 更新：是/否/不适用
