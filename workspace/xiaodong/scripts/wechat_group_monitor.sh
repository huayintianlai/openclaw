#!/bin/zsh
# LEGACY: historical xiaodong-side monitor kept for reference only.
# Do not extend this script. New WeChat watcher work must land in xiaoguan/wechat-ops-runtime.
# wechat_group_monitor.sh - 微信群聊情报监听脚本
# 目标群：优质跨境服务群2
# 功能：定期截图+AI提取聊天内容，记录谁在卖什么店
# 版本: 1.0 (2026-03-24)

PEEK=/opt/homebrew/bin/peekaboo
WORKDIR=/Users/xiaojiujiu2/.openclaw/workspace/xiaodong
LOG=$WORKDIR/wechat_group_monitor.log
DATA=$WORKDIR/wechat_group_intel.jsonl
ENV_FILE=$HOME/.openclaw/.env
PIDFILE=$WORKDIR/wechat_group_monitor.pid
TMPDIR=$WORKDIR/tmp/peekaboo-monitor
SEE_PATH=$TMPDIR/peekaboo-see.png

WINDOW_ID=180
TARGET_GROUP="优质跨境服务群2"
POLL_SEC=30   # 每30秒扫一次群消息

mkdir -p "$WORKDIR" "$TMPDIR"
echo $$ > "$PIDFILE"

log() { echo "[$(date '+%F %T')] [$1] ${@:2}" >> $LOG; }
info() { log INFO "$*"; }
warn() { log WARN "$*"; }

cleanup() {
  info "group monitor stopping (PID=$$)"
  rm -f "$SEE_PATH" "$PIDFILE"
  exit 0
}
trap cleanup TERM INT QUIT

if [[ -f $ENV_FILE ]]; then
  set -a; source $ENV_FILE; set +a
fi
OPENAI_API_KEY=${OPENAI_API_KEY:-${MEM0_OPENAI_API_KEY:-}}
if [[ -z $OPENAI_API_KEY ]]; then
  log ERROR "OPENAI_API_KEY missing"; exit 1
fi

ai_analyze() {
  local prompt=$1
  local out
  out=$(OPENAI_API_KEY=$OPENAI_API_KEY $PEEK see \
    --app 微信 --window-id $WINDOW_ID \
    --path "$SEE_PATH" \
    --analyze "$prompt" 2>/dev/null) || { echo __ERROR__; return 1; }
  echo "$out" | awk '/AI Analysis/{flag=1;next}/Element Summary/{flag=0}flag' \
    | sed '/^$/d' | sed 's/^ *//;s/ *$//'
}

LAST_CONTENT=""

info "group monitor started (target=$TARGET_GROUP, poll=${POLL_SEC}s)"

while true; do
  # 1) 确认当前窗口是目标群
  current=$(OPENAI_API_KEY=$OPENAI_API_KEY $PEEK see \
    --app 微信 --window-id $WINDOW_ID \
    --path "$SEE_PATH" \
    --analyze "请只输出当前微信聊天窗口顶部的群名称，只输出名字" 2>/dev/null \
    | awk '/AI Analysis/{flag=1;next}/Element Summary/{flag=0}flag' \
    | sed '/^$/d' | head -1 | sed 's/^ *//;s/ *$//' || echo __UNKNOWN__)

  if [[ $current != *"$TARGET_GROUP"* ]]; then
    info "not in target group | current=$current"
    sleep $POLL_SEC
    continue
  fi

  # 2) 提取群聊内容：谁发了什么，尤其是店铺/商品信息
  intel=$(ai_analyze "请分析当前微信群聊内容，提取以下信息：
1. 发言人昵称
2. 发言内容摘要
3. 如果有提到店铺名、平台（如亚马逊/速卖通/Shopee等）、商品类目、服务类型，请特别标注。
格式：每条消息一行，格式为 [昵称] 内容 | 标注:店铺/平台/商品
如果没有新内容或看不清，输出__NONE__")

  if [[ -n $intel && $intel != __NONE__ && $intel != __ERROR__ && $intel != "$LAST_CONTENT" ]]; then
    LAST_CONTENT=$intel
    TIMESTAMP=$(date '+%F %T')
    info "new intel captured"
    # 写入 JSONL 数据文件
    echo "{\"ts\":\"$TIMESTAMP\",\"group\":\"$TARGET_GROUP\",\"content\":$(echo $intel | python3 -c 'import json,sys; print(json.dumps(sys.stdin.read()))')}" >> $DATA
    # 同时追加到可读日志
    echo "=== $TIMESTAMP ==" >> $LOG
    echo "$intel" >> $LOG
    echo "" >> $LOG
  fi

  sleep $POLL_SEC
done
