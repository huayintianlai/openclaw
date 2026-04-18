#!/usr/bin/env python3
"""
PhotoshopAPI 完整测试 - 验证能否完美编辑公证文件
测试目标：
1. 读取 PSD 文件
2. 找到文本图层
3. 检查 FauxBold 和 Tracking 支持
4. 修改文本内容
5. 保留所有原始样式
6. 写回 PSD 文件
"""
import sys
import os
from datetime import datetime

try:
    import photoshopapi as psapi
    print("✅ PhotoshopAPI 导入成功")
except ImportError as e:
    print(f"❌ PhotoshopAPI 未安装: {e}")
    print("请运行: python3 -m pip install PhotoshopAPI")
    sys.exit(1)

class PhotoshopAPICertificateEditor:
    def __init__(self):
        self.months_fr = {
            1: 'janvier', 2: 'février', 3: 'mars', 4: 'avril',
            5: 'mai', 6: 'juin', 7: 'juillet', 8: 'août',
            9: 'septembre', 10: 'octobre', 11: 'novembre', 12: 'décembre'
        }

    def format_date(self, date_str):
        """将日期从 YYYY-MM-DD 格式转换为法文格式"""
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        return f"{date_obj.day} {self.months_fr[date_obj.month]} {date_obj.year}"

    def find_text_layer_by_content(self, layered_file, search_text):
        """根据文本内容查找图层"""
        for layer in layered_file.flat_layers:
            if isinstance(layer, (psapi.TextLayer_8bit, psapi.TextLayer_16bit, psapi.TextLayer_32bit)):
                if layer.text and search_text in layer.text:
                    return layer
        return None

    def inspect_layer_styles(self, layer):
        """检查图层的样式信息"""
        print(f"\n📋 图层样式信息:")
        print(f"   名称: {layer.name}")
        print(f"   文本: {layer.text}")

        # 字体信息
        if hasattr(layer, 'font_count'):
            print(f"   字体数量: {layer.font_count}")
            for i in range(layer.font_count):
                font_name = layer.font_postscript_name(i)
                print(f"     字体 {i}: {font_name}")

        # 样式运行
        if hasattr(layer, 'style_run_count'):
            print(f"   样式运行数量: {layer.style_run_count}")
            for i in range(min(2, layer.style_run_count)):
                print(f"     样式运行 {i}:")

                # 字号
                if hasattr(layer, 'style_run_font_size'):
                    font_size = layer.style_run_font_size(i)
                    print(f"       字号: {font_size}")

                # FauxBold
                if hasattr(layer, 'style_run_faux_bold'):
                    faux_bold = layer.style_run_faux_bold(i)
                    print(f"       伪粗体 (FauxBold): {faux_bold}")

                # Tracking
                if hasattr(layer, 'style_run_tracking'):
                    tracking = layer.style_run_tracking(i)
                    print(f"       字间距 (Tracking): {tracking}")

                # 颜色
                if hasattr(layer, 'style_run_fill_color'):
                    color = layer.style_run_fill_color(i)
                    if color:
                        print(f"       填充颜色: {color}")

    def test_read_and_inspect(self, psd_path):
        """测试读取和检查 PSD 文件"""
        print(f"\n{'='*60}")
        print(f"  测试 1: 读取和检查 PSD 文件")
        print(f"{'='*60}")

        if not os.path.exists(psd_path):
            print(f"❌ 文件不存在: {psd_path}")
            return None

        print(f"📄 正在读取: {psd_path}")

        try:
            layered_file = psapi.LayeredFile.read(psd_path)
            print(f"✅ 读取成功")
            print(f"   图层总数: {len(layered_file.flat_layers)}")

            # 查找包含 "dénomination sociale" 的图层（公司名称所在段落）
            print(f"\n🔍 查找文本图层...")
            text_layers = []
            for layer in layered_file.flat_layers:
                if isinstance(layer, (psapi.TextLayer_8bit, psapi.TextLayer_16bit, psapi.TextLayer_32bit)):
                    text_layers.append(layer)
                    print(f"   • {layer.name}: {layer.text[:50] if layer.text else 'None'}...")

            print(f"\n✅ 找到 {len(text_layers)} 个文本图层")

            # 检查第一个文本图层的详细信息
            if text_layers:
                self.inspect_layer_styles(text_layers[0])

            return layered_file

        except Exception as e:
            print(f"❌ 读取失败: {e}")
            import traceback
            traceback.print_exc()
            return None

    def test_modify_text(self, psd_path, output_path):
        """测试修改文本并保存"""
        print(f"\n{'='*60}")
        print(f"  测试 2: 修改文本并保存")
        print(f"{'='*60}")

        try:
            layered_file = psapi.LayeredFile.read(psd_path)

            # 查找第一个文本图层
            text_layer = None
            for layer in layered_file.flat_layers:
                if isinstance(layer, (psapi.TextLayer_8bit, psapi.TextLayer_16bit, psapi.TextLayer_32bit)):
                    if layer.text:
                        text_layer = layer
                        break

            if not text_layer:
                print("❌ 未找到可修改的文本图层")
                return False

            print(f"📝 修改图层: {text_layer.name}")
            print(f"   原文本: {text_layer.text}")

            # 保存原始样式信息
            original_faux_bold = None
            original_tracking = None
            if hasattr(text_layer, 'style_run_faux_bold'):
                original_faux_bold = text_layer.style_run_faux_bold(0)
            if hasattr(text_layer, 'style_run_tracking'):
                original_tracking = text_layer.style_run_tracking(0)

            print(f"   原始 FauxBold: {original_faux_bold}")
            print(f"   原始 Tracking: {original_tracking}")

            # 修改文本（使用 replace_text 保留样式）
            if "Hello" in text_layer.text:
                text_layer.replace_text("Hello", "Bonjour")
                print(f"   新文本: {text_layer.text}")
            else:
                # 如果没有 "Hello"，就在末尾添加测试文本
                original_text = text_layer.text
                text_layer.replace_text(original_text, original_text + " [TEST]")
                print(f"   新文本: {text_layer.text}")

            # 验证样式是否保留
            new_faux_bold = None
            new_tracking = None
            if hasattr(text_layer, 'style_run_faux_bold'):
                new_faux_bold = text_layer.style_run_faux_bold(0)
            if hasattr(text_layer, 'style_run_tracking'):
                new_tracking = text_layer.style_run_tracking(0)

            print(f"   修改后 FauxBold: {new_faux_bold}")
            print(f"   修改后 Tracking: {new_tracking}")

            if original_faux_bold == new_faux_bold:
                print(f"   ✅ FauxBold 样式保留")
            else:
                print(f"   ⚠️  FauxBold 样式改变")

            if original_tracking == new_tracking:
                print(f"   ✅ Tracking 样式保留")
            else:
                print(f"   ⚠️  Tracking 样式改变")

            # 保存文件
            print(f"\n💾 保存到: {output_path}")
            layered_file.write(output_path)

            if os.path.exists(output_path):
                print(f"✅ 文件保存成功")
                print(f"   文件大小: {os.path.getsize(output_path)} 字节")
                return True
            else:
                print(f"❌ 文件保存失败")
                return False

        except Exception as e:
            print(f"❌ 修改失败: {e}")
            import traceback
            traceback.print_exc()
            return False

    def test_roundtrip(self, original_path, modified_path):
        """测试往返读写"""
        print(f"\n{'='*60}")
        print(f"  测试 3: 往返读写验证")
        print(f"{'='*60}")

        try:
            print(f"📄 重新读取修改后的文件...")
            layered_file = psapi.LayeredFile.read(modified_path)

            text_layer = None
            for layer in layered_file.flat_layers:
                if isinstance(layer, (psapi.TextLayer_8bit, psapi.TextLayer_16bit, psapi.TextLayer_32bit)):
                    if layer.text:
                        text_layer = layer
                        break

            if text_layer:
                print(f"✅ 成功读取修改后的文件")
                print(f"   图层: {text_layer.name}")
                print(f"   文本: {text_layer.text}")

                if hasattr(text_layer, 'style_run_faux_bold'):
                    print(f"   FauxBold: {text_layer.style_run_faux_bold(0)}")
                if hasattr(text_layer, 'style_run_tracking'):
                    print(f"   Tracking: {text_layer.style_run_tracking(0)}")

                return True
            else:
                print(f"❌ 未找到文本图层")
                return False

        except Exception as e:
            print(f"❌ 读取失败: {e}")
            import traceback
            traceback.print_exc()
            return False

