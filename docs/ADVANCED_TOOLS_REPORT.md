# 高级功能实施报告 - 记忆作用域管理工具

**实施时间：** 2026-03-13 13:40
**状态：** ✅ 已完成

---

## 执行摘要

成功实施了两个高级管理工具，用于手动管理记忆的作用域和共享权限。这些工具允许用户在记忆创建后动态调整访问控制，提供了更灵活的记忆管理能力。

**核心成果：**
- ✅ memory_set_scope 工具（手动调整作用域）
- ✅ memory_share 工具（共享记忆给其他 agent）
- ✅ 直接操作 Qdrant API 更新 metadata
- ✅ 完整的参数验证和错误处理

---

## 工具 1: memory_set_scope

### 功能描述

手动调整记忆的作用域（private/group/public），改变谁可以访问该记忆。

### 使用场景

1. **将公开记忆改为私密**
   - 场景：某条记忆最初是公开的，但后来发现包含敏感信息
   - 操作：`memory_set_scope(memoryId, "private")`

2. **将私密记忆共享给团队**
   - 场景：某条个人记忆需要与团队成员共享
   - 操作：`memory_set_scope(memoryId, "group", ["xiaodong", "xiaoguan"])`

3. **将群聊记忆改为公开**
   - 场景：某条群聊记忆包含通用知识，希望所有 agent 都能访问
   - 操作：`memory_set_scope(memoryId, "public")`

### 参数说明

```typescript
{
  memoryId: string;        // 记忆 ID（必填）
  scope: "private" | "group" | "public";  // 新作用域（必填）
  participants?: string[]; // 参与者列表（group 作用域必填）
}
```

### 实现逻辑

1. **参数验证**
   - 检查 scope 为 "group" 时是否提供了 participants
   - 验证 participants 数组非空

2. **获取现有记忆**
   - 使用 `provider.get(memoryId)` 获取记忆
   - 验证记忆是否存在

3. **构建新 metadata**
   ```typescript
   {
     ...currentMetadata,
     scope: scope,
     owner: currentMetadata.owner || toolCtx.agentId,
     participants: scope === "private"
       ? [owner]
       : scope === "group"
       ? participants
       : ["*"],
     scope_updated_at: new Date().toISOString(),
     scope_updated_by: toolCtx.agentId
   }
   ```

4. **更新 Qdrant**
   - 直接调用 Qdrant API `/collections/{collection}/points/payload`
   - 使用 POST 方法更新 metadata

### 代码位置

- 文件：`instances/kentclaw/data/extensions/openclaw-mem0/index.ts`
- 位置：行 1436-1550（约）
- 工具名：`memory_set_scope`

### 使用示例

```typescript
// 示例 1: 将记忆改为私密
await memory_set_scope({
  memoryId: "abc123",
  scope: "private"
});

// 示例 2: 将记忆共享给团队
await memory_set_scope({
  memoryId: "abc123",
  scope: "group",
  participants: ["xiaodong", "xiaoguan", "echo"]
});

// 示例 3: 将记忆改为公开
await memory_set_scope({
  memoryId: "abc123",
  scope: "public"
});
```

---

## 工具 2: memory_share

### 功能描述

将私密或群聊记忆共享给额外的 agent。自动将作用域改为 "group" 并添加指定的 agent 到参与者列表。

### 使用场景

1. **扩大群聊记忆的访问范围**
   - 场景：某条群聊记忆需要让更多人看到
   - 操作：`memory_share(memoryId, ["finance", "echo"])`

2. **将私密记忆共享给特定人员**
   - 场景：某条私密记忆需要与特定同事共享
   - 操作：`memory_share(memoryId, ["xiaoguan"])`

3. **逐步扩大访问权限**
   - 场景：随着项目进展，需要让更多人访问某条记忆
   - 操作：多次调用 `memory_share` 添加新成员

### 参数说明

```typescript
{
  memoryId: string;   // 记忆 ID（必填）
  shareWith: string[]; // 要共享给的 agent ID 列表（必填）
}
```

### 实现逻辑

1. **参数验证**
   - 检查 shareWith 数组非空

2. **获取现有记忆**
   - 使用 `provider.get(memoryId)` 获取记忆
   - 验证记忆是否存在

3. **合并参与者列表**
   ```typescript
   const currentParticipants = currentMetadata.participants || [owner];
   const newParticipants = Array.from(new Set([...currentParticipants, ...shareWith]));
   ```
   - 使用 Set 去重
   - 保留原有参与者

4. **构建新 metadata**
   ```typescript
   {
     ...currentMetadata,
     scope: "group",  // 自动改为 group
     owner: currentMetadata.owner || toolCtx.agentId,
     participants: newParticipants,
     scope_updated_at: new Date().toISOString(),
     scope_updated_by: toolCtx.agentId
   }
   ```

