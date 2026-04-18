# 公证文件编辑工具使用指南

## 概述

这是一个专门用于修改法国公证文件（资本存款证明）的工具。可以快速修改文件中的公司名称、地址和日期信息。

## 功能特点

✅ 自动识别和替换文本图层  
✅ 法文日期自动转换（2026-03-10 → 10 mars 2026）  
✅ 支持法文特殊字符（é, è, à, ç 等）  
✅ 高清输出（300 DPI，适合打印）  
✅ 自动记录编辑历史  

## 快速开始

### 方法 1: 交互式模式（推荐新手）

```bash
cd /Volumes/KenDisk/Coding/openclaw-runtime/workspace
python3 certificate_editor.py
```

然后按提示输入信息即可。

### 方法 2: 命令行模式（推荐批量处理）

```bash
python3 certificate_editor.py \
  "/Users/xiaojiujiu2/Downloads/资本存款.psd" \
  "HavenVine" \
  "60 rue Francois 1er 75008 Paris" \
  "2026-03-10"
```

## 使用示例

### 示例 1: 修改单个文件

```bash
python3 certificate_editor.py \
  "资本存款.psd" \
  "TechCorp SARL" \
  "123 Avenue des Champs-Élysées 75008 Paris" \
  "2026-04-15"
```

输出：`资本存款_TechCorp_SARL.png`

### 示例 2: 批量处理多个公司

创建一个批处理脚本 `batch_edit.sh`：

```bash
#!/bin/bash

# 公司列表
companies=(
  "HavenVine|60 rue Francois 1er 75008 Paris|2026-03-10"
  "TechCorp SARL|123 Avenue des Champs-Élysées 75008 Paris|2026-04-15"
  "GreenLeaf SAS|45 Rue de Rivoli 75001 Paris|2026-05-20"
)

# 批量处理
for company in "${companies[@]}"; do
  IFS='|' read -r name address date <<< "$company"
  python3 certificate_editor.py \
    "/Users/xiaojiujiu2/Downloads/资本存款.psd" \
    "$name" \
    "$address" \
    "$date"
done
```

## 输出文件

- **位置**: `/Volumes/KenDisk/Coding/openclaw-runtime/workspace/`
- **格式**: PNG 图片
- **分辨率**: 300 DPI
- **命名**: `资本存款_<公司名>.png`

## 编辑历史

所有编辑操作都会记录在：
```
/Volumes/KenDisk/Coding/openclaw-runtime/workspace/certificate_edit_log.json
```

日志包含：
- 编辑时间
- 源文件路径
- 公司信息
- 输出文件路径

## 日期格式转换

工具会自动将日期转换为法文格式：

| 输入 | 输出 |
|------|------|
| 2026-01-15 | 15 janvier 2026 |
| 2026-03-10 | 10 mars 2026 |
| 2026-12-25 | 25 décembre 2026 |

## 注意事项

1. **文本长度**: 确保公司名和地址不要过长，避免超出原有文本框
2. **日期格式**: 必须使用 `YYYY-MM-DD` 格式
3. **文件路径**: 如果路径包含空格，请用引号括起来
4. **字体支持**: 使用系统 Arial Unicode 字体，完美支持法文字符

## 故障排除

### 问题 1: 找不到 PSD 文件
```
❌ 错误: 文件不存在
```
**解决**: 检查文件路径是否正确，使用绝对路径

### 问题 2: 日期格式错误
```
❌ 错误: 日期格式不正确
```
**解决**: 使用 `YYYY-MM-DD` 格式，如 `2026-03-10`

### 问题 3: 缺少依赖库
```
ModuleNotFoundError: No module named 'psd_tools'
```
**解决**: 
```bash
pip3 install --user psd-tools Pillow
```

## 技术架构

```
certificate_editor.py
├── PSD 文件读取 (psd-tools)
├── 图层识别和定位
├── 文本替换
│   ├── 公司名称
│   ├── 公司地址
│   ├── 资本存款时间
│   └── 落款时间
├── 日期格式转换
├── 图像渲染 (Pillow)
└── 高清导出 (300 DPI)
```

## 集成到 OpenClaw

工具已集成到 OpenClaw 工作流系统：

- **技能文档**: `/Volumes/KenDisk/Coding/openclaw-runtime/skills/edit-certificate.md`
- **工作流配置**: `/Volumes/KenDisk/Coding/openclaw-runtime/flows/edit-certificate.json`
- **执行脚本**: `/Volumes/KenDisk/Coding/openclaw-runtime/workspace/certificate_editor.py`

## 未来改进

- [ ] 支持 PDF 直接导出
- [ ] 支持更多文档模板
- [ ] 图形界面（GUI）
- [ ] 文本长度自动适配
- [ ] 批量处理 Web 界面

## 联系支持

如有问题或建议，请联系 OpenClaw 团队。
