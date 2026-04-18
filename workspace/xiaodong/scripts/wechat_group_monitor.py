#!/usr/bin/env python3
# LEGACY: historical xiaodong-side monitor kept for reference only.
# Do not extend this script. New WeChat watcher work must land in xiaoguan/wechat-ops-runtime.
# wechat_group_monitor.py - 微信群聊情报监听脚本（Python版）
# 目标群：优质跨境服务群2
# 功能：定期截图+AI提取聊天内容，记录谁在卖什么店
# 版本: 1.0 (2026-03-24)

import subprocess, json, os, time, sys, signal, datetime
from pathlib import Path

WORKDIR = Path('/Users/xiaojiujiu2/.openclaw/workspace/xiaodong')
LOG_FILE = WORKDIR / 'wechat_group_monitor.log'
DATA_FILE = WORKDIR / 'wechat_group_intel.jsonl'
ENV_FILE = Path.home() / '.openclaw' / '.env'
PID_FILE = WORKDIR / 'wechat_group_monitor.pid'
TMP_DIR = WORKDIR / 'tmp' / 'peekaboo-monitor'
SEE_PATH = TMP_DIR / 'peekaboo-see.png'

PEEK = '/opt/homebrew/bin/peekaboo'
WINDOW_ID = '180'
TARGET_GROUP = '优质跨境服务群2'
POLL_SEC = 30

def log(level, msg):
    ts = datetime.datetime.now().strftime('%F %T')
    line = f'[{ts}] [{level}] {msg}'
    print(line, flush=True)
    with open(LOG_FILE, 'a') as f:
        f.write(line + '\n')

def load_env():
    env = dict(os.environ)
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text().splitlines():
            line = line.strip()
            if '=' in line and not line.startswith('#'):
                k, v = line.split('=', 1)
                env[k.strip()] = v.strip()
    key = env.get('OPENAI_API_KEY') or env.get('MEM0_OPENAI_API_KEY', '')
    env['OPENAI_API_KEY'] = key
    return env

def ai_see(prompt, env):
    try:
        r = subprocess.run(
            [
                PEEK,
                'see',
                '--app',
                '微信',
                '--window-id',
                WINDOW_ID,
                '--path',
                str(SEE_PATH),
                '--analyze',
                prompt,
            ],
            capture_output=True, text=True, timeout=40, env=env
        )
        out = r.stdout
        lines = []
        flag = False
        for line in out.splitlines():
            if 'AI Analysis' in line:
                flag = True
                continue
            if 'Element Summary' in line:
                flag = False
            if flag and line.strip():
                lines.append(line.strip())
        return '\n'.join(lines).strip()
    except Exception as e:
        log('WARN', f'ai_see error: {e}')
        return '__ERROR__'

def save_intel(ts, group, content):
    record = {'ts': ts, 'group': group, 'content': content}
    with open(DATA_FILE, 'a') as f:
        f.write(json.dumps(record, ensure_ascii=False) + '\n')
    with open(LOG_FILE, 'a') as f:
        f.write(f'=== {ts} ===\n{content}\n\n')

def handle_signal(sig, frame):
    log('INFO', f'group monitor stopping (PID={os.getpid()})')
    SEE_PATH.unlink(missing_ok=True)
    PID_FILE.unlink(missing_ok=True)
    sys.exit(0)

signal.signal(signal.SIGTERM, handle_signal)
signal.signal(signal.SIGINT, handle_signal)

TMP_DIR.mkdir(parents=True, exist_ok=True)
PID_FILE.write_text(str(os.getpid()))
env = load_env()

if not env.get('OPENAI_API_KEY'):
    log('ERROR', 'OPENAI_API_KEY missing')
    sys.exit(1)

log('INFO', f'group monitor started (target={TARGET_GROUP}, poll={POLL_SEC}s)')

last_content = ''

while True:
    try:
        # 1) 确认当前窗口是目标群
        current = ai_see('请只输出当前微信聊天窗口顶部的群名称，只输出名字本身', env)
        if TARGET_GROUP not in current:
            log('INFO', f'not in target group | current={current}')
            time.sleep(POLL_SEC)
            continue

        # 2) 提取情报
        prompt = (
            '请分析当前微信群聊内容，提取以下信息：\n'
            '1. 发言人昵称\n'
            '2. 发言内容摘要\n'
            '3. 如果有提到店铺名、平台（如亚马逊/速卖通/Shopee/希音/沃尔玛/美客多等）、商品类目、服务类型，请特别标注。\n'
            '格式：每条消息一行，格式为 [昵称] 内容 | 标注:店铺/平台/商品\n'
            '如果没有新内容或看不清，输出__NONE__'
        )
        intel = ai_see(prompt, env)

        if intel and intel != '__NONE__' and intel != '__ERROR__' and intel != last_content:
            last_content = intel
            ts = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            log('INFO', f'new intel captured ({len(intel)} chars)')
            save_intel(ts, TARGET_GROUP, intel)

    except Exception as e:
        log('WARN', f'loop error: {e}')

    time.sleep(POLL_SEC)
