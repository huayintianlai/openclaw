---
name: edit-certificate
description: 修改法国公证文件（PSD格式）中的公司信息
version: 1.0.0
author: OpenClaw
---

# 公证文件编辑技能

这个技能用于修改法国公证文件（资本存款证明）中的关键信息。

## 功能

- 修改公司名称
- 修改公司地址
- 修改日期（自动转换为法文格式）
- 导出为高清 PNG 图片（300 DPI）

## 使用方法

当用户请求修改公证文件时，你需要：

1. **收集必要信息**：
   - PSD 文件路径
   - 公司名称
   - 公司地址
   - 日期（YYYY-MM-DD 格式）

2. **执行修改**：
   ```bash
   cd /Volumes/KenDisk/Coding/openclaw-runtime/workspace
   python3 psd_editor.py "<PSD文件路径>" "<公司名>" "<地址>" "<日期>"
   ```

3. **输出结果**：
   - 文件保存在 `/Volumes/KenDisk/Coding/openclaw-runtime/workspace/`
   - 文件名格式：`资本存款_<公司名>.png`

## 示例

```bash
python3 psd_editor.py \
  "/Users/xiaojiujiu2/Downloads/资本存款.psd" \
  "HavenVine" \
  "60 rue Francois 1er 75008 Paris" \
  "2026-03-10"
```

输出：`资本存款_HavenVine.png`

## 日期格式转换

输入格式：`YYYY-MM-DD`（如 2026-03-10）
输出格式：法文日期（如 10 mars 2026）

支持的月份：
- janvier, février, mars, avril, mai, juin
- juillet, août, septembre, octobre, novembre, décembre

## 技术细节

- 使用 `psd-tools` 读取 PSD 文件结构
- 使用 `Pillow` 进行图像处理和文本渲染
- 字体：Arial Unicode（系统自带，支持法文字符）
- 输出分辨率：300 DPI（适合打印）

## 注意事项

1. 确保 PSD 文件路径正确
2. 地址和公司名不要过长，避免超出原有文本框
3. 日期必须是有效的日期格式
4. 生成的是 PNG 图片，如需 PDF 可以后续转换
