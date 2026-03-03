# 新协作者 / 新 Agent Onboarding（入场流程）

> 目标：新人加入后 10 分钟内完成：能力画像登记 → 角色确认 → 权限最小化 → 领取第一批任务。

## 1. 入场前置（必须）
1) 阅读：README、CONTRIBUTING、v0.1 规格
2) 认领一个 Issue（或由项目主管分配）
3) 完成《协作者能力画像登记表》（见 agents-registry.md）并提交 PR

## 2. 需要登记的内容（强制）
- 协作者类型：Human / Agent
- Agent 运行平台：openclaw / cloud_code / antigravity / 其他
- 服务器能力画像：CPU/内存/磁盘/GPU、OS、Python/Node 版本
- 能力标签：exec/browser/docker/vision/feishu 等
- 网络环境：地区、是否需要代理（不写代理地址）
- 擅长方向：API/Worker/Docs/Review/UI

## 3. 敏感信息（禁止提交到仓库）
- Token/密码/私钥/公网 IP/内网拓扑/代理地址
- 如确需提供：仅通过私密渠道交付，并在文档中用 `secret_ref` 占位。

## 4. 角色与分工（由项目主管分配）
- API/后端
- Worker/调度
- 审核/评测
- 文档/规范
- 前端

## 5. 推荐插件/技能（按角色建议安装）
> 由项目主管根据协作者平台与能力画像指定。

- API/后端：pytest、ruff/black、sqlite 工具
- Worker：队列/重试工具（后续定）、系统监控工具
- 文档：markdown lint、OpenAPI 生成工具（后续定）

