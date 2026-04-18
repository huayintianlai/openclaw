# TOOLS.md - 工具速查表

## 飞书多维表工具

### 数据源坐标
- **app_token**: `E8y1wVcfWicN0Lk9Ce5ciL9fnle`
- **收入表**: `tblmGKQFjewsNUNM`
- **支出表**: `tblBPxsrnLyFmuDe`

### 可用工具

| 工具名 | 用途 | 典型用法 |
|---|---|---|
| `feishu_bitable_app` | 多维表应用级操作 | 获取应用/表元信息 |
| `feishu_bitable_app_table_field` | 列出字段 | 字段漂移检测 |
| `feishu_bitable_app_table_record` | 记录查询与变更 | 月度数据分析的核心工具 |
| `feishu_fetch_doc` | 读取指定文档 | 查询公司文档 |
| `feishu_search_doc_wiki` | 搜索知识库 | 查找文档与 Wiki |

### 常用查询模式

#### 拉取某月收入数据
```
feishu_bitable_app_table_record (action=list)
  app_token: E8y1wVcfWicN0Lk9Ce5ciL9fnle
  table_id: tblmGKQFjewsNUNM
  filter: 账期 = "2026-02"
```

#### 拉取未结算股东利润
```
feishu_bitable_app_table_record (action=list)
  app_token: E8y1wVcfWicN0Lk9Ce5ciL9fnle
  table_id: tblmGKQFjewsNUNM
  filter: 股东利润结算 = "未结算"
```

#### 检查字段是否漂移
```
feishu_bitable_app_table_field (action=list)
  app_token: E8y1wVcfWicN0Lk9Ce5ciL9fnle
  table_id: tblmGKQFjewsNUNM
  → 对比 FINANCE_RULES.md 中的字段字典
```

## 禁用工具（安全边界）

以下工具被 deny，绝不应尝试调用：
- `exec` / `process` — 禁止执行命令
- `write` / `edit` / `apply_patch` — 禁止写文件