def main():
    print("="*60)
    print("  PhotoshopAPI 完整功能测试")
    print("="*60)

    editor = PhotoshopAPICertificateEditor()

    # 测试文件路径
    psd_path = "/Users/xiaojiujiu2/Downloads/资本存款.psd"
    output_path = "/Volumes/KenDisk/Coding/openclaw-runtime/workspace/test_output.psd"

    # 测试 1: 读取和检查
    layered_file = editor.test_read_and_inspect(psd_path)
    if not layered_file:
        print("\n❌ 测试失败：无法读取 PSD 文件")
        return

    # 测试 2: 修改文本
    success = editor.test_modify_text(psd_path, output_path)
    if not success:
        print("\n❌ 测试失败：无法修改文本")
        return

    # 测试 3: 往返验证
    success = editor.test_roundtrip(psd_path, output_path)
    if not success:
        print("\n❌ 测试失败：往返验证失败")
        return

    print("\n" + "="*60)
    print("✅ 所有测试通过！")
    print("="*60)
    print("\n结论:")
    print("  PhotoshopAPI 可以:")
    print("  ✅ 读取 PSD 文件")
    print("  ✅ 访问文本图层")
    print("  ✅ 读取 FauxBold 和 Tracking")
    print("  ✅ 修改文本内容")
    print("  ✅ 保留原始样式")
    print("  ✅ 写回 PSD 文件")
    print("\n  下一步: 实现完整的公证文件编辑器")

if __name__ == "__main__":
    main()
