#!/usr/bin/env python3
"""
下载并配置政府单据所需的字体
"""
import os
import urllib.request
from pathlib import Path

# 字体存储目录
font_dir = Path("/Volumes/KenDisk/Coding/openclaw-runtime/extensions/bill-generator-plugin/fonts")
font_dir.mkdir(exist_ok=True)

print("政府单据字体配置")
print("=" * 60)
print()

# 需要的字体
fonts_needed = {
    "微软雅黑": "msyh.ttc",
    "华文仿宋": "STFangsong.ttf"
}

print("需要的字体：")
for name, file in fonts_needed.items():
    print(f"  - {name} ({file})")
print()

print("注意：")
print("由于版权原因，这些字体需要手动获取。")
print()
print("请将以下字体文件复制到：")
print(f"  {font_dir}")
print()
print("字体文件：")
print("  1. msyh.ttc (微软雅黑)")
print("  2. STFangsong.ttf (华文仿宋)")
print()
print("字体来源：")
print("  - Windows系统：C:\\Windows\\Fonts\\")
print("  - macOS系统：/System/Library/Fonts/ 或 /Library/Fonts/")
print("  - 或从正版Office安装包中提取")
print()

# 检查字体是否已存在
print("当前字体状态：")
for name, file in fonts_needed.items():
    font_path = font_dir / file
    if font_path.exists():
        print(f"  ✓ {name}: 已安装")
    else:
        print(f"  ✗ {name}: 未安装")
print()

# 检查系统字体
print("检查系统可用字体...")
import fitz

try:
    # 尝试使用内置字体
    test_fonts = {
        'china-s': '简体中文宋体',
        'china-ss': '简体中文宋体（细）',
        'china-t': '繁体中文宋体',
        'china-ts': '繁体中文宋体（细）'
    }

    print("PyMuPDF内置中文字体：")
    for font_name, desc in test_fonts.items():
        try:
            font = fitz.Font(font_name)
            print(f"  ✓ {font_name}: {desc}")
        except:
            print(f"  ✗ {font_name}: 不可用")
except Exception as e:
    print(f"  错误: {e}")
