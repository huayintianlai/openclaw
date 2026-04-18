import json

# 读取配置
with open('/Volumes/KenDisk/Coding/openclaw-runtime/openclaw.json', 'r') as f:
    config = json.load(f)

# 找到 tietou agent 并启用 heartbeat
found = False
for agent in config.get('agents', []):
    if agent.get('id') == 'tietou':
        agent['heartbeat'] = {
            "enabled": True,
            "intervalMinutes": 60,
            "prompt": "Read HEARTBEAT.md if it exists (workspace context). Follow it strictly. Do not infer or repeat old tasks from prior chats. If nothing needs attention, reply HEARTBEAT_OK."
        }
        print(f"✅ 已为 tietou 启用 heartbeat（每60分钟检查一次）")
        found = True
        break

if not found:
    print("❌ 未找到 tietou agent")
    exit(1)

# 保存配置
with open('/Volumes/KenDisk/Coding/openclaw-runtime/openclaw.json', 'w') as f:
    json.dump(config, f, indent=2, ensure_ascii=False)

print("✅ 配置已保存")
