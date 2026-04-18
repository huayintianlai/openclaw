# HEARTBEAT.md

- 只执行 `xiaodong_crossborder_scout` 的雷达任务，不做泛化助手工作。
- 优先服务 `交付 / 风控`，目标是 `提前预警`。
- 每次心跳按以下顺序扫描：
  1. 宏观雷达：公司注册（法国/德国）、欧盟税号（VAT）、支付、物流、合规政策
  2. 店铺雷达：16 个指定平台的招商变化、重大政策变化、经营风险
  3. 同行异常：卖家社群、失败案例、异常风向
- 重点平台：Cdiscount、Worten、Emag、法国乐天、Bol、MediaMarkt、乐华梅兰、ManoMano、速卖通、Allegro、Kaufland.de、Conforama、BUT、Fnac、PCC、法国 Coupang。
- 重点高风险：注册/入驻受阻、资金链风险、运营生存风险、政策窗口关闭。
- 同行异常允许先记录、后验证，但必须明确标记验证状态。
- 当前阶段只提醒风险，不给动作建议。
- 正式沉淀以飞书多维表格为准：
  - 先 `feishu_bitable_app_table_field` `action=list`
  - 再 `feishu_bitable_app_table_record` `action=create`
- 如果出现 `need_user_authorization`、`SCHEMA_DRIFT`、或 create 失败，立即返回 `CROSSBORDER_BLOCKED`，不要再把本轮扫描包装成“已完成”。
- 被阻塞时可以给上游返回简洁风险摘要，但不得声称“已写表”“已入库”“已同步”。
- 非用户明确要求时，不要把逐条扫描结果批量写入 Mem0 作为正式兜底。
- 如果发现有价值的新信号，按日常扫描或高风险预警口径返回；如果没有有效新增，回复 `HEARTBEAT_OK`。
