# 敏感信息与公开前清理规范（Secrets & Public Release Policy）

> 默认语言：中文。此项目未来可能公开，因此必须从第一天开始执行“敏感信息不入库”。

## 1) 什么信息禁止进入仓库（MUST NOT）
以下内容 **禁止** 出现在仓库中的任何位置（代码、docs、Issue、PR、commit message、日志、截图等）：
- Token / 密码 / 私钥 / Cookie / Session
- 真实公网 IP、内网拓扑、端口映射细节
- 代理地址、VPN/组网的可访问入口
- 任何可直接用于入侵/登录的信息

## 2) 允许进入仓库的“能力画像”（OK）
允许登记但必须脱敏：
- 机器能力（CPU/内存/GPU/OS/版本）
- 能力标签（exec/browser/docker/vision/feishu 等）
- 网络环境抽象信息（region、是否需要代理 yes/no）

## 3) Private Registry（本地私密登记表）
- 私密信息统一记录在 **本地文件**：
  - `~/.openclaw/workspace/private/agent-hub-private-registry.md`
- 该文件 **不属于仓库**，也不允许复制到仓库。

### secret_ref 约定
涉及凭据时，优先使用 `secret_ref`（引用）而不是明文：
- `vault:ssh/agent-001`
- `env:AGENT_001_SSH_PASSWORD`
- `file:/secure/path/to/key`

## 4) 仓库公开前清理 Checklist
公开仓库前必须执行：
1. 全局搜索：`token` `secret` `password` `proxy` `tailscale` `ssh` `ip` `cookie`
2. 检查 `.env` / `*.key` / `*.pem` / `*.sqlite` 是否被 gitignore
3. 检查 Issue/PR 评论是否含敏感信息（必要时删除/编辑）
4. 检查 Git 历史：如曾误提交敏感信息，必须 rewrite history（BFG / filter-repo）并轮换密钥

## 5) 责任与执行
- 项目主管负责把关（PR review + CODEOWNERS）。
- 任何协作者发现敏感信息泄露风险必须立即报告并阻止合并。
