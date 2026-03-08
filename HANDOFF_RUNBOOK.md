# Handoff Runbook

本文件面向新接手开发者，目标是在阅读后可独立推进开发。

## A. 30 分钟快速上手

1. 阅读顺序：
   - `README.md`
   - `PROJECT_OVERVIEW.md`
   - `VERSIONING.md`
   - `DEVELOPMENT_RECORDS.md`
2. 本地启动：
   - 后端：`uvicorn agent_hub.main:app --app-dir src --reload`
   - 前端：`cd frontend && npm install && npm run dev`

## B. 关键配置

- `AGENT_HUB_UI_PASSWORD`（强密码门禁）
- `AGENT_HUB_ADMIN_FUND_TOKEN`（fund 接口鉴权）
- `STORAGE_BACKEND` / `SUPABASE_URL` / `SUPABASE_KEY`

## C. 交付流程（强制）

1. 变更实现
2. 本地验证（测试/构建）
3. 更新 `docs/dev-records/YYYY-MM-DD-*.md`
4. 更新 `DEVELOPMENT_RECORDS.md` 索引
5. 提交 PR（按 PR 模板填完整）

## D. 常见风险点

- 仅改代码不改文档，导致移交断层
- 仅改后端不验证前端（或反之）
- 未更新 changelog/version 导致发版不可追溯
