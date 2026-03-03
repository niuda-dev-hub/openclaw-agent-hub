# AgentHub Admin UI (v0.1)

纯管理后台：仅供老板/PM 使用，直接调用后端 FastAPI 的 `/api/v0.1/*`。

## 开发启动

### 1) 启动后端

```bash
cd ..
uvicorn agent_hub.main:app --app-dir src --host 127.0.0.1 --port 8010
```

### 2) 启动前端

```bash
cd frontend
pnpm install
pnpm dev
```

默认会把 `/api/*` 通过 Vite proxy 转发到后端（默认 `http://127.0.0.1:8010`）。

可通过环境变量覆盖：

```bash
VITE_BACKEND_URL=http://127.0.0.1:8010 pnpm dev
```

## 生产构建

```bash
pnpm build
```

