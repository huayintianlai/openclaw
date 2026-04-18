#!/usr/bin/env python3
"""
物流同步技能
触发格式：订单{阿里巴巴订单号}的运单号：{运单号}，同步。

流程：
1. 从飞书表格查询阿里订单号 -> 商户订单号
2. 通过浏览器自动化登录内部系统
3. 搜索商户订单号，点编辑
4. 填入 shipped + 运单号，提交
"""

import re
import sys
import json
import time
import subprocess

# ============ 配置 ============
FEISHU_SPREADSHEET_TOKEN = "shtcnkNJV83oZqDGUqdCi83tKkh"
FEISHU_SHEET_ID = "7e18c8"
SYSTEM_URL = "http://love.99uwen.com:3667"
SYSTEM_ACCOUNT = "张建东"
SYSTEM_PASSWORD = "123456"

# ============ 工具函数 ============

def curl(method, url, token=None, data=None, retries=5):
    args = ["/usr/bin/curl", "-s", "-X", method, url]
    if token:
        args += ["-H", f"access_token: {token}"]
    if data is not None:
        args += ["-H", "Content-Type: application/json",
                 "-d", json.dumps(data, ensure_ascii=False)]
    for i in range(retries):
        r = subprocess.run(args, capture_output=True, text=True, timeout=25)
        if r.stdout.strip():
            return r.stdout
        time.sleep(2)
    return ""


def get_feishu_app_token():
    """获取飞书 app_access_token"""
    # 从 openclaw keychain 读取配置
    r = subprocess.run(
        ["security", "find-generic-password", "-s", "openclaw-feishu-app", "-a", "cli_a904a148eab81bd8", "-w"],
        capture_output=True, text=True
    )
    # fallback: 直接通过 openclaw gateway RPC 调用
    return None


def query_merchant_order_no(alibaba_order_no, feishu_token):
    """
    从飞书表格查询阿里巴巴订单号对应的商户订单号
    表格结构：A列=商户订单号，C列=阿里巴巴订单号
    """
    url = f"https://open.feishu.cn/open-apis/sheets/v2/spreadsheets/{FEISHU_SPREADSHEET_TOKEN}/values/{FEISHU_SHEET_ID}!A1:D500"
    r = subprocess.run(
        ["/usr/bin/curl", "-s", url, "-H", f"Authorization: Bearer {feishu_token}"],
        capture_output=True, text=True, timeout=15
    )
    if not r.stdout.strip():
        return None
    data = json.loads(r.stdout)
    rows = data.get("data", {}).get("valueRange", {}).get("values", [])
    for row in rows:
        if len(row) >= 3 and str(row[2]) == str(alibaba_order_no):
            return str(row[0])  # A列=商户订单号
    return None


# ============ 浏览器自动化（通过 OpenClaw browser tool） ============
# 注意：实际执行由 OpenClaw agent 的 browser tool 完成，
# 本脚本记录完整流程步骤供 agent 参考。

BROWSER_STEPS = """
浏览器自动化步骤：

1. 打开登录页：{system_url}/admin/#/login
2. 填写用户名（ref=e11 或 placeholder=请填写用户名）：{account}
3. 填写密码（ref=e13 或 placeholder=请填写用户登录密码）：{password}
4. 点击登录按钮
5. 导航到：{system_url}/admin/#/logistics/list
6. 找到第三个 input（placeholder=请输入订单编号），用 nativeInputValueSetter 填入商户订单号，触发 input/change 事件
7. 触发 keydown/keypress/keyup Enter 事件
8. 等待列表刷新，点击目标订单的编辑按钮
9. 在编辑页：
   a. 找到 value=paid 的 input，用 nativeInputValueSetter 改为 shipped，触发 input/change
   b. 找到 placeholder=请输入渠道名称 的 input，填入运单号，触发 input/change
10. 点击提交修改按钮
11. 验证列表中订单状态变为 已发货
"""


def main():
    if len(sys.argv) < 3:
        print("用法: sync.py <阿里巴巴订单号> <运单号>")
        sys.exit(1)

    alibaba_order_no = sys.argv[1]
    tracking_no = sys.argv[2]

    print(f"阿里巴巴订单号: {alibaba_order_no}")
    print(f"运单号: {tracking_no}")
    print("\n浏览器操作步骤:")
    print(BROWSER_STEPS.format(
        system_url=SYSTEM_URL,
        account=SYSTEM_ACCOUNT,
        password=SYSTEM_PASSWORD
    ))


if __name__ == "__main__":
    main()
