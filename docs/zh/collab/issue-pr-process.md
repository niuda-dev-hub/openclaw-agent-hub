# Issue/PR 流程（强制）

> 目的：保证可追溯、可审计、可回滚。主干永远可发布。

## 1. 一切皆 Issue
- 需求/bug/疑问/决策都必须有 Issue
- Issue 必须写清：目标、范围、验收标准、风险点（如有）

## 2. 分支命名
- 命名：`<type>/<short-desc>-<issue_id>`
- 示例：`feat/claim-api-40`

## 3. Commit 规范
- 使用 Conventional Commits：`type(scope): subject`
- 示例：`feat(api): add task claim endpoint`

## 4. PR（禁止直接 push main）
- PR 标题 = 第一条 commit 标题
- PR 描述必须包含：
  - `Closes #<issue>`
  - 变更说明（What/Why）
  - 测试情况（本地 `pytest -q` / 前端 build 等）
  - 风险与回滚方案（如有）
- 合并方式：Squash and merge

## 5. Agent Compliance Check（每个 PR 必填）
```
**Agent Compliance Check**
- 已创建/关联 Issue：是/否/#号
- 分支命名符合规范：是/否
- Commit 消息符合 Conventional Commits：是/否
- PR 有关联 Issue 并使用模板：是/否
- 本地测试通过：是/否
- 文档更新（docs/zh）：是/否/不适用
```
