#!/bin/bash
# 测试 OpenClaw Agent Binding 配置

echo "=== OpenClaw Agent Binding 测试 ==="
echo ""

CONFIG_FILE="/Volumes/KenDisk/Coding/openclaw-runtime/openclaw.json"

echo "1. 检查 afeng agent 配置..."
if grep -q '"id": "afeng"' "$CONFIG_FILE"; then
    echo "   ✅ afeng agent 已配置"
else
    echo "   ❌ afeng agent 未配置"
fi

echo ""
echo "2. 检查 afeng binding..."
if grep -q '"agentId": "afeng"' "$CONFIG_FILE"; then
    echo "   ✅ afeng binding 已配置"
    echo ""
    echo "   Binding 详情:"
    cat "$CONFIG_FILE" | grep -A 5 '"agentId": "afeng"'
else
    echo "   ❌ afeng binding 未配置"
fi

echo ""
echo "3. 检查 afeng AGENT.md..."
AGENT_MD="/Volumes/KenDisk/Coding/openclaw-runtime/agents/afeng/agent/AGENT.md"
if [ -f "$AGENT_MD" ]; then
    echo "   ✅ AGENT.md 存在"
    echo ""
    echo "   身份定位:"
    grep -A 2 "## 身份定位" "$AGENT_MD"
else
    echo "   ❌ AGENT.md 不存在"
fi

echo ""
echo "4. 检查 afeng workspace..."
WORKSPACE="/Volumes/KenDisk/Coding/openclaw-runtime/workspace/afeng"
if [ -d "$WORKSPACE" ]; then
    echo "   ✅ workspace 存在: $WORKSPACE"
else
    echo "   ❌ workspace 不存在"
fi

echo ""
echo "5. 检查飞书账号配置..."
if grep -q '"afeng":' "$CONFIG_FILE"; then
    echo "   ✅ 飞书账号已配置"
    echo ""
    echo "   账号详情:"
    cat "$CONFIG_FILE" | sed -n '/"afeng": {/,/}/p' | head -15
else
    echo "   ❌ 飞书账号未配置"
fi

echo ""
echo "=== 测试建议 ==="
echo ""
echo "在飞书中给阿峰发送以下消息进行测试："
echo ""
echo "1. 测试身份识别："
echo "   \"你的主要职责是什么？\""
echo ""
echo "2. 测试文件读取："
echo "   \"请读取你的 AGENT.md 文件，告诉我你的身份定位\""
echo ""
echo "3. 测试工作流："
echo "   \"编辑公证文件\""
echo ""
echo "预期结果："
echo "- 应该回答关于海外注册专员、法国公司注册的内容"
echo "- 不应该说自己是老金或其他 agent"
echo ""
