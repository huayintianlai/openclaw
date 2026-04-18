#!/usr/bin/env python3
"""
完整的公证文件编辑工具 - PhotoshopAPI 版本
编辑 PSD 并导出为 PDF（使用系统工具）
"""
import sys
import os
import subprocess
from datetime import datetime

try:
    import photoshopapi as psapi
except ImportError:
    print("❌ PhotoshopAPI 未安装")
    print("请在虚拟环境中运行:")
    print("  source photoshop_env/bin/activate")
    print("  pip install PhotoshopAPI")
    sys.exit(1)

class CertificateEditorComplete:
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

    def edit_psd(self, psd_path, company_name, address, date, output_psd_path):
        """编辑 PSD 文件"""
        print(f"\n{'='*60}")
        print(f"  步骤 1: 编辑 PSD 文件")
        print(f"{'='*60}")

        if not os.path.exists(psd_path):
            print(f"❌ 错误: 文件不存在 - {psd_path}")
            return None

        print("⏳ 正在加载 PSD 文件...")
        try:
            layered_file = psapi.LayeredFile.read(psd_path)
            print(f"✅ 加载成功")
        except Exception as e:
            print(f"❌ 加载失败: {e}")
            return None

        # 定义需要修改的图层
        layers_to_edit = [
            {'name': '公司名称', 'new_text': company_name},
            {'name': '公司地址', 'new_text': address},
            {'name': '资本存款时间', 'new_text': self.format_date(date)},
            {'name': '落款时间', 'new_text': f"Le {self.format_date(date)}."},
        ]

        print("✏️  正在修改文本图层...")

        for layer_info in layers_to_edit:
            layer = self.find_layer_by_name(layered_file, layer_info['name'])

            if not layer:
                print(f"   ⚠️  未找到图层: {layer_info['name']}")
                continue

            if not isinstance(layer, (psapi.TextLayer_8bit, psapi.TextLayer_16bit, psapi.TextLayer_32bit)):
                print(f"   ⚠️  图层不是文本图层: {layer_info['name']}")
                continue

            original_text = layer.text
            new_text = layer_info['new_text']

            print(f"   • {layer_info['name']}: {original_text} → {new_text}")

            try:
                layer.replace_text(original_text, new_text)
            except Exception as e:
                print(f"     ❌ 修改失败: {e}")

        print(f"\n💾 正在保存 PSD...")
        try:
            layered_file.write(output_psd_path)
            print(f"✅ PSD 保存成功: {output_psd_path}")
            return output_psd_path
        except Exception as e:
            print(f"❌ 保存失败: {e}")
            return None

    def psd_to_pdf_sips(self, psd_path, pdf_path):
        """使用 macOS sips 工具将 PSD 转换为 PDF"""
        print(f"\n{'='*60}")
        print(f"  步骤 2: 转换为 PDF (使用 sips)")
        print(f"{'='*60}")

        try:
            # 先转换为 PNG
            temp_png = pdf_path.replace('.pdf', '_temp.png')
            print(f"⏳ 转换 PSD → PNG...")

            result = subprocess.run(
                ['sips', '-s', 'format', 'png', psd_path, '--out', temp_png],
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                print(f"❌ PNG 转换失败: {result.stderr}")
                return None

            print(f"✅ PNG 生成成功")

            # 再转换为 PDF
            print(f"⏳ 转换 PNG → PDF...")
            result = subprocess.run(
                ['sips', '-s', 'format', 'pdf', temp_png, '--out', pdf_path],
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                print(f"❌ PDF 转换失败: {result.stderr}")
                return None

            # 删除临时文件
            if os.path.exists(temp_png):
                os.remove(temp_png)

            print(f"✅ PDF 生成成功: {pdf_path}")
            return pdf_path

        except Exception as e:
            print(f"❌ 转换失败: {e}")
            return None

    def process(self, psd_path, company_name, address, date, output_pdf_path=None):
        """完整流程：编辑 PSD + 转换为 PDF"""
        print(f"\n{'='*60}")
        print(f"  公证文件编辑工具 - PhotoshopAPI 完整版")
        print(f"{'='*60}")
        print(f"📄 源文件: {os.path.basename(psd_path)}")
        print(f"🏢 公司名称: {company_name}")
        print(f"📍 公司地址: {address}")
        print(f"📅 日期: {date} → {self.format_date(date)}")
        print(f"{'='*60}")

        # 生成输出路径
        base_name = os.path.splitext(os.path.basename(psd_path))[0]
        safe_company_name = company_name.replace(' ', '_').replace('/', '_')

        temp_psd = os.path.join(self.workspace, f"{base_name}_{safe_company_name}_temp.psd")

        if output_pdf_path is None:
            output_pdf_path = f"/Users/xiaojiujiu2/Downloads/{base_name}_{safe_company_name}.pdf"

        # 步骤 1: 编辑 PSD
        result_psd = self.edit_psd(psd_path, company_name, address, date, temp_psd)
        if not result_psd:
            return None

        # 步骤 2: 转换为 PDF
        result_pdf = self.psd_to_pdf_sips(temp_psd, output_pdf_path)
        if not result_pdf:
            return None

        print(f"\n{'='*60}")
        print(f"✅ 全部完成！")
        print(f"{'='*60}")
        print(f"📄 PSD 文件: {temp_psd}")
        print(f"📄 PDF 文件: {output_pdf_path}")
        print(f"   文件大小: {os.path.getsize(output_pdf_path):,} 字节")
        print(f"{'='*60}\n")

        return output_pdf_path

def main():
    editor = CertificateEditorComplete()

    if len(sys.argv) >= 5:
        psd_path = sys.argv[1]
        company_name = sys.argv[2]
        address = sys.argv[3]
        date = sys.argv[4]
        output_pdf = sys.argv[5] if len(sys.argv) > 5 else None

        result = editor.process(psd_path, company_name, address, date, output_pdf)
        sys.exit(0 if result else 1)
    else:
        print("用法: python3 certificate_editor_complete.py <psd文件> <公司名> <地址> <日期> [pdf输出路径]")
        print("\n示例:")
        print('  python3 certificate_editor_complete.py \\')
        print('    "/Users/xiaojiujiu2/Downloads/资本存款.psd" \\')
        print('    "HavenVine SARL" \\')
        print('    "47 rue Vivienne 75002 Paris" \\')
        print('    "2026-03-10"')
        sys.exit(1)

if __name__ == "__main__":
    main()
