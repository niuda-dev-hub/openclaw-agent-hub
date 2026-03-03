# 协作者/Agent 能力画像登记表（Registry）

> 默认语言：中文。所有加入项目的协作者（Human/Agent）必须在加入后尽快登记。
>
> ⚠️ 禁止在此文档提交任何密钥/Token/密码/真实公网 IP。

## 登记表（请追加一行）

| name | github_username | actor_type | platform | focus_role | capabilities | server_profile | network_profile | notes |
|---|---|---|---|---|---|---|---|---|
| 小牛 | niudakok-kok | human | openclaw | PM/Backend | exec,repo,ci | local-server | private | 项目主管 |
| 小犇 | niuda-xiaoben | agent | openclaw | API/Docs | exec,repo,docs | cpu=2c;mem=4g;gpu=none;os=ubuntu | region=CN;proxy=yes;control=openclaw_gateway | availability=10:00-12:00,20:00-23:00(GMT+8) |
| 天津牛 | niuda-xiaoniu | agent | openclaw | Docs/API-Design/Review | exec,git,github | cpu=virtual;mem=shared;gpu=none;os=ubuntu | region=CN;proxy=yes;control=openclaw_gateway | 7x24 在线，可按小牛调度 |
| 昆明牛 | niuda-xiaomeng | agent | openclaw | Docs/Review | exec,web_search,browser,github | cpu=8c;mem=16g;gpu=none;os=debian | region=EU;proxy=no;control=openclaw_gateway | 老板的协作助理，偏文档/评审 |

### 字段说明
- actor_type：human / agent
- platform：openclaw / cloud_code / antigravity / other
- capabilities：用逗号分隔，例如 `exec,browser,docker,vision,feishu`
- server_profile：建议写成简短结构（不要写 IP），例如 `cpu=8c;mem=16g;gpu=none;os=ubuntu`
- network_profile：例如 `region=CN;proxy=yes/no;control=openclaw_gateway`

## 推荐工作方式
- 新协作者通过 PR 修改本表（留痕、可审计）。
- 项目主管根据本表进行任务分配与 CODEOWNERS 责任划分。
