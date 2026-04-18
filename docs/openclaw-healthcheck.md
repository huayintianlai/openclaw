# OpenClaw 分层健康检查方案

最后更新：2026-03-07

## 目标

避免“服务启动了但功能缺块”的问题，把检查拆成三层并形成上线门禁：

- L0 运行层：容器、进程、基础健康端点
- L2 依赖层：Gateway、渠道探针、模型探针、定时器状态
- L3 业务层：agent 合成回合

## 脚本

- 主脚本：`scripts/healthcheck_openclaw.sh`
- 快捷入口：`./oc.sh health`

## 用法

```bash
# quick（默认）：无业务副作用
./oc.sh health kent

# full：包含 L3 agent 合成回合
./oc.sh health kent --level full

# 全部实例
./oc.sh health
```

等价直调：

```bash
./scripts/healthcheck_openclaw.sh --instance kent --level full
```

## 退出码（门禁）

- `0`：全部通过
- `1`：存在失败项（fail）
- `2`：仅有告警（degraded）

可选参数 `--allow-degraded`：当仅告警时返回 0。

## 报告位置

默认输出：

- `backups/reports/health/latest.json`

结构包含：

- `summary.overall`：`pass` / `degraded` / `fail`
- `summary.totals`：pass/warn/fail/skip 数量
- `checks[]`：每个检查项的层级、状态、错误码、详情

## 检查项清单

### L0 运行层

- compose 服务状态（实例容器）
- `gateway /healthz`

### L2 依赖层

- `openclaw channels status --probe --json`（仅检查 `configured=true` 的账号）
- `openclaw models status --probe --json`
- `openclaw cron status --json`

### L3 业务层（full 模式）

- Agent 合成回合：`openclaw agent --agent xiaodong ... --json`

## 生产建议（推荐频率）

- quick：每 10 分钟
- full：每天 2 次（建议 09:00 / 21:00，避开高峰）

示例（crontab）：

```bash
*/10 * * * * cd /Users/xiaojiujiu2/Documents/openclaw-docker && /bin/bash scripts/healthcheck_openclaw.sh --instance kent --level quick >> backups/reports/cron-health.log 2>&1
0 9,21 * * * cd /Users/xiaojiujiu2/Documents/openclaw-docker && /bin/bash scripts/healthcheck_openclaw.sh --instance kent --level full >> backups/reports/cron-health.log 2>&1
```

## 最佳实践说明

- 不把“端口通”当“服务可用”：必须做协议层和业务层探测。
- 对外告警必须区分：
  - `SERVICE_DOWN`（容器/进程故障）
  - `AUTH_EXPIRED`（鉴权失效）
  - `DEGRADED`（部分模型/渠道异常）
- 任何 L3 失败不应静默降级，必须告警并附错误码。
