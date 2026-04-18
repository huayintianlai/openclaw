#!/usr/bin/env python3
"""
PSD 文件分析工具 - 读取 PSD 文件结构和文本图层信息
"""
import sys
from psd_tools import PSDImage

def analyze_psd(psd_path):
    """分析 PSD 文件结构"""
    print(f"正在分析: {psd_path}\n")

    # 打开 PSD 文件
    psd = PSDImage.open(psd_path)

    print(f"文件尺寸: {psd.width} x {psd.height}")
    print(f"颜色模式: {psd.color_mode}")
    print(f"图层数量: {len(list(psd.descendants()))}\n")

    print("=" * 80)
    print("文本图层列表:")
    print("=" * 80)

    # 遍历所有图层
    for i, layer in enumerate(psd.descendants()):
        if layer.kind == 'type':  # 文本图层
            print(f"\n图层 #{i}: {layer.name}")
            print(f"  可见: {layer.visible}")
            print(f"  位置: ({layer.left}, {layer.top})")
            print(f"  尺寸: {layer.width} x {layer.height}")

            # 获取文本内容
            if hasattr(layer, 'text'):
                text = layer.text
                print(f"  文本内容: {repr(text[:100])}..." if len(text) > 100 else f"  文本内容: {repr(text)}")

            # 获取字体信息
            if hasattr(layer, 'engine_dict'):
                engine = layer.engine_dict
                if 'StyleRun' in engine and 'RunArray' in engine['StyleRun']:
                    for run in engine['StyleRun']['RunArray']:
                        if 'StyleSheet' in run and 'StyleSheetData' in run['StyleSheet']:
                            style = run['StyleSheet']['StyleSheetData']
                            if 'Font' in style:
                                print(f"  字体: {style['Font']}")
                            if 'FontSize' in style:
                                print(f"  字号: {style['FontSize']}")
                            if 'FillColor' in style:
                                print(f"  颜色: {style['FillColor']}")
                            break

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python3 psd_analyzer.py <psd文件路径>")
        sys.exit(1)

    analyze_psd(sys.argv[1])
