#!/usr/bin/env python3
"""
公证文件编辑器 - PhotoshopAPI 版本
使用 PhotoshopAPI 完美保留所有 Photoshop 样式（FauxBold, Tracking 等）
"""
import sys
import os
from datetime import datetime

try:
    import photoshopapi as psapi
except ImportError:
    print("❌ PhotoshopAPI 未安装")
    print("请运行: python3 -m pip install PhotoshopAPI")
    sys.exit(1)

class PhotoshopAPICertificateEditor:
    def __init__(self):
        self.workspace = "/Volumes/KenDisk/Coding/openclaw-runtime/workspace"

        self.months_fr = {
            1: 'janvier', 2: 'février', 3: 'mars', 4: 'avril',
            5: 'mai', 6: 'juin', 7: 'juillet', 8: 'août',
            9: 'septembre', 10: 'octobre', 11: 'novembre', 12: 'décembre'
        }

    def format_date(self, date_str):
        """将日期从 YYYY-MM-DD 格式转换为法文格式"""
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        return f"{date_obj.day} {self.months_fr[date_obj.month]} {date_obj.year}"

    def find_layer_by_name(self, layered_file, layer_name):
        """根据图层名称查找图层"""
        for layer in layered_file.flat_layers:
            if hasattr(layer, 'name') and layer.name == layer_name:
                return layer
        return None

    def edit_certificate(self, psd_path, company_name, address, date, output_path=None):
        """编辑公证文件"""
        print(f"\n{'='*60}")
        print(f"  公证文件编辑工具 - PhotoshopAPI 版")
        print(f"{'='*60}")
        print(f"📄 源文件: {os.path.basename(psd_path)}")
        print(f"🏢 公司名称: {company_name}")
        print(f"📍 公司地址: {address}")
        print(f"📅 日期: {date} → {self.format_date(date)}")
        print(f"{'='*60}\n")

        if not os.path.exists(psd_path):
            print(f"❌ 错误: 文件不存在 - {psd_path}")
            return None

        print("⏳ 正在加载 PSD 文件...")
        try:
            layered_file = psapi.LayeredFile.read(psd_path)
            print(f"✅ 加载成功 (共 {len(layered_file.flat_layers)} 个图层)")
        except Exception as e:
            print(f"❌ 加载失败: {e}")
            return None

        # 定义需要修改的图层
        layers_to_edit = [
            {
                'name': '公司名称',
                'new_text': company_name,
            },
            {
                'name': '公司地址',
                'new_text': address,
            },
            {
                'name': '资本存款时间',
                'new_text': self.format_date(date),
            },
            {
                'name': '落款时间',
                'new_text': f"Le {self.format_date(date)}.",
            }
        ]

        print("✏️  正在修改文本图层...")

        for layer_info in layers_to_edit:
            layer_name = layer_info['name']
            new_text = layer_info['new_text']

            # 查找图层
            layer = self.find_layer_by_name(layered_file, layer_name)

            if not layer:
                print(f"   ⚠️  未找到图层: {layer_name}")
                continue

            if not isinstance(layer, (psapi.TextLayer_8bit, psapi.TextLayer_16bit, psapi.TextLayer_32bit)):
                print(f"   ⚠️  图层不是文本图层: {layer_name}")
                continue

            # 保存原始样式信息（用于验证）
            original_text = layer.text
            original_faux_bold = layer.style_run_faux_bold(0) if hasattr(layer, 'style_run_faux_bold') else None
            original_tracking = layer.style_run_tracking(0) if hasattr(layer, 'style_run_tracking') else None

            print(f"   • {layer_name}")
            print(f"     原文本: {original_text}")
            print(f"     新文本: {new_text}")

            # 使用 replace_text 完全替换文本（保留所有样式）
            try:
                layer.replace_text(original_text, new_text)

                # 验证样式是否保留
                new_faux_bold = layer.style_run_faux_bold(0) if hasattr(layer, 'style_run_faux_bold') else None
                new_tracking = layer.style_run_tracking(0) if hasattr(layer, 'style_run_tracking') else None

                if original_faux_bold == new_faux_bold and original_tracking == new_tracking:
                    print(f"     ✅ 样式完整保留 (FauxBold: {new_faux_bold}, Tracking: {new_tracking})")
                else:
                    print(f"     ⚠️  样式可能改变")

            except Exception as e:
                print(f"     ❌ 修改失败: {e}")

        # 保存结果
        if output_path is None:
            base_name = os.path.splitext(os.path.basename(psd_path))[0]
            safe_company_name = company_name.replace(' ', '_').replace('/', '_')
            output_path = os.path.join(self.workspace, f"{base_name}_{safe_company_name}_photoshopapi.psd")

        print(f"\n💾 正在保存文件...")
        print(f"   输出路径: {output_path}")

        try:
            layered_file.write(output_path)

            if os.path.exists(output_path):
                file_size = os.path.getsize(output_path)
                print(f"✅ 完成！文件已保存")
                print(f"   文件大小: {file_size:,} 字节")
                print(f"   路径: {output_path}\n")
                return output_path
            else:
                print(f"❌ 保存失败: 文件未创建")
                return None

        except Exception as e:
            print(f"❌ 保存失败: {e}")
            import traceback
            traceback.print_exc()
            return None

def main():
    editor = PhotoshopAPICertificateEditor()

    if len(sys.argv) >= 5:
        psd_path = sys.argv[1]
        company_name = sys.argv[2]
        address = sys.argv[3]
        date = sys.argv[4]
        output_path = sys.argv[5] if len(sys.argv) > 5 else None

        result = editor.edit_certificate(psd_path, company_name, address, date, output_path)

        if result:
            sys.exit(0)
        else:
            sys.exit(1)
    else:
        print("用法: python3 certificate_editor_photoshopapi.py <psd文件> <公司名> <地址> <日期> [输出路径]")
        print("\n示例:")
        print('  python3 certificate_editor_photoshopapi.py \\')
        print('    "/Users/xiaojiujiu2/Downloads/资本存款.psd" \\')
        print('    "HavenVine SARL" \\')
        print('    "47 rue Vivienne 75002 Paris" \\')
        print('    "2026-03-10"')
        sys.exit(1)

if __name__ == "__main__":
    main()
