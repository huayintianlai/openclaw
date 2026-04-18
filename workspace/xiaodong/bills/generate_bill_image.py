#!/usr/bin/env python3
"""生成电费账单 - 图片转PDF方式"""

from PIL import Image, ImageDraw, ImageFont
import random
from datetime import datetime

def generate_bill_as_image():
    """生成电费账单 - 先生成图片再转PDF"""
    
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
    
    # 创建白色背景图片 (A4比例: 210mm x 297mm = 2480 x 3508 pixels at 300dpi)
    width, height = 2480, 3508
    img = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(img)
    
    # 加载中文字体
    try:
        font_title = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", 80)
        font_large = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", 60)
        font_medium = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", 48)
        font_normal = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", 40)
        font_small = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", 32)
    except:
        # 如果加载失败，使用默认字体
        font_title = ImageFont.load_default()
        font_large = font_medium = font_normal = font_small = font_title
    
    # 标题
    y = 150
    title = "国家电网电费缴费通知单"
    bbox = draw.textbbox((0, 0), title, font=font_title)
    title_width = bbox[2] - bbox[0]
    draw.text((width//2 - title_width//2, y), title, fill='black', font=font_title)
    
    # 账单编号和日期
    y = 280
    draw.text((150, y), f"账单编号: {bill_no}", fill='black', font=font_small)
    date_text = f"账单日期: {bill_date}"
    bbox = draw.textbbox((0, 0), date_text, font=font_small)
    date_width = bbox[2] - bbox[0]
    draw.text((width - 150 - date_width, y), date_text, fill='black', font=font_small)
    
    # 分隔线
    y = 350
    draw.line([(150, y), (width - 150, y)], fill='black', width=2)
    
    # 用户信息
    y = 420
    draw.text((150, y), f"户    名: {name}", fill='black', font=font_normal)
    draw.text((1200, y), f"户    号: {account_no}", fill='black', font=font_normal)
    
    y += 80
    draw.text((150, y), f"用电地址: {address}", fill='black', font=font_normal)
    
    y += 80
    draw.text((150, y), f"联系电话: {phone}", fill='black', font=font_normal)
    
    # 分隔线
    y += 60
    draw.line([(150, y), (width - 150, y)], fill='black', width=2)
    
    # 用电信息
    y += 80
    draw.text((150, y), f"抄表日期: {meter_date}", fill='black', font=font_normal)
    draw.text((1200, y), f"账    期: {period}", fill='black', font=font_normal)
    
    y += 80
    draw.text((150, y), f"上期表码: {last_reading}", fill='black', font=font_normal)
    draw.text((800, y), f"本期表码: {current_reading}", fill='black', font=font_normal)
    draw.text((1450, y), f"用电量: {usage} 度", fill='black', font=font_normal)
    
    # 费用明细
    y += 120
    draw.text((150, y), "费用明细:", fill='black', font=font_medium)
    
    y += 80
    draw.text((200, y), "电费 (0.538元/度)", fill='black', font=font_normal)
    fee_text = f"{base_fee:.2f} 元"
    bbox = draw.textbbox((0, 0), fee_text, font=font_normal)
    fee_width = bbox[2] - bbox[0]
    draw.text((width - 150 - fee_width, y), fee_text, fill='black', font=font_normal)
    
    y += 70
    draw.text((200, y), "城市公用事业附加费", fill='black', font=font_normal)
    fee_text = f"{surcharge1:.2f} 元"
    bbox = draw.textbbox((0, 0), fee_text, font=font_normal)
    fee_width = bbox[2] - bbox[0]
    draw.text((width - 150 - fee_width, y), fee_text, fill='black', font=font_normal)
    
    y += 70
    draw.text((200, y), "国家重大水利工程建设基金", fill='black', font=font_normal)
    fee_text = f"{surcharge2:.2f} 元"
    bbox = draw.textbbox((0, 0), fee_text, font=font_normal)
    fee_width = bbox[2] - bbox[0]
    draw.text((width - 150 - fee_width, y), fee_text, fill='black', font=font_normal)
    
    y += 70
    draw.text((200, y), "可再生能源电价附加", fill='black', font=font_normal)
    fee_text = f"{surcharge3:.2f} 元"
    bbox = draw.textbbox((0, 0), fee_text, font=font_normal)
    fee_width = bbox[2] - bbox[0]
    draw.text((width - 150 - fee_width, y), fee_text, fill='black', font=font_normal)
    
    # 分隔线
    y += 60
    draw.line([(150, y), (width - 150, y)], fill='black', width=2)
    
    # 应缴金额
    y += 80
    draw.text((150, y), "应缴金额:", fill='black', font=font_large)
    total_text = f"{total:.2f} 元"
    bbox = draw.textbbox((0, 0), total_text, font=font_large)
    total_width = bbox[2] - bbox[0]
    draw.text((width - 150 - total_width, y), total_text, fill='red', font=font_large)
    
    # 缴费信息
    y += 120
    draw.text((150, y), f"缴费截止日期: {due_date}", fill='black', font=font_normal)
    
    y += 80
    draw.text((150, y), "缴费方式: 支付宝/微信扫码、网上国网APP、营业厅", fill='black', font=font_normal)
    
    # 底部提示
    y = 2900
    draw.text((150, y), "温馨提示:", fill='black', font=font_small)
    y += 50
    draw.text((200, y), "1. 请在缴费截止日期前缴纳电费,逾期将影响用电", fill='black', font=font_small)
    y += 50
    draw.text((200, y), "2. 如有疑问请拨打95598客服热线", fill='black', font=font_small)
    y += 50
    draw.text((200, y), "3. 本账单仅供参考,以实际抄表数据为准", fill='black', font=font_small)
    
    # 底部信息
    y = 3300
    company = "国家电网浙江省电力有限公司建德市供电公司"
    bbox = draw.textbbox((0, 0), company, font=font_small)
    company_width = bbox[2] - bbox[0]
    draw.text((width//2 - company_width//2, y), company, fill='black', font=font_small)
    
    y += 50
    hotline = "客服热线: 95598"
    bbox = draw.textbbox((0, 0), hotline, font=font_small)
    hotline_width = bbox[2] - bbox[0]
    draw.text((width//2 - hotline_width//2, y), hotline, fill='black', font=font_small)
    
    # 保存为图片
    img_path = f"/Volumes/KenDisk/Coding/openclaw-runtime/workspace/xiaodong/bills/电费账单-{name}-{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    img.save(img_path, 'PNG', dpi=(300, 300))
    
    # 转换为PDF
    pdf_path = img_path.replace('.png', '.pdf')
    img_rgb = img.convert('RGB')
    img_rgb.save(pdf_path, 'PDF', resolution=300.0)
    
    print(f"✓ 账单生成成功!")
    print(f"📄 PDF文件: {pdf_path}")
    print(f"🖼️  图片文件: {img_path}")
    print(f"\n已使用图片方式生成，完全避免黑块问题")
    
    return pdf_path

if __name__ == "__main__":
    generate_bill_as_image()
