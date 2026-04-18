#!/usr/bin/env python3
"""
PSD 转 PDF - 使用 PhotoshopAPI 渲染并转换
"""
import sys
import os

try:
    import photoshopapi as psapi
    from PIL import Image
    import img2pdf
except ImportError as e:
    print(f"❌ 缺少依赖: {e}")
    print("请运行: pip install PhotoshopAPI Pillow img2pdf")
    sys.exit(1)

def psd_to_pdf(psd_path, pdf_path=None):
    """将 PSD 文件转换为 PDF"""
    print(f"\n{'='*60}")
    print(f"  PSD 转 PDF")
    print(f"{'='*60}")
    print(f"📄 输入: {psd_path}")

    if not os.path.exists(psd_path):
        print(f"❌ 文件不存在")
        return None

    # 读取 PSD
    print("⏳ 正在读取 PSD...")
    try:
        layered_file = psapi.LayeredFile.read(psd_path)
        print(f"✅ 读取成功")
    except Exception as e:
        print(f"❌ 读取失败: {e}")
        return None

    # 渲染为图像
    print("⏳ 正在渲染图像...")
    try:
        # 获取合成图像
        image_data = layered_file.get_image_data()

        # 转换为 PIL Image
        import numpy as np
        height, width, channels = image_data.shape

        # PhotoshopAPI 返回的是 float32 [0, 1] 范围
        image_data_uint8 = (image_data * 255).astype(np.uint8)

        image = Image.fromarray(image_data_uint8, mode='RGB')
        print(f"✅ 渲染成功 ({width}x{height})")
    except Exception as e:
        print(f"❌ 渲染失败: {e}")
        import traceback
        traceback.print_exc()
        return None

    # 保存为 PDF
    if pdf_path is None:
        pdf_path = psd_path.replace('.psd', '.pdf')

    print(f"⏳ 正在转换为 PDF...")
    print(f"   输出: {pdf_path}")

    try:
        # 先保存为临时 PNG
        temp_png = pdf_path.replace('.pdf', '_temp.png')
        image.save(temp_png, 'PNG', dpi=(300, 300))

        # 转换为 PDF
        with open(pdf_path, 'wb') as f:
            f.write(img2pdf.convert(temp_png, dpi=300))

        # 删除临时文件
        os.remove(temp_png)

        print(f"✅ 转换成功")
        print(f"   文件大小: {os.path.getsize(pdf_path):,} 字节")
        print(f"   路径: {pdf_path}\n")
        return pdf_path

    except Exception as e:
        print(f"❌ 转换失败: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    if len(sys.argv) >= 2:
        psd_path = sys.argv[1]
        pdf_path = sys.argv[2] if len(sys.argv) > 2 else None

        result = psd_to_pdf(psd_path, pdf_path)
        sys.exit(0 if result else 1)
    else:
        print("用法: python3 psd_to_pdf.py <psd文件> [pdf输出路径]")
        sys.exit(1)

if __name__ == "__main__":
    main()
