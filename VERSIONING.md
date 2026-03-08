# Versioning Policy

本仓库与 `openclaw-automaton-lifecycle` 统一采用 **SemVer + Git Tag + CHANGELOG** 策略。

## 1. 版本语义（SemVer）

- `MAJOR`：不兼容变更（破坏 API/数据结构/部署方式）
- `MINOR`：向后兼容的新功能
- `PATCH`：向后兼容的问题修复

示例：`v0.1.0` → `v0.2.0` → `v0.2.1`

## 2. 单一版本源

- 后端版本以 `pyproject.toml` 的 `[project].version` 为准
- 发布 Tag 必须与版本一致（如 `v0.2.1`）

## 3. 提交规范

建议使用 Conventional Commits：

- `feat:` 新功能（通常触发 MINOR）
- `fix:` 修复（通常触发 PATCH）
- `docs:` 文档
- `chore:` 杂项/构建
- 带 `!` 或 `BREAKING CHANGE` 触发 MAJOR

## 4. 发版流程

1. 更新代码并通过测试
2. 更新 `CHANGELOG.md`（新增 Unreleased 内容并整理为新版本小节）
3. 更新 `pyproject.toml` 版本号
4. 合并到 `main`
5. 打 tag：`vX.Y.Z` 并 push
6. GitHub Actions 自动创建 Release（附 CHANGELOG 摘要）

## 5. 兼容性约束

- 任何 API 破坏性改动必须先在 `CHANGELOG.md` 显式标注
- Docker 镜像标签与 Git Tag 对齐，`main` 保留 `latest`