5. **更新 Qdrant**
   - 直接调用 Qdrant API 更新 metadata

### 代码位置

- 文件：`instances/kentclaw/data/extensions/openclaw-mem0/index.ts`
- 位置：行 1552-1660（约）
- 工具名：`memory_share`

### 使用示例

```typescript
// 示例 1: 共享给单个 agent
await memory_share({
  memoryId: "abc123",
  shareWith: ["xiaoguan"]
});

// 示例 2: 共享给多个 agent
await memory_share({
  memoryId: "abc123",
  shareWith: ["finance", "echo", "aduan"]
});

// 示例 3: 逐步添加成员
await memory_share({
  memoryId: "abc123",
  shareWith: ["xiaoguan"]
});
// 稍后再添加
await memory_share({
  memoryId: "abc123",
  shareWith: ["finance"]
});
// 最终 participants: [owner, "xiaoguan", "finance"]
```

---

## 技术实现细节

### 为什么直接操作 Qdrant API？

**问题：** Mem0 不支持仅更新 metadata 的操作

**Mem0 API 限制：**
- `add()` - 添加新记忆
- `search()` - 搜索记忆
- `get()` - 获取记忆
- `delete()` - 删除记忆
- ❌ 没有 `update()` 或 `updateMetadata()` 方法

**解决方案：** 直接调用 Qdrant REST API

```typescript
const response = await fetch(`${qdrantUrl}/collections/${collection}/points/payload`, {
  method: "POST",
  headers: {
    "api-key": qdrantApiKey,
    "Content-Type": "application/json",
  },
  body: JSON.stringify({
    points: [memoryId],
    payload: {
      metadata: newMetadata,
    },
  }),
});
```

**优点：**
- ✅ 直接更新 metadata，不影响其他字段
- ✅ 高效，无需重新生成向量
- ✅ 保留原有记忆内容和向量

**缺点：**
- ⚠️ 绕过 Mem0 抽象层
- ⚠️ 需要直接访问 Qdrant 环境变量

---

## 错误处理

### 1. 参数验证错误

**场景：** scope 为 "group" 但未提供 participants

```json
{
  "error": "missing_participants",
  "message": "Error: 'group' scope requires a non-empty 'participants' array."
}
```

**场景：** shareWith 数组为空

```json
{
  "error": "missing_agents",
  "message": "Error: 'shareWith' must contain at least one agent ID."
}
```

### 2. 记忆不存在

```json
{
  "error": "not_found",
  "message": "Memory not found: abc123"
}
```

### 3. Qdrant 更新失败

```json
{
  "error": "Qdrant update failed: Bad Request",
  "message": "Failed to update memory scope: ..."
}
```

---

## 部署状态

### 文件变更

**修改文件：**
- `instances/kentclaw/data/extensions/openclaw-mem0/index.ts`
  - 新增 memory_set_scope 工具（约 115 行）
  - 新增 memory_share 工具（约 108 行）
  - 总计新增约 223 行代码

**备份文件：**
- `index.ts.backup-advanced-tools-20260313-133940`

### 容器状态

- **状态：** healthy (Up 17 seconds)
- **插件：** openclaw-mem0 initialized
- **工具注册：** memory_set_scope, memory_share

---

## 测试验证

### 手动测试步骤

**测试 1: memory_set_scope（private → group）**

```bash
# 1. 获取一条记忆 ID
curl -s -X POST "${QDRANT_URL}/collections/${MEM0_QDRANT_COLLECTION}/points/scroll" \
  -H "api-key: ${QDRANT_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"limit": 1, "with_payload": true}' | \
  jq -r '.result.points[0].id'

# 2. 使用工具调整作用域（需要通过 OpenClaw 调用）
# memory_set_scope(memoryId: "xxx", scope: "group", participants: ["xiaodong", "xiaoguan"])

# 3. 验证更新
curl -s -X POST "${QDRANT_URL}/collections/${MEM0_QDRANT_COLLECTION}/points" \
  -H "api-key: ${QDRANT_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"ids": ["xxx"], "with_payload": true}' | \
  jq '.result[0].payload.metadata | {scope, owner, participants}'

# 预期输出：
# {
#   "scope": "group",
#   "owner": "xiaodong",
#   "participants": ["xiaodong", "xiaoguan"]
# }
```

**测试 2: memory_share（添加成员）**

