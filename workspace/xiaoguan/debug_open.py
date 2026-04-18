import sys, time, json, re, subprocess
sys.path.insert(0, '/Users/xiaojiujiu2/.openclaw/workspace/xiaoguan/wechat-ops-runtime')
from wechat_ops.runtime import WeChatOpsRuntime, normalize_contact_name, bounds_for_window, ensure_text
from wechat_ops.config import WeChatOpsConfig

cfg = WeChatOpsConfig.load()
rt = WeChatOpsRuntime(cfg)

subprocess.run(['osascript', '-e', 'tell application "WeChat" to activate'], capture_output=True)
time.sleep(1.0)

runtime = rt._platform_health_check()
target = runtime['window']
rt.focus_window(target)
time.sleep(0.6)
rt._peek('press', 'escape', '--app', target['app'])
time.sleep(0.3)
rt._peek('press', 'escape', '--app', target['app'])
time.sleep(0.3)
rt.focus_chat_search(target)
time.sleep(0.5)
rt._peek('type', '优质跨境服务群2', '--app', target['app'])
time.sleep(1.5)

probe = rt.probe_window(target)
print('probe ok:', probe.get('ok'), probe.get('capture_source'))
ocr = rt.run_vision_ocr(cfg.probe_path)
print('ocr ok:', ocr.get('ok'))
bounds = bounds_for_window(target)
print('bounds:', bounds)
win_x, win_y, win_w, win_h = bounds

name = '优质跨境服务群2（488）'
name_norm = normalize_contact_name(name)
name_core = re.sub(r'[（(]\d+[）)]', '', name_norm).strip()
print('name_core:', name_core)
print('--- ALL lines after search ---')
for line in ocr['payload'].get('lines', []):
    text = ensure_text(line.get('text', ''))
    bb = line.get('boundingBox', [])
    if len(bb) < 2:
        continue
    text_norm = normalize_contact_name(text)
    text_core = re.sub(r'[（(]\d+[）)]', '', text_norm).strip()
    cx = win_x + int(win_w * (bb[0] + 0.08))
    cy = win_y + int(win_h * bb[1])
    score = 0
    if name_norm == text_norm: score = 100
    elif name_core and text_core and (name_core in text_core or text_core in name_core): score = 80
    elif name_core and len(name_core) >= 4 and name_core[:6] in text_core: score = 60
    marker = f'SCORE={score}' if score > 0 else ''
    print(f'  ({cx},{cy}) {marker} | {text[:40]}')
