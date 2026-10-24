# 苹果日历与课程上传

## 账号与日历发现

使用 Apple ID 的 App 专用密码。中国区与国际区可能返回不同权威节点：在 `.env` 设置对应入口后运行 `python scripts/calendar_tools.py discover`，从结果复制课表日历 URL 到 `COURSE_CALENDAR_URL`。这些 URL 包含账号标识，只存本地 `.env`。

课程建议写入独立“课表”日历，QQ 通知写入“工作”或单独“通知”日历。程序写 VEVENT（日历），不依赖新版提醒事项不再支持的 CalDAV VTODO。

## 整理课程

教务总表 XLSX 可用 `python scripts/parse_timetable_xlsx.py private.xlsx 教学班关键词` 辅助查看。总表可能同时包含多个专业，解析不是自动选出个人课表；请以个人教务导出为准。

将确认后的每次上课整理为 `examples/courses.json` 的格式。节次不是钟点，必须按学校真实作息填写。每周一个独立事件，便于停课和调课。仅用虚构示例，真实课表放在被 gitignore 排除的 `data/` 下。

## 上传与备份

```sh
python scripts/caldav_icloud.py list
python scripts/caldav_icloud.py backup backups/calendar-before.ics
python scripts/caldav_icloud.py put data/my-courses.json
```

上传后再次 list，核对次数与首末日期。当前上传工具每次新增事件，**不要重复上传同一个文件**，否则会重复；已有课程应原地修改。上传遇到失败先核对已成功部分，不要盲目重试整批。ICS 备份含私人日程，禁止公开提交。

## 调课

```sh
python scripts/calendar_tools.py shift --title '示例课程' --from-date 2026-11-01 --to-date 2026-11-08 --days 14
```

先预览，核对匹配日期后在相同命令末尾加 `--apply` 执行。工具保存原始 ICS，以 ETag 防止覆盖并发修改，原地更新并回读核对 UID 和起止时间。适用于独立单次课程，不支持 RRULE 系列；遇到失败立即停止，检查已成功部分后再操作。工具不自动处理与其他课的冲突，应先查看日历。

## 位置与地图

通用程序支持可选 LOCATION，但仓库不保存任何真实学校、校区、教室、坐标、个人课表或 MapKit handle。示例地点是虚构的。若不想让课程带地点，省略 JSON 的 `location` 字段即可。

从 Apple 导出的事件可能包含 `X-APPLE-STRUCTURED-LOCATION`、GEO 和长串地图标识；公开分享前不能只删 LOCATION，必须移除这些字段。本仓库不附真实 ICS。上传新课只写你本地提供的 LOCATION，不会自动获取当前位置，也不会自动查询地图坐标。日历 App 可能自行解析地点文字；同名教学楼被定位到其他城市时，应在私有配置中写清真实校区，或删除错误结构化地图标记。更改已有 LOCATION 时同步移除旧 `X-APPLE-STRUCTURED-LOCATION`，避免文字和地图不一致。
