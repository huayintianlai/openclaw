#!/usr/bin/env python3
"""生成国家电网电费账单PDF模板"""

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import mm
import os

def create_electric_bill_template():
    """创建电费账单模板"""
    
    # 输出路径
    output_path = "/Volumes/KenDisk/Coding/openclaw-runtime/workspace/xiaodong/bills/templates/电费账单模板.pdf"
    
    # 创建PDF
    c = canvas.Canvas(output_path, pagesize=A4)
    width, height = A4
    
    # 注册中文字体（使用系统字体）
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
    c.drawString(50, height - 80, "账单编号: 2024031234567")
    c.drawRightString(width - 50, height - 80, "账单日期: 2024年03月15日")
    
    # 分隔线
    c.line(50, height - 90, width - 50, height - 90)
    
    # 用户信息区域
    y = height - 120
    c.setFont(font_name, 12)
    c.drawString(50, y, "户    名: 李四")
    c.drawString(300, y, "户    号: 330182202403001")
    
    y -= 25
    c.drawString(50, y, "用电地址: 浙江省杭州市西湖区文三路XX号XX室")
    
    y -= 25
    c.drawString(50, y, "联系电话: 138****5678")
    
    # 分隔线
    y -= 15
    c.line(50, y, width - 50, y)
    
    # 用电信息
    y -= 30
    c.setFont(font_name, 11)
    c.drawString(50, y, "抄表日期: 2024年03月10日")
    c.drawString(300, y, "账    期: 2024年03月")
    
    y -= 25
    c.drawString(50, y, "上期表码: 12345")
    c.drawString(200, y, "本期表码: 12495")
    c.drawString(350, y, "用电量: 150 度")
    
    # 费用明细
    y -= 40
    c.setFont(font_name, 12)
    c.drawString(50, y, "费用明细:")
    
    y -= 25
    c.setFont(font_name, 10)
    c.drawString(70, y, "电费 (0.538元/度)")
    c.drawRightString(width - 50, y, "80.70 元")
    
    y -= 20
    c.drawString(70, y, "城市公用事业附加费")
    c.drawRightString(width - 50, y, "8.07 元")
    
    y -= 20
    c.drawString(70, y, "国家重大水利工程建设基金")
    c.drawRightString(width - 50, y, "1.05 元")
    
    y -= 20
    c.drawString(70, y, "可再生能源电价附加")
    c.drawRightString(width - 50, y, "0.18 元")
    
    # 分隔线
    y -= 15
    c.line(50, y, width - 50, y)
    
    # 应缴金额
    y -= 30
    c.setFont(font_name, 14)
    c.drawString(50, y, "应缴金额:")
    c.setFont(font_name, 16)
    c.drawRightString(width - 50, y, "90.00 元")
    
    # 缴费信息
    y -= 40
    c.setFont(font_name, 10)
    c.drawString(50, y, "缴费截止日期: 2024年03月30日")
    
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
    c.drawCentredString(width/2, 50, "国家电网浙江省电力有限公司")
    c.drawCentredString(width/2, 35, "客服热线: 95598")
    
    c.save()
    print(f"✓ 模板已生成: {output_path}")
    return output_path

if __name__ == "__main__":
    create_electric_bill_template()
