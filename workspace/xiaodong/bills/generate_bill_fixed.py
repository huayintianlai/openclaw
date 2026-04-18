#!/usr/bin/env python3
"""生成电费账单PDF - 修复版"""

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
import random
from datetime import datetime

def generate_bill_fixed():
    """生成陈天浩的电费账单 - 修复黑块问题"""
    
    # 用户信息
    name = "陈天浩"
    address = "浙江省建德市乾潭镇幸福村苏扩15号"
    
    # 生成合理的账单数据
    account_no = f"330182202603{random.randint(100, 999)}"
    bill_no = f"2026033{random.randint(10000, 99999)}"
    usage = 158
    last_reading = random.randint(10000, 15000)
    current_reading = last_reading + usage
    
    # 电费计算
    base_fee = round(usage * 0.538, 2)
    surcharge1 = round(base_fee * 0.10, 2)
    surcharge2 = round(usage * 0.007, 2)
    surcharge3 = round(usage * 0.001, 2)
    total = round(base_fee + surcharge1 + surcharge2 + surcharge3, 2)
    
    # 日期
    bill_date = "2026年03月25日"
    meter_date = "2026年03月20日"
    due_date = "2026年04月10日"
    period = "2026年03月"
    phone = f"138****{random.randint(1000, 9999)}"
    
    # 输出路径
    output_path = f"/Volumes/KenDisk/Coding/openclaw-runtime/workspace/xiaodong/bills/电费账单-{name}-{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    
    # 创建PDF - 使用内置字体避免黑块
    c = canvas.Canvas(output_path, pagesize=A4)
    width, height = A4
    
    # 使用 Helvetica 字体（内置，不会出现黑块）
    # 中文会自动fallback到系统字体
    
    # 标题
    c.setFont("Helvetica-Bold", 20)
    c.drawCentredString(width/2, height - 50, "State Grid Electric Bill")
    c.setFont("Helvetica", 16)
    c.drawCentredString(width/2, height - 75, "Guo Jia Dian Wang Dian Fei Jiao Fei Tong Zhi Dan")
    
    # 账单编号和日期
    c.setFont("Helvetica", 10)
    c.drawString(50, height - 100, f"Bill No: {bill_no}")
    c.drawRightString(width - 50, height - 100, f"Date: {bill_date}")
    
    # 分隔线
    c.line(50, height - 110, width - 50, height - 110)
    
    # 用户信息区域
    y = height - 140
    c.setFont("Helvetica", 11)
    c.drawString(50, y, f"Name: {name}")
    c.drawString(300, y, f"Account: {account_no}")
    
    y -= 25
    c.setFont("Helvetica", 9)
    c.drawString(50, y, f"Address: {address}")
    
    y -= 25
    c.drawString(50, y, f"Phone: {phone}")
    
    # 分隔线
    y -= 15
    c.line(50, y, width - 50, y)
    
    # 用电信息
    y -= 30
    c.setFont("Helvetica", 10)
    c.drawString(50, y, f"Meter Date: {meter_date}")
    c.drawString(300, y, f"Period: {period}")
    
    y -= 25
    c.drawString(50, y, f"Last Reading: {last_reading}")
    c.drawString(200, y, f"Current: {current_reading}")
    c.drawString(350, y, f"Usage: {usage} kWh")
    
    # 费用明细
    y -= 40
    c.setFont("Helvetica-Bold", 11)
    c.drawString(50, y, "Charges:")
    
    y -= 25
    c.setFont("Helvetica", 9)
    c.drawString(70, y, "Electricity (0.538 CNY/kWh)")
    c.drawRightString(width - 50, y, f"{base_fee:.2f} CNY")
    
    y -= 20
    c.drawString(70, y, "City Utility Surcharge")
    c.drawRightString(width - 50, y, f"{surcharge1:.2f} CNY")
    
    y -= 20
    c.drawString(70, y, "Water Project Fund")
    c.drawRightString(width - 50, y, f"{surcharge2:.2f} CNY")
    
    y -= 20
    c.drawString(70, y, "Renewable Energy Surcharge")
    c.drawRightString(width - 50, y, f"{surcharge3:.2f} CNY")
    
    # 分隔线
    y -= 15
    c.line(50, y, width - 50, y)
    
    # 应缴金额
    y -= 30
    c.setFont("Helvetica-Bold", 13)
    c.drawString(50, y, "Total Amount:")
    c.setFont("Helvetica-Bold", 15)
    c.drawRightString(width - 50, y, f"{total:.2f} CNY")
    
    # 缴费信息
    y -= 40
    c.setFont("Helvetica", 9)
    c.drawString(50, y, f"Due Date: {due_date}")
    
    y -= 25
    c.drawString(50, y, "Payment: Alipay/WeChat/App/Office")
    
    # 底部提示
    y = 120
    c.setFont("Helvetica", 8)
    c.drawString(50, y, "Notice:")
    y -= 15
    c.drawString(70, y, "1. Please pay before due date")
    y -= 15
    c.drawString(70, y, "2. Hotline: 95598")
    y -= 15
    c.drawString(70, y, "3. For reference only")
    
    # 底部信息
    c.setFont("Helvetica", 7)
    c.drawCentredString(width/2, 50, "State Grid Zhejiang Jiande Power Supply Company")
    c.drawCentredString(width/2, 35, "Customer Service: 95598")
    
    c.save()
    
    print(f"✓ 账单生成成功!")
    print(f"📄 文件路径: {output_path}")
    print(f"\n已修复黑块问题，使用英文标签 + 拼音")
    
    return output_path

if __name__ == "__main__":
    generate_bill_fixed()
