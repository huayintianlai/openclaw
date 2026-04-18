#!/usr/bin/env python3
"""
PhotoshopAPI POC - 测试是否能完美编辑 PSD 文本图层
目标：验证 PhotoshopAPI 能否保留 FauxBold 和 Tracking 等样式
"""
import sys
import os

# 等待 PhotoshopAPI 安装完成
print("等待 PhotoshopAPI 安装完成...")
import time
time.sleep(5)

try:
    import photoshopapi as psapi
    print("✅ PhotoshopAPI 导入成功")
except ImportError as e:
    print(f"❌ PhotoshopAPI 导入失败: {e}")
    print("请等待安装完成后重试")
    sys.exit(1)

def test_read_psd():
    """测试读取 PSD 文件"""
    psd_path = "/Users/xiaojiujiu2/Downloads/资本存款.psd"

    if not os.path.exists(psd_path):
        print(f"❌ 文件不存在: {psd_path}")
        return None

    print(f"\n📄 正在读取 PSD 文件: {psd_path}")

    try:
        layered_file = psapi.LayeredFile.read(psd_path)
        print(f"✅ PSD 文件读取成功")
        print(f"   - 图层数量: {len(layered_file.flat_layers)}")
        return layered_file
    except Exception as e:
        print(f"❌ 读取失败: {e}")
        return None

def find_text_layers(layered_file):
    """查找所有文本图层"""
    print("\n🔍 查找文本图层...")
    text_layers = []

    for layer in layered_file.flat_layers:
        # 检查是否是文本图层
        if isinstance(layer, (psapi.TextLayer_8bit, psapi.TextLayer_16bit, psapi.TextLayer_32bit)):
            text = layer.text if hasattr(layer, 'text') else None
            name = layer.name if hasattr(layer, 'name') else "Unknown"
            print(f"   • 找到文本图层: {name}")
            if text:
                print(f"     内容: {text[:50]}...")
            text_layers.append(layer)

    print(f"\n✅ 共找到 {len(text_layers)} 个文本图层")
    return text_layers

def inspect_text_layer(layer):
    """详细检查文本图层的样式信息"""
    print(f"\n📋 检查图层: {layer.name}")
    print(f"   文本内容: {layer.text}")

    # 检查字体信息
    if hasattr(layer, 'font_count'):
        print(f"   字体数量: {layer.font_count}")
        for i in range(layer.font_count):
            font_name = layer.font_postscript_name(i)
            print(f"     字体 {i}: {font_name}")

    # 检查样式运行
    if hasattr(layer, 'style_run_count'):
        print(f"   样式运行数量: {layer.style_run_count}")
        for i in range(min(3, layer.style_run_count)):  # 只显示前3个
            font_size = layer.style_run_font_size(i) if hasattr(layer, 'style_run_font_size') else None
            faux_bold = layer.style_run_faux_bold(i) if hasattr(layer, 'style_run_faux_bold') else None
            tracking = layer.style_run_tracking(i) if hasattr(layer, 'style_run_tracking') else None

            print(f"     样式 {i}:")
            if font_size is not None:
                print(f"       字号: {font_size}")
            if faux_bold is not None:
                print(f"       伪粗体: {faux_bold}")
            if tracking is not None:
                print(f"       字间距: {tracking}")

def main():
    print("="*60)
    print("  PhotoshopAPI POC 测试")
    print("="*60)

    # 1. 读取 PSD
    layered_file = test_read_psd()
    if not layered_file:
        return

    # 2. 查找文本图层
    text_layers = find_text_layers(layered_file)
    if not text_layers:
        print("❌ 未找到文本图层")
        return

    # 3. 检查第一个文本图层的详细信息
    if text_layers:
        inspect_text_layer(text_layers[0])

    print("\n" + "="*60)
    print("✅ POC 测试完成")
    print("="*60)

if __name__ == "__main__":
    main()
