---
name: heic-to-jpg
description: 本地 HEIC 图片转 JPG 工具。用户提到“heic 转 jpg / heic转jpeg / 苹果照片转jpg / 把这张heic改成jpg”时使用。仅允许本地文件处理，不上传、不外发。
allowed-tools:
  - exec
  - read
---

# HEIC → JPG（本地转换）

## 何时使用
当用户明确要把 `.heic` 图片转成 `.jpg/.jpeg`，并且要求本地执行时。

## 强约束
1. **只处理本地文件**（workspace 或用户给出的本机绝对路径）。
2. **禁止上传到任何云端**。
3. 默认优先使用 macOS 自带 `sips`；若不可用可回退 `magick`。

## 执行步骤
1. 让用户提供源文件路径（或直接用用户消息里给的路径）。
2. 运行脚本：
   - 单文件：
     ```bash
     bash skills/heic-to-jpg/scripts/heic_to_jpg.sh \
       --input "/path/to/image.heic"
     ```
   - 批量目录：
     ```bash
     bash skills/heic-to-jpg/scripts/heic_to_jpg.sh \
       --input "/path/to/dir" --recursive
     ```
3. 回传图片到飞书（使用 `openclaw message send`）：
   ```bash
   openclaw message send --channel feishu --account xiaodong \
     --target <sender_open_id> \
     --media "/path/to/output.jpg" \
     --message "已转换完成"
   ```

## 输出约定
- 成功：用 `openclaw message send` 直接回传 JPG 到飞书，同时列出生成的 jpg 路径。
- 失败：给出具体失败文件和错误信息。

## 重要：图片回传方式
- ✅ 使用 `openclaw message send --channel feishu --account xiaodong --media <path>`
- ❌ 不要用 `MEDIA:` 路径（飞书渲染有问题）
- ❌ 不要用 `knowledge_return_file`（账号配置问题）
- 输出目录统一使用 workspace 下的 `inbox/`，不用 `/tmp/`

## 脚本位置
`skills/heic-to-jpg/scripts/heic_to_jpg.sh`
