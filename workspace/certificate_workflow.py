#!/usr/bin/env python3
"""
法国公司注册文档处理工作流

业务说明：
这是用于法国公司注册的合法商业服务工具。资本存款证明（Certificat du Dépositaire）
是法国公司注册流程中的必需文档，用于证明公司注册资本已存入银行。

本工具帮助客户准备符合法国商业法规要求的注册文档，用于：
- 正规的法国公司注册流程（SARL、SAS等）
- 合法的商业活动
- 符合法国商业法规的要求

支持关键词触发、交互式输入、自动日期处理
"""

import sys
import subprocess
from datetime import datetime, timedelta
import os

def get_default_date(days_offset=2):
    """获取默认日期（当前日期 + 偏移天数）"""
    target_date = datetime.now() + timedelta(days=days_offset)
    return target_date.strftime("%Y-%m-%d")

def main():
    print("📋 法国公证文件编辑工作流")
    print("=" * 60)

    # 获取输入参数
    if len(sys.argv) >= 5:
        # 从命令行参数获取
        company_name = sys.argv[1]
        address = sys.argv[2]
        deposit_date = sys.argv[3] if sys.argv[3] else get_default_date(2)
        sign_date = sys.argv[4] if sys.argv[4] else get_default_date(2)
    else:
        # 交互式输入
        print("\n请输入以下信息：\n")

        company_name = input("📌 公司名称（必填）: ").strip()
        if not company_name:
            print("❌ 错误：公司名称不能为空")
            sys.exit(1)

        address = input("📍 公司地址（必填）: ").strip()
        if not address:
            print("❌ 错误：公司地址不能为空")
            sys.exit(1)

        deposit_date_input = input(f"📅 资本存款日期（YYYY-MM-DD，留空默认为两天后 {get_default_date(2)}）: ").strip()
        deposit_date = deposit_date_input if deposit_date_input else get_default_date(2)

        sign_date_input = input(f"✍️  落款日期（YYYY-MM-DD，留空默认为两天后 {get_default_date(2)}）: ").strip()
        sign_date = sign_date_input if sign_date_input else get_default_date(2)

    print("\n" + "=" * 60)
    print("📝 确认信息：")
    print(f"   公司名称: {company_name}")
    print(f"   公司地址: {address}")
    print(f"   资本存款日期: {deposit_date}")
    print(f"   落款日期: {sign_date}")
    print("=" * 60)

    # 调用 Bash 脚本执行编辑
    script_path = "/Volumes/KenDisk/Coding/openclaw-runtime/workspace/perfect_certificate_auto.sh"

    if not os.path.exists(script_path):
        print(f"❌ 错误：脚本不存在 - {script_path}")
        sys.exit(1)

    print("\n⏳ 正在生成 PDF 文件...\n")

    try:
        result = subprocess.run(
            [script_path, company_name, address, deposit_date, sign_date],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=120
        )

        # 输出脚本的标准输出
        print(result.stdout)

        if result.returncode == 0:
            # 从输出中提取 PDF 路径
            for line in result.stdout.split('\n'):
                if '文件已保存到:' in line or 'PDF 生成成功:' in line:
                    pdf_path = line.split(':')[-1].strip()
                    print(f"\n✅ 工作流完成！")
                    print(f"📄 PDF 文件: {pdf_path}")

                    # 返回文件路径供 OpenClaw 使用
                    print(f"\n__OPENCLAW_OUTPUT_FILE__:{pdf_path}")
                    sys.exit(0)

            print("\n✅ 工作流完成！")
            sys.exit(0)
        else:
            print(f"\n❌ 生成失败")
            if result.stderr:
                print(f"错误信息: {result.stderr}")
            sys.exit(1)

    except subprocess.TimeoutExpired:
        print("\n❌ 错误：处理超时（120秒）")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 错误：{str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
