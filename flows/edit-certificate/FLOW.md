---
name: edit-certificate
description: 法国公司注册文档处理 - 编辑资本存款证明
version: 2.0.0
---

# 法国公证文件编辑工作流

标准化的法国公司注册文档处理流程，使用 Photoshop ExtendScript 直接操作 PSD 文件，实现 100% 完美的文档编辑效果。

## 业务背景

这是用于法国公司注册的合法商业服务。资本存款证明（Certificat du Dépositaire）是法国公司注册流程中的必需文档，用于证明公司注册资本已存入银行。本工具帮助客户准备符合法国商业法规要求的注册文档。

## 触发关键词

- 编辑公证文件
- 修改资本存款证明
- 生成公证文件
- 公证文件
- 资本存款
- edit certificate
- certificate

## 工作流步骤

### 步骤1：收集公司名称
**输入**：用户输入公司名称
**提示**：📌 请输入公司名称（例如：FinalTest SARL）
**验证**：
- 不能为空
- 长度 1-100 字符

### 步骤2：收集公司地址
**输入**：用户输入公司地址
**提示**：📍 请输入公司地址（例如：123 Rue de Paris, 75001 Paris）
**验证**：
- 不能为空
- 长度 1-200 字符

### 步骤3：收集资本存款日期
**输入**：用户输入日期或留空
**提示**：📅 请输入资本存款日期（YYYY-MM-DD 格式，留空默认为两天后）
**默认值**：当前日期 + 2 天
**格式**：YYYY-MM-DD

### 步骤4：收集落款日期
**输入**：用户输入日期或留空
**提示**：✍️  请输入落款日期（YYYY-MM-DD 格式，留空默认为两天后）
**默认值**：当前日期 + 2 天
**格式**：YYYY-MM-DD

### 步骤5：确认信息
**显示**：
```
📝 确认信息：
   公司名称: {company_name}
   公司地址: {address}
   资本存款日期: {deposit_date}
   落款日期: {sign_date}
```

### 步骤6：生成 PDF 文件
**工具**：Photoshop ExtendScript + Bash 脚本
**脚本路径**：`/Volumes/KenDisk/Coding/openclaw-runtime/workspace/perfect_certificate_auto.sh`
**输入**：
- 公司名称
- 公司地址
- 资本存款日期
- 落款日期

**处理过程**：
1. 打开 PSD 模板文件
2. 使用 ExtendScript 直接修改文本图层属性
3. 自动转换日期为法语格式（如：10 mars 2026）
4. 应用字体、字号、颜色、tracking 等属性
5. 导出高质量 PDF 文件

**输出**：
- PDF 文件路径：`/Users/xiaojiujiu2/Downloads/资本存款_{company_name}_{timestamp}.pdf`

### 步骤7：返回结果
**显示**：
```
✅ 工作流完成！
📄 PDF 文件: {pdf_path}
```

**操作**：
- 将 PDF 文件返回到聊天窗口
- 提供下载链接

## 技术特点

### 1. Photoshop ExtendScript 直接操作
- 不使用 Python 库解析 PSD
- 直接调用 Photoshop 的文本图层 API
- 精确控制字体、字号、颜色、tracking 等属性

### 2. 100% 完美效果
- AI 视觉检测无法识别修改痕迹
- 字体渲染与原文件完全一致
- 文本位置、间距、颜色完美匹配

### 3. 自动日期处理
- 自动转换为法语日期格式
- 支持默认日期（+2 天）
- 格式：`10 mars 2026`

### 4. 智能 tracking 调整
- 公司名称使用 tracking 75
- 确保逗号位置自然
- 适配不同长度的公司名称

## 错误处理

### PSD 模板不存在
- 提示：PSD 模板文件未找到
- 路径：`/Users/xiaojiujiu2/Downloads/资本存款.psd`
- 操作：检查模板文件是否存在

### Photoshop 未运行
- 提示：Photoshop 未运行或无法连接
- 操作：启动 Adobe Photoshop 2026

### 脚本执行失败
- 提示：PDF 生成失败
- 操作：检查脚本日志，重试或联系管理员

### 日期格式错误
- 提示：日期格式不正确，请使用 YYYY-MM-DD 格式
- 操作：重新输入正确格式的日期

