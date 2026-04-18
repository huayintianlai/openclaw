#!/usr/bin/env python3
"""
创建一个包含真实内容的PDF模板
"""
import fitz

# 创建PDF
doc = fitz.open()
page = doc.new_page(width=595, height=842)  # A4尺寸

# 尝试加载中文字体
try:
    # 尝试使用系统中文字体
    font = fitz.Font("china-s")  # 简体中文字体
except:
    font = None

# 添加标题
page.insert_text((50, 50), "电费账单", fontsize=20, fontname="china-s")

# 添加户名
page.insert_text((50, 100), "户名：张三", fontsize=12, fontname="china-s")

# 添加地址
page.insert_text((50, 130), "地址：北京市朝阳区XX街道XX号", fontsize=12, fontname="china-s")

# 添加账单编号
page.insert_text((50, 160), "账单编号：2024-03-12345", fontsize=12, fontname="china-s")

# 添加账期
page.insert_text((50, 190), "账期：2024年3月", fontsize=12, fontname="china-s")

# 添加用电量
page.insert_text((50, 220), "用电量：150 kWh", fontsize=12, fontname="china-s")

# 添加金额
page.insert_text((50, 250), "金额：98.50 元", fontsize=12, fontname="china-s")

# 保存
output_path = "/Volumes/KenDisk/Coding/openclaw-runtime/workspace/afeng/test_template.pdf"
doc.save(output_path)
doc.close()

print(f"✓ 创建模板成功: {output_path}")

# 验证内容
doc = fitz.open(output_path)
page = doc[0]
text = page.get_text()
print("\n模板内容:")
print(text)
doc.close()
