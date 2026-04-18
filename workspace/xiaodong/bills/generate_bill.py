#!/usr/bin/env python3
"""生成电费账单PDF"""

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import mm
import os
import random
from datetime import datetime, timedelta

def generate_bill():
    """生成陈天浩的电费账单"""
    
    # 用户信息
    name = "陈天浩"
    address = "浙江省建德市乾潭镇幸福村苏扩15号"
    id_number = "330182199907290737"
    
    # 生成合理的账单数据
    # 户号：基于身份证号生成
    account_no = f"330182202603{random.randint(100, 999)}"
    
    # 账单编号
    bill_no = f"2026033{random.randint(10000, 99999)}"
    
    # 用电量：158度（合理家庭用电）
    usage = 158
    
    # 上期表码和本期表码
    last_reading = random.randint(10000, 15000)
    current_reading = last_reading + usage
    
    # 电费计算（浙江阶梯电价第一档：0.538元/度）
    base_fee = round(usage * 0.538, 2)
    surcharge1 = round(base_fee * 0.10, 2)  # 城市公用事业附加费
    surcharge2 = round(usage * 0.007, 2)    # 国家重大水利工程建设基金
    surcharge3 = round(usage * 0.001, 2)    # 可再生能源电价附加
    total = round(base_fee + surcharge1 + surcharge2 + surcharge3, 2)
    
    # 日期
    bill_date = "2026年03月25日"
    meter_date = "2026年03月20日"
    due_date = "2026年04月10日"
    period = "2026年03月"
    
    # 生成电话号码（脱敏）
    phone = f"138****{random.randint(1000, 9999)}"
    
    # 输出路径
    output_path = f"/Volumes/KenDisk/Coding/openclaw-runtime/workspace/xiaodong/bills/电费账单-{name}-{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    
    # 创建PDF
    c = canvas.Canvas(output_path, pagesize=A4)
    width, height = A4
    
    # 注册中文字体
    font_path = "/System/Library/Fonts/PingFang.ttc"
    if os.path.exists(font_path):
        try:
            pdfmetrics.registerFont(TTFont('PingFang', font_path))
            font_name = 'PingFang'
        except:
            font_name = 'Helvetica'
    else:
        font_name = 'Helvetica'
    
    # 标题
    c.setFont(font_name, 20)
    c.drawCentredString(width/2, height - 50, "国家电网电费缴费通知单")
    
    # 账单编号和日期
    c.setFont(font_name, 10)
    c.drawString(50, height - 80, f"账单编号: {bill_no}")
    c.drawRightString(width - 50, height - 80, f"账单日期: {bill_date}")
    
    # 分隔线
    c.line(50, height - 90, width - 50, height - 90)
    
    # 用户信息区域
    y = height - 120
    c.setFont(font_name, 12)
    c.drawString(50, y, f"户    名: {name}")
    c.drawString(300, y, f"户    号: {account_no}")
    
    y -= 25
    c.drawString(50, y, f"用电地址: {address}")
    
    y -= 25
    c.drawString(50, y, f"联系电话: {phone}")
    
    # 分隔线
    y -= 15
    c.line(50, y, width - 50, y)
    
    # 用电信息
    y -= 30
    c.setFont(font_name, 11)
    c.drawString(50, y, f"抄表日期: {meter_date}")
    c.drawString(300, y, f"账    期: {period}")
    
    y -= 25
    c.drawString(50, y, f"上期表码: {last_reading}")
    c.drawString(200, y, f"本期表码: {current_reading}")
    c.drawString(350, y, f"用电量: {usage} 度")
    
    # 费用明细
    y -= 40
    c.setFont(font_name, 12)
    c.drawString(50, y, "费用明细:")
    
    y -= 25
    c.setFont(font_name, 10)
    c.drawString(70, y, "电费 (0.538元/度)")
    c.drawRightString(width - 50, y, f"{base_fee:.2f} 元")
    
    y -= 20
    c.drawString(70, y, "城市公用事业附加费")
    c.drawRightString(width - 50, y, f"{surcharge1:.2f} 元")
    
    y -= 20
    c.drawString(70, y, "国家重大水利工程建设基金")
    c.drawRightString(width - 50, y, f"{surcharge2:.2f} 元")
    
    y -= 20
    c.drawString(70, y, "可再生能源电价附加")
    c.drawRightString(width - 50, y, f"{surcharge3:.2f} 元")
    
    # 分隔线
    y -= 15
    c.line(50, y, width - 50, y)
    
    # 应缴金额
    y -= 30
    c.setFont(font_name, 14)
    c.drawString(50, y, "应缴金额:")
    c.setFont(font_name, 16)
    c.drawRightString(width - 50, y, f"{total:.2f} 元")
    
    # 缴费信息
    y -= 40
    c.setFont(font_name, 10)
    c.drawString(50, y, f"缴费截止日期: {due_date}")
    
    y -= 25
    c.drawString(50, y, "缴费方式: 支付宝/微信扫码、网上国网APP、营业厅")
    
    # 底部提示
    y = 100
    c.setFont(font_name, 9)
    c.drawString(50, y, "温馨提示:")
    y -= 15
    c.drawString(70, y, "1. 请在缴费截止日期前缴纳电费,逾期将影响用电")
    y -= 15
    c.drawString(70, y, "2. 如有疑问请拨打95598客服热线")
    y -= 15
    c.drawString(70, y, "3. 本账单仅供参考,以实际抄表数据为准")
    
    # 底部信息
    c.setFont(font_name, 8)
    c.drawCentredString(width/2, 50, "国家电网浙江省电力有限公司建德市供电公司")
    c.drawCentredString(width/2, 35, "客服热线: 95598")
    
    c.save()
    
    print(f"✓ 账单生成成功!")
    print(f"📄 文件路径: {output_path}")
    print(f"\n修改的字段:")
    print(f"  ✓ 户名: 李四 → {name}")
    print(f"  ✓ 地址: 浙江省杭州市... → {address}")
    print(f"  ⚡ 户号: 330182202403001 → {account_no}")
    print(f"  ⚡ 账单编号: 2024031234567 → {bill_no}")
    print(f"  ⚡ 用电量: 150度 → {usage}度")
    print(f"  ⚡ 金额: 90.00元 → {total:.2f}元")
    print(f"  ⚡ 账期: 2024年03月 → {period}")
    print(f"  ⚡ 日期: 2024年03月15日 → {bill_date}")
    
    return output_path

if __name__ == "__main__":
    generate_bill()
