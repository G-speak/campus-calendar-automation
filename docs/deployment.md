# QQ 消息获取与部署

## 1. 运行 NapCat

在已安装 Docker Compose 的 Linux 服务器上把项目放到 `/opt/campus-calendar-automation`，配置根目录 `.env`，再执行：

```sh
docker compose --env-file .env -f deploy/compose.yaml up -d
```

NapCat 是 PC 端 QQ，同账号电脑 QQ 登录可能挤掉它；手机 QQ 可以同时在线。不要为了检查状态反复重启容器。

WebUI 和 OneBot 仅绑定服务器回环地址。需要扫码时从本机开隧道：

```sh
ssh -L 6099:127.0.0.1:6099 your-server
```

浏览器打开 `http://127.0.0.1:6099/webui`，使用 `.env` 中的 token 进入并扫码。不要公开分享包含 token 的链接。

## 2. 开启 OneBot

在 WebUI 配置 WebSocket 服务端：启用，容器内 host `0.0.0.0`、port `3001`，token 与 `WS_TOKEN` 相同，消息格式 array，心跳 30000ms。保存后按当前 NapCat 提示重载。对应持久化目录 `data/napcat-config/`；登录会话在 `data/qq-session/`。

## 3. 安装消费者

在项目根目录创建虚拟环境并安装 requirements，填写 `.env`。Apple 日历先建好配置中指定的通知日历，否则程序会报错而不会随意写入另一个日历。

```sh
sudo cp deploy/qq-notify.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now qq-notify
sudo systemctl status qq-notify
sudo journalctl -u qq-notify -n 30 --no-pager
```

看到“已连接 OneBot WebSocket”表示消费者连接成功，还需确认 NapCat 自身 QQ 在线。

## 4. 从现有部署迁移

先备份旧脚本、systemd 文件、去重 state 和日历；将旧脚本中的私人参数复制到新 `.env`。API key 单独填写，不再引用其他项目配置。复制旧 `qq_notify_state.json` 到新项目 `data/`。停止旧消费者后才启动新消费者；同一时间只运行一个，NapCat 本身不必重启。

## 5. 排障与回滚

- 没消息：先看 QQ 在线状态，再看消费者 WebSocket 状态与群号；服务 active 不保证 QQ 在线。
- AI 退化：检查所选服务的模型是否支持、返回结构和超时；失败会采用规则兜底。
- 无关通知：查 `[无关跳过]`；身份不确定时仍可能保留消息，参见 filtering.md。
- 日历不同步：以服务端读回结果为准，手机可能延迟；不要反复创建。
- 回滚：停止新消费者，恢复旧 systemd 配置及备份 state 后启动旧服务。
- 原始群通知会发送到你配置的 LLM 服务提炼；日志也会保留部分通知片段。不要把生产日志和 `.env` 提交到仓库。

测试只用离线模拟事件。不要向真实 QQ 群发“测试消息”。