```bash
# 1. 使用工具共享记忆（需要通过 OpenClaw 调用）
# memory_share(memoryId: "xxx", shareWith: ["finance", "echo"])

# 2. 验证更新
curl -s -X POST "${QDRANT_URL}/collections/${MEM0_QDRANT_COLLECTION}/points" \
  -H "api-key: ${QDRANT_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"ids": ["xxx"], "with_payload": true}' | \
  jq '.result[0].payload.metadata | {scope, participants}'

# 预期输出：
# {
#   "scope": "group",
#   "participants": ["xiaodong", "xiaoguan", "finance", "echo"]
# }
```

---

## 使用指南

### 何时使用 memory_set_scope？

1. **需要完全控制作用域**
   - 从 private 改为 public
   - 从 group 改为 private
   - 完全替换参与者列表

2. **需要降低访问权限**
   - 将公开记忆改为私密
   - 缩小群聊记忆的访问范围

### 何时使用 memory_share？

1. **需要扩大访问权限**
   - 添加新成员到群聊记忆
   - 将私密记忆共享给特定人员

2. **需要保留现有参与者**
   - 不想替换整个参与者列表
   - 只想添加新成员

### 最佳实践

1. **使用 memory_share 添加成员**
   - 更安全，不会意外移除现有成员
   - 自动去重，避免重复添加

2. **使用 memory_set_scope 调整作用域**
   - 需要完全控制时使用
   - 小心操作，可能会移除现有成员

3. **记录操作历史**
   - 两个工具都会记录 scope_updated_at 和 scope_updated_by
   - 便于审计和追踪

---

## 限制和注意事项

### 1. 需要知道 memoryId

**问题：** 用户通常不知道记忆的 ID

**解决方案：**
- 先使用 `memory_search` 工具搜索记忆
- 从搜索结果中获取 memoryId
- 然后调用 memory_set_scope 或 memory_share

### 2. 无法批量操作

**问题：** 每次只能更新一条记忆

**解决方案：**
- 如果需要批量操作，可以编写脚本
- 或者在工具中添加批量操作支持（未来优化）

### 3. 不验证 agent ID 是否存在

**问题：** 可以添加不存在的 agent ID 到 participants

**影响：** 不存在的 agent 永远无法访问该记忆

**缓解：** 在使用前确认 agent ID 正确

---

## 监控和审计

### 查看作用域变更历史

```bash
# 查看最近更新的记忆
curl -s -X POST "${QDRANT_URL}/collections/${MEM0_QDRANT_COLLECTION}/points/scroll" \
  -H "api-key: ${QDRANT_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"limit": 10, "with_payload": true}' | \
  jq '.result.points[] | select(.payload.metadata.scope_updated_at != null) | {
    memory: .payload.data,
    scope: .payload.metadata.scope,
    updated_at: .payload.metadata.scope_updated_at,
    updated_by: .payload.metadata.scope_updated_by
  }'
```

### 统计各作用域的记忆数

```bash
# Private 记忆
curl -s -X POST "${QDRANT_URL}/collections/${MEM0_QDRANT_COLLECTION}/points/scroll" \
  -H "api-key: ${QDRANT_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"filter": {"must": [{"key": "metadata.scope", "match": {"value": "private"}}]}, "limit": 1000}' | \
  jq '.result.points | length'

# Group 记忆
curl -s -X POST "${QDRANT_URL}/collections/${MEM0_QDRANT_COLLECTION}/points/scroll" \
  -H "api-key: ${QDRANT_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"filter": {"must": [{"key": "metadata.scope", "match": {"value": "group"}}]}, "limit": 1000}' | \
  jq '.result.points | length'

# Public 记忆
curl -s -X POST "${QDRANT_URL}/collections/${MEM0_QDRANT_COLLECTION}/points/scroll" \
  -H "api-key: ${QDRANT_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"filter": {"must": [{"key": "metadata.scope", "match": {"value": "public"}}]}, "limit": 1000}' | \
  jq '.result.points | length'
```

---

## 总结

成功实施了两个高级管理工具，提供了灵活的记忆作用域管理能力。

**核心成果：**
- ✅ memory_set_scope 工具（完全控制作用域）
- ✅ memory_share 工具（添加访问权限）
- ✅ 直接操作 Qdrant API（绕过 Mem0 限制）
- ✅ 完整的错误处理和参数验证
- ✅ 操作审计（scope_updated_at, scope_updated_by）

**技术亮点：**
- 直接操作 Qdrant API 实现 metadata 更新
- 自动去重参与者列表
- 完整的参数验证和错误处理
- 操作历史记录

**使用建议：**
- 使用 memory_share 添加成员（更安全）
- 使用 memory_set_scope 完全控制作用域
- 先搜索记忆获取 memoryId，再调用管理工具

---

**实施人员：** Claude (Kiro)
**完成时间：** 2026-03-13 13:45
**状态：** ✅ 已完成并部署
