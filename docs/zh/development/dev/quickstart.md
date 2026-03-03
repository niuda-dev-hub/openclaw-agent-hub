# Quickstart（协作者 5 分钟上手）

> 目标：让新协作者在 5 分钟内完成：安装依赖 → 本地启动 → 跑通测试。

## 1. 环境要求
- Python：建议 3.11+
- OS：Linux/macOS/Windows 均可（SQLite 本地文件）

## 2. 获取代码
```bash
git clone https://github.com/niudakok-kok/openclaw-agent-hub.git
cd openclaw-agent-hub
```

## 3. 安装依赖
使用 pip（最简单）：
```bash
python -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -e .
```

> 说明：本项目使用 `pyproject.toml` 管理依赖。

## 4. 本地启动服务
```bash
uvicorn agent_hub.main:app --reload --host 0.0.0.0 --port 8011
```

健康检查：
- http://localhost:8011/health

## 5. 运行测试
```bash
pytest -q
```

## 6. 数据与 SQLite 文件位置
- 默认数据目录：运行时会在数据目录下创建 SQLite 文件
- 测试默认会使用临时目录（见 tests/conftest.py）

> 注意：不要把 `*.sqlite` / `*.db` 提交进仓库。

## 7. 常用命令清单
- 代码格式/静态检查：
  - （待引入）ruff / black
- 启动：`uvicorn agent_hub.main:app --reload --port 8011`
- 测试：`pytest -q`

## 8. 常见问题
### 8.1 端口被占用
把 `--port 8011` 改成其他端口。

### 8.2 ModuleNotFoundError: agent_hub
确认你在仓库根目录，且已执行：
```bash
pip install -e .
```