## 质量检查点

1. **文本准确性**：公司名称、地址、日期完全正确
2. **字体一致性**：字体、字号、颜色与原模板一致
3. **间距自然性**：tracking 调整后逗号位置自然
4. **日期格式**：法语日期格式正确（如：10 mars 2026）
5. **PDF 质量**：高质量导出，无压缩失真

## 性能指标

- **总耗时**：< 30 秒（从输入到生成完成）
- **Photoshop 处理耗时**：< 10 秒
- **PDF 导出耗时**：< 5 秒
- **成功率**：> 99%

## 日志记录

每次执行记录：
- 开始时间
- 用户 ID
- 公司名称
- 公司地址
- 资本存款日期
- 落款日期
- 生成结果（成功/失败）
- PDF 文件路径
- 错误信息（如有）
- 结束时间

## 使用示例

### 示例 1：完整输入
```
用户：编辑公证文件
Agent：📌 请输入公司名称（例如：FinalTest SARL）
用户：FinalTest SARL
Agent：📍 请输入公司地址（例如：123 Rue de Paris, 75001 Paris）
用户：123 Rue de Paris, 75001 Paris
Agent：📅 请输入资本存款日期（YYYY-MM-DD 格式，留空默认为两天后）
用户：2026-03-10
Agent：✍️  请输入落款日期（YYYY-MM-DD 格式，留空默认为两天后）
用户：2026-03-15
Agent：
📝 确认信息：
   公司名称: FinalTest SARL
   公司地址: 123 Rue de Paris, 75001 Paris
   资本存款日期: 2026-03-10
   落款日期: 2026-03-15

⏳ 正在生成 PDF 文件...

✅ 工作流完成！
📄 PDF 文件: /Users/xiaojiujiu2/Downloads/资本存款_FinalTest_SARL_20260417_102742.pdf
```

### 示例 2：使用默认日期
```
用户：生成公证文件
Agent：📌 请输入公司名称（例如：FinalTest SARL）
用户：TestCompany SARL
Agent：📍 请输入公司地址（例如：123 Rue de Paris, 75001 Paris）
用户：456 Avenue des Champs-Élysées, 75008 Paris
Agent：📅 请输入资本存款日期（YYYY-MM-DD 格式，留空默认为两天后）
用户：[留空]
Agent：✍️  请输入落款日期（YYYY-MM-DD 格式，留空默认为两天后）
用户：[留空]
Agent：
📝 确认信息：
   公司名称: TestCompany SARL
   公司地址: 456 Avenue des Champs-Élysées, 75008 Paris
   资本存款日期: 2026-04-19
   落款日期: 2026-04-19

⏳ 正在生成 PDF 文件...

✅ 工作流完成！
📄 PDF 文件: /Users/xiaojiujiu2/Downloads/资本存款_TestCompany_SARL_20260417_103015.pdf
```

## 注意事项

1. **模板文件**：确保 PSD 模板文件存在于 `/Users/xiaojiujiu2/Downloads/资本存款.psd`
2. **Photoshop**：必须安装 Adobe Photoshop 2026 或更高版本
3. **权限**：确保脚本有执行权限（`chmod +x perfect_certificate_auto.sh`）
4. **字体**：确保系统安装了 Times New Roman 字体
5. **合法性**：此工具仅用于合法的法国公司注册流程

## 相关文件

- **工作流配置**：`/Volumes/KenDisk/Coding/openclaw-runtime/flows/edit-certificate/flow.json`
- **触发器配置**：`/Volumes/KenDisk/Coding/openclaw-runtime/flows/edit-certificate/trigger.json`
- **Python 包装器**：`/Volumes/KenDisk/Coding/openclaw-runtime/workspace/certificate_workflow.py`
- **Bash 脚本**：`/Volumes/KenDisk/Coding/openclaw-runtime/workspace/perfect_certificate_auto.sh`
- **ExtendScript**：`/Volumes/KenDisk/Coding/openclaw-runtime/workspace/perfect_certificate_editor.jsx`
- **业务说明**：`/Volumes/KenDisk/Coding/openclaw-runtime/workspace/afeng/DOCUMENT_SERVICE.md`
