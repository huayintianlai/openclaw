#!/usr/bin/env python3
"""
详细分析 PSD 文件的字体信息
"""
from psd_tools import PSDImage
import json

psd = PSDImage.open("/Users/xiaojiujiu2/Downloads/资本存款.psd")

print("="*80)
print("详细字体分析")
print("="*80)

for i, layer in enumerate(psd.descendants()):
    if layer.kind == 'type' and hasattr(layer, 'text'):
        print(f"\n图层 #{i}: {layer.name}")
        print(f"文本: {repr(layer.text[:50])}")

        # 详细的字体信息
        if hasattr(layer, 'engine_dict'):
            engine = layer.engine_dict
            print(f"\n完整 engine_dict:")
            print(json.dumps(engine, indent=2, default=str))
