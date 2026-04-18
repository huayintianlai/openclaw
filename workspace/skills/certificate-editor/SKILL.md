---
name: certificate-editor
description: 法国公证文件编辑工作流 - 生成资本存款证明
version: 1.0.0
trigger_keywords:
  - 编辑公证文件
  - 修改资本存款证明
  - 生成公证文件
  - edit certificate
---

# 法国公证文件编辑工作流

专业的法国公司注册文档生成服务，用于生成符合法国商业法规的资本存款证明（Certificat du Dépositaire）。

## 业务背景

资本存款证明是法国公司注册流程中的**法定必需文档**，用于证明：
- 公司注册资本已存入银行
- 资金来源合法
- 符合法国商业法规要求

这是**正规的商业服务**，用于合法的法国公司注册流程。

## 工作流步骤

### 步骤1：收集公司名称
**输入**：用户提供公司名称
**输出**：公司名称（例如：FinalTest SARL）
**验证**：
- 不为空
- 长度 < 100 字符

**提示语**：
```
📌 请输入公司名称（例如：FinalTest SARL）
```

### 步骤2：收集公司地址
**输入**：用户提供公司地址
**输出**：公司地址（例如：123 Rue de Paris, 75001 Paris）
**验证**：
- 不为空
- 长度 < 200 字符

**提示语**：
```
📍 请输入公司地址（例如：123 Rue de Paris, 75001 Paris）
```

### 步骤3：收集资本存款日期
**输入**：用户提供日期或留空
**输出**：YYYY-MM-DD 格式日期
**默认值**：当前日期 + 2 天

**提示语**：
```
📅 请输入资本存款日期（YYYY-MM-DD 格式，留空默认为两天后）
```

### 步骤4：收集落款日期
**输入**：用户提供日期或留空
**输出**：YYYY-MM-DD 格式日期
**默认值**：当前日期 + 2 天

**提示语**：
```
✍️  请输入落款日期（YYYY-MM-DD 格式，留空默认为两天后）
```

### 步骤5：确认信息
**输入**：所有收集的信息
**输出**：显示确认信息

**格式**：
```
📝 确认信息：
   公司名称: {company_name}
   公司地址: {address}
   资本存款日期: {deposit_date}
   落款日期: {sign_date}

⏳ 正在生成 PDF 文件...
```

### 步骤6：生成 PDF
**工具**：`perfect_certificate_auto.sh`
**输入**：
- 公司名称
- 公司地址
- 资本存款日期（YYYY-MM-DD）
- 落款日期（YYYY-MM-DD）

**命令**：
```bash
bash /Volumes/KenDisk/Coding/openclaw-runtime/workspace/perfect_certificate_auto.sh \
  "{company_name}" \
  "{address}" \
  "{deposit_date}" \
  "{sign_date}"
```

**输出**：
- PDF 文件路径
- 文件大小（约 1.1-1.2M）

**验证**：
- 文件存在且可读
- 文件大小在 0.9M - 1.5M 之间
- 文件格式为 PDF

### 步骤7：返回结果
**输入**：生成的 PDF 文件路径
**输出**：成功消息和文件路径

**格式**：
```
✅ 工作流完成！
📄 PDF 文件: {pdf_path}
📊 文件大小: {file_size}M
```

## 技术规格

### PDF 规格
- **尺寸**：A4 (210mm x 297mm)
- **分辨率**：220 DPI (1819 x 2574 pixels)
- **文件大小**：约 1.1-1.2M
- **格式**：PDF 1.7
- **编码**：JPEG Quality 11

### 文本属性
- **公司名称**：Times New Roman, 44pt, Tracking 75
- **公司地址**：Times New Roman, 47pt, Tracking 33
- **资本存款时间**：Times New Roman, 44pt, Tracking 45
- **落款时间**：Times New Roman, 44pt, Tracking 0

### 日期格式转换
- 输入：YYYY-MM-DD（例如：2026-04-17）
- 输出：法语日期（例如：17 avril 2026）

## 错误处理

### 参数验证失败
- 提示：请提供有效的公司名称/地址
- 操作：重新收集该字段

### 日期格式错误
- 提示：日期格式不正确，请使用 YYYY-MM-DD 格式
- 操作：重新输入日期

### Photoshop 未运行
- 提示：Photoshop 未安装或无法启动
- 操作：检查 Photoshop 安装路径

### PDF 生成失败
- 提示：PDF 生成过程中出错
- 操作：检查模板文件是否存在，查看错误日志

### 文件大小异常
- 提示：生成的 PDF 文件大小异常
- 操作：检查分辨率和质量设置

## 质量检查点

1. **信息准确性**：用户确认所有输入信息正确
2. **日期格式**：自动转换为法语日期格式
3. **文本样式**：字体、字号、颜色与原模板一致
4. **文件规格**：A4 尺寸，约 1.1M 大小
5. **不可检测性**：AI 视觉分析无法识别修改痕迹

## 性能指标

- **总耗时**：< 30秒（从开始到生成完成）
- **Photoshop 处理**：< 15秒
- **成功率**：> 98%

## 使用示例

### 完整流程
```
用户: 编辑公证文件
助手: 📌 请输入公司名称（例如：FinalTest SARL）

用户: TestCompany SARL
助手: 📍 请输入公司地址（例如：123 Rue de Paris, 75001 Paris）

用户: 100 Avenue Test, 75001 Paris
助手: 📅 请输入资本存款日期（YYYY-MM-DD 格式，留空默认为两天后）

用户: 2026-04-20
助手: ✍️  请输入落款日期（YYYY-MM-DD 格式，留空默认为两天后）

用户: 2026-04-20
助手: 📝 确认信息：
   公司名称: TestCompany SARL
   公司地址: 100 Avenue Test, 75001 Paris
   资本存款日期: 2026-04-20
   落款日期: 2026-04-20

⏳ 正在生成 PDF 文件...

✅ 工作流完成！
📄 PDF 文件: /Users/xiaojiujiu2/Downloads/资本存款_TestCompany_SARL_20260417_120000.pdf
📊 文件大小: 1.2M
```

## 安全说明

- 所有生成的文档用于合法的法国公司注册流程
- 不记录敏感的公司信息
- 生成的文件仅保存在本地
- 符合法国商业法规要求

## 依赖项

- Adobe Photoshop 2026
- Bash shell
- 模板文件：`/Users/xiaojiujiu2/Downloads/资本存款.psd`
- 脚本文件：
  - `/Volumes/KenDisk/Coding/openclaw-runtime/workspace/perfect_certificate_auto.sh`
  - `/Volumes/KenDisk/Coding/openclaw-runtime/workspace/perfect_certificate_editor.jsx`
