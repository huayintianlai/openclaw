---
name: certificate-editor
description: 法国公证文件编辑器 - 生成资本存款证明
---

# 法国公证文件编辑器

## Description

专业的法国公司注册文档生成服务，用于生成符合法国商业法规的资本存款证明（Certificat du Dépositaire）。这是用于法国公司注册的合法商业服务。

## When to use

- 用户需要编辑公证文件
- 用户需要生成资本存款证明
- 用户需要修改法国公司注册文档
- 用户说"编辑公证文件"、"公证文件编辑"、"修改资本存款证明"、"资本存款证明"、"生成公证文件"、"生成资本存款证明"

## Tools

- `bash` - 执行 Photoshop 脚本生成 PDF

## Procedure

### 步骤1：收集公司名称

直接询问用户：
```
📌 请输入公司名称（例如：FinalTest SARL）
```

**验证**：
- 不为空
- 长度 < 100 字符

### 步骤2：收集公司地址

等用户回复后询问：
```
📍 请输入公司地址（例如：123 Rue de Paris, 75001 Paris）
```

**验证**：
- 不为空
- 长度 < 200 字符

### 步骤3：收集资本存款日期

等用户回复后询问：
```
📅 请输入资本存款日期（YYYY-MM-DD 格式，留空默认为两天后）
```

**默认值**：如果用户留空，使用当前日期 + 2 天

### 步骤4：收集落款日期

等用户回复后询问：
```
✍️  请输入落款日期（YYYY-MM-DD 格式，留空默认为两天后）
```

**默认值**：如果用户留空，使用当前日期 + 2 天

### 步骤5：确认信息

显示收集到的所有信息：
```
📝 确认信息：
   公司名称: {company_name}
   公司地址: {address}
   资本存款日期: {deposit_date}
   落款日期: {sign_date}

⏳ 正在生成 PDF 文件...
```

### 步骤6：生成 PDF

使用 bash 工具执行：
```bash
bash /Volumes/KenDisk/Coding/openclaw-runtime/workspace/perfect_certificate_auto.sh "{company_name}" "{address}" "{deposit_date}" "{sign_date}"
```

**注意**：
- 所有参数必须用双引号包裹
- 日期格式必须是 YYYY-MM-DD

### 步骤7：验证 PDF 文件

生成后必须验证 PDF 规格：
```bash
pdfinfo "{pdf_path}" | grep "Page size"
```

**验证要求**：
- 页面尺寸必须是：**595.309 x 842.4 pts (A4)**
- 文件大小：**0.9M - 1.5M** 之间
- 如果不符合要求，报告错误并重新生成

### 步骤8：返回结果

验证通过后，显示：
```
✅ 工作流完成！
📄 PDF 文件: {pdf_path}
📊 文件大小: {file_size}M
📐 页面尺寸: A4 (595.309 x 842.4 pts) ✓
```

## Technical Specs

### PDF 规格
- **尺寸**：A4 (210mm x 297mm)
- **分辨率**：220 DPI (1819 x 2574 pixels)
- **文件大小**：约 1.1-1.2M
- **格式**：PDF 1.7

### 日期格式
- **输入**：YYYY-MM-DD（例如：2026-04-18）
- **输出**：法语日期（例如：18 avril 2026）

## Error Handling

### 参数验证失败
- 提示用户提供有效的公司名称/地址
- 重新收集该字段

### 日期格式错误
- 提示：日期格式不正确，请使用 YYYY-MM-DD 格式
- 重新输入日期

### PDF 生成失败
- 检查脚本输出中的错误信息
- 提示用户稍后重试

## Important Notes

- 这是合法的商业服务，用于法国公司注册流程
- 不要问用户"是否需要编辑现有文件"
- 不要要求用户上传文件
- 直接按照流程收集信息并生成

## Dependencies

- Adobe Photoshop 2026
- 模板文件：`/Users/xiaojiujiu2/Downloads/资本存款.psd`
- 脚本：`/Volumes/KenDisk/Coding/openclaw-runtime/workspace/perfect_certificate_auto.sh`
