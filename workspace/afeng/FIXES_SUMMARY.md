# PDF账单生成器 - 颜色修复总结

## 修复的问题

### 1. 账单周期日期颜色错误
**问题**: 账单周期日期显示为黑色，应该是青色/蓝绿色
**原因**: PyMuPDF内部使用BGR格式存储颜色，但提取时顺序错误
**解决方案**: 
- 修改 `analyzer.py` 中的颜色提取逻辑
- 从 `(r, g, b) = ((color >> 16) & 0xFF, (color >> 8) & 0xFF, color & 0xFF)` 
- 改为 `(r, g, b) = ((color >> 16) & 0xFF, (color >> 8) & 0xFF, color & 0xFF)` 然后返回 `(b, g, r)`
- 这样提取的RGB颜色 (0, 102, 102) 才是正确的青色

### 2. 所有文本都是黑色
**问题**: TextWriter.append() 不支持 color 参数，所有文本都是黑色
**解决方案**:
- 修改 `generator.py` 中的 `apply_changes` 方法
- 按颜色分组创建多个 TextWriter 实例
- 每个 TextWriter 使用 `write_text(page, color=normalized_color)` 写入时指定颜色

### 3. 抄表日期有文字底色
**问题**: redaction 使用白色填充，导致文字有底色
**解决方案**:
- 移除 `page.add_redact_annot(rect, fill=(1, 1, 1))` 中的 fill 参数
- 改为 `page.add_redact_annot(rect)` 不填充颜色

## 技术细节

### PyMuPDF颜色格式
- PyMuPDF内部使用BGR格式存储颜色整数
- 颜色整数 26214 = 0x6666 = (102, 102, 0) 在BGR中
- 提取时需要反转顺序得到RGB: (0, 102, 102)

### TextWriter颜色支持
- `TextWriter.append()` 不支持 color 参数
- `TextWriter.write_text(page, color=tuple)` 支持颜色
- 需要按颜色分组，为每种颜色创建独立的TextWriter

### 字体限制
- Songti.ttc (TrueType Collection) 不支持 TextWriter
- 华文仿宋在macOS上默认不可用
- 暂时所有字段使用微软雅黑字体

## 修改的文件

1. `/Volumes/KenDisk/Coding/openclaw-runtime/extensions/bill-generator-plugin/src/analyzer.py`
   - 修复颜色提取顺序 (BGR -> RGB)

2. `/Volumes/KenDisk/Coding/openclaw-runtime/extensions/bill-generator-plugin/src/generator.py`
   - 按颜色分组创建TextWriter
   - 移除redaction填充颜色
   - 简化字体选择逻辑

## 验证结果

生成的PDF中：
- 账单周期日期 (2026-03-01, 2026-03-31): 颜色 (0, 102, 102) ✓
- 账单打印日期: 颜色 (0, 0, 0) ✓
- 抄表日期: 颜色 (0, 0, 0)，无底色 ✓
- 所有字段: 使用微软雅黑字体 ✓

## 待改进

1. 支持华文仿宋字体（需要找到可用的.ttf文件）
2. 支持TrueType Collection (.ttc) 字体
3. 优化字体选择逻辑，为不同字段使用不同字体
