# HEARTBEAT.md

## 微信结果消费（优先）

- 先查看 `/Users/xiaojiujiu2/.openclaw/workspace/xiaoguan/wechat-ops-runtime/state/results/pending` 是否存在待消费结果；如果没有，再继续其他巡检。
- 业务输入只认 `results/pending/*.json`，不要把 `events.jsonl` 当成业务消费入口。
- 处理完成后，用 `exec` 把结果文件移动到 `results/consumed`；如果飞书字段异常、工具报错或事实不够完整，就移动到 `results/failed` 并在回执里说明真实原因。

结果处理规则：
- `unread.snapshot.changed`
  只生成内部提醒或会话级建议，不默认写飞书，不自动发微信。
- `chat.visible.delta`
  只看 `added_messages`。命中线索或资源关键词时，写入群消息监听表 `tblhviIhGA7ToWxy`；未命中时只归档结果，不外写。
- `moments.cards.unseen`
  先对照 CRM 表 `tblTrN5hZM9w0Aj2`、意向表 `tblc2lDtItP7N7vp`、成交表 `tbl2SZmEq4LbQkBk` 判断作者是否为已知客户；命中已知客户时创建或更新《小冠任务清单》跟进任务，否则只提醒 Boss，不直接改 CRM 主数据。
- `watcher.health.changed`
  只回报 watcher、状态、错误码、推荐下一步；禁止猜测微信里“应该没问题”，也不要让 Boss 自己看微信确认消息是否发出。

群聊线索关键词基线：
- 购买/咨询：`想买` `购买` `多少钱` `价格` `报价` `咨询` `了解` `问一下` `请问`
- 紧急：`急` `尽快` `今天` `马上`
- 店铺/平台/资源：`店铺` `入驻` `注册` `法国` `德国` `英国` `亚马逊` `速卖通` `Shopee` `沃尔玛` `美客多` `希音` `新蛋` `半托` `现号`

## 每日任务与动态巡检

1. 先调用 `feishu_task_tasklist`，使用 `action=list` 找到《小冠任务清单》。
2. 再调用 `feishu_task_tasklist`，使用 `action=tasks` 拉取该清单中的任务；必要时补充 `feishu_task_task` `action=list` 且 `completed=false` 核对未完成任务。
3. 标记三类事项并提醒 Boss：
   - 24 小时内到期
   - 已逾期未完成
   - Boss 明确标记为高优先级
4. 对于新出现的动态（新需求、承诺、约定时间），立即建议创建任务并给出下一步。
5. 对已完成事项，提示执行 `feishu_task_task` 的 `action=patch` 并设置 `completed_at` 做闭环。

## 订单回归检查（保留）

- 如 Task API 临时不可用，可回退读取官方文档兜底页（使用 `feishu_fetch_doc`）做兜底检查，但恢复后仍以官方 Task 为准。
- 调用官方 `feishu_bitable_app_table_record` 检查预定单表 `tblm7Kkk6k5OQdxH` 与代入驻订单表 `tblbFLlgjqOjflnL` 的进行中/逾期项目。
- 若飞书表与兜底文档记录存在冲突，优先提醒 Boss 做一次状态对齐，并以官方 Task 最新状态为主。

## CRM 巡检（每2-3天执行一次）

所有表共用 app_token: `Z3DEboviLaJAlXsdUPvcItgrnZd`
- CRM表: `tblTrN5hZM9w0Aj2`
- 意向表: `tblc2lDtItP7N7vp`
- 成交表: `tbl2SZmEq4LbQkBk`

巡检规则：
1. 扫描意向表和成交表的客户名
2. 检查这些客户是否已录入CRM表
   - 不存在 → 提醒 Boss 补录（注意：纯服务商/上游渠道不用进CRM）
   - 已存在但主攻平台/消费区间/客户关键词为空 → 提醒 Boss 补充
3. 检查CRM表中「客户状态」为「跟进中」且「最近跟进时间」超过7天的客户 → 提醒 Boss 跟进

## 业务规则备忘

- CRM只录终端买家或有长期关系价值的客户
- 纯上游供应商/服务商（如 Toby）只记在成交表渠道备注，不进CRM
- B2B倒货（服务商→我→服务商）的下游也不进CRM
- 收款信息（定金/尾款）必须当天录入成交表，防止散款被遗忘
