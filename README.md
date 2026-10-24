# Campus Calendar Automation · 校园日历自动化

独立于其他项目的 QQ 群通知 → 对象筛选 → AI 提炼 → iCloud 日历提醒，以及课程表解析、上传、备份和调课工具。

此仓库从正在运行的个人自动化系统整理而来，账号、群号、Apple 专用密码、API key、服务器地址、QQ 登录会话和私人课表均不包含在版本库中。运行参数全部由独立 `.env` 提供，不读取任何 AI 币项目文件。

## 功能

- NapCat / OneBot WebSocket 接收指定群消息；只监听，不向群发送消息。
- 基于入学年级、培养阶段、专业、指定对象判断相关性；直接 @ 本人优先保留。
- AI 输出标题、截止日期、活动时间、备注和相关性；模型失败时退回规则解析。
- 活动提前 30 分钟提醒；截止任务首次 10 分钟后提醒，另每天 09:00 提醒到截止日；纯通知 10 分钟后提醒。事件为 5 分钟短块。
- 按群号和消息 ID 去重。课程与消息通知分别使用自己的目标日历。
- 课程 JSON 上传和 ICS 全量备份；XLSX 教务总表辅助解析；已有课程原地顺延。

## 本地准备

Python 3.10+。在项目根目录运行：

```sh
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
chmod 600 .env
```

填写 `.env`。苹果日历使用 Apple 的 App 专用密码，不是 Apple ID 登录密码。中国区账户的 CalDAV 实际节点应通过发现流程取得，不能把某个个人账户的节点当通用节点。参见 [日历使用说明](docs/calendar.md)。

## 部署与日常使用

- [QQ 获取、NapCat 登录、systemd 部署与排障](docs/deployment.md)
- [课程整理、上传、备份与调课](docs/calendar.md)
- [筛选规则、身份更新和已知限制](docs/filtering.md)

运行监听：`python qq_notify.py`。

离线测试：`python -m unittest discover -s tests -v`。测试不会连接 QQ、调用模型或写入日历。

`python qq_notify.py --test` 则是**真实日历写入测试**，会创建后删除测试事件，日常验收优先用离线测试。

## 目录

- `qq_notify.py`：消息监听、提炼、时间解析和日历排程。
- `qq_relevance.py`：对象与年级筛选。
- `scripts/`：CalDAV 发现、课程上传、备份与调课。
- `deploy/`：NapCat Compose 和 systemd 模板。
- `examples/`：脱敏课程示例。
- `tests/`：离线规则和提示词格式测试。

## 当前整理范围

当前线上 QQ 服务继续运行原来的部署目录；此仓库是可独立配置的新整理版，没有自动迁移或重启生产环境。迁移前需要自行复制私人配置和消息去重状态，避免重复提醒。NapCat 镜像使用 upstream latest，正式迁移时建议固定测试通过的镜像摘要。
