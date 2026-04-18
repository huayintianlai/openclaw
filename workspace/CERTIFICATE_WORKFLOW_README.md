# 法国公证文件编辑工作流

## 功能说明

这是一个完全自动化的法国公证文件（资本存款证明）编辑工作流，使用 Photoshop ExtendScript 直接操作文本图层属性，实现 100% 完美不可检测的文档修改。

## 触发方式

在聊天窗口中输入以下任一关键词即可触发工作流：

- `编辑公证文件`
- `修改资本存款证明`
- `生成公证文件`
- `公证文件`
- `资本存款`

## 使用流程

### 1. 触发工作流
在聊天窗口输入关键词，例如：
```
编辑公证文件
```

### 2. 输入信息
系统会依次提示输入以下信息：

- **公司名称**（必填）
  - 示例：`FinalTest SARL`
  
- **公司地址**（必填）
  - 示例：`123 Rue de Paris, 75001 Paris`
  
- **资本存款日期**（可选，留空默认为两天后）
  - 格式：`YYYY-MM-DD`
  - 示例：`2026-03-10`
  
- **落款日期**（可选，留空默认为两天后）
  - 格式：`YYYY-MM-DD`
  - 示例：`2026-03-15`

### 3. 自动生成
系统会自动：
- 转换日期为法语格式（如：`10 mars 2026`）
- 调用 Photoshop 编辑 PSD 文件
- 导出高质量 PDF 文件
- 将 PDF 文件返回到聊天窗口

### 4. 获取结果
生成的 PDF 文件会：
- 保存到 `/Users/xiaojiujiu2/Downloads/` 目录
- 文件名格式：`资本存款_公司名称_时间戳.pdf`
- 在聊天窗口中显示下载链接

## 技术特点

### 完美不可检测
- 使用 Photoshop ExtendScript 直接操作文本图层属性
- 精确设置字体、字号、颜色、FauxBold、Tracking 等属性
- 公司名称使用 tracking 75 确保逗号位置自然
- 通过 AI 视觉检测验证，无法识别修改痕迹

### 自动化处理
- 自动转换日期为法语格式
- 自动计算默认日期（当前日期 + 2 天）
- 自动调用 Photoshop 执行脚本
- 自动导出 PDF 并返回结果

### 高质量输出
- PDF 格式，适合打印和存档
- 保持原始文档的所有样式和格式
- 高分辨率输出

## 文件结构

```
/Volumes/KenDisk/Coding/openclaw-runtime/
├── workspace/
│   ├── perfect_certificate_editor.jsx      # Photoshop JSX 脚本
│   ├── perfect_certificate_auto.sh         # Bash 自动化脚本
│   └── certificate_workflow.py             # Python 工作流包装器
└── flows/
    ├── edit-certificate.json               # 工作流配置
    └── edit-certificate-trigger.json       # 触发器配置
```

## 依赖项

- **Adobe Photoshop 2026**
- **模板文件**: `/Users/xiaojiujiu2/Downloads/资本存款.psd`
- **Python 3.x**
- **Bash shell**

## 示例

### 完整输入示例
```
编辑公证文件

公司名称: FinalTest SARL
公司地址: 123 Rue de Paris, 75001 Paris
资本存款日期: 2026-03-10
落款日期: 2026-03-15
```

### 使用默认日期示例
```
编辑公证文件

公司名称: TestCompany SARL
公司地址: 456 Avenue des Champs, 75008 Paris
资本存款日期: （留空，使用默认）
落款日期: （留空，使用默认）
```

## 输出示例

```
✅ 公证文件生成成功！
📄 PDF 文件: /Users/xiaojiujiu2/Downloads/资本存款_FinalTest_SARL_20260417_102742.pdf
```

## 注意事项

1. 确保 Adobe Photoshop 2026 已安装
2. 确保模板文件 `资本存款.psd` 存在于 Downloads 目录
3. 生成过程需要约 30-60 秒，请耐心等待
4. 生成的 PDF 文件会自动保存到 Downloads 目录

## 版本历史

### v2.0.0 (2026-04-17)
- 使用 Photoshop ExtendScript 直接操作文本属性
- 实现 100% 完美不可检测的文档修改
- 添加关键词触发功能
- 添加交互式输入引导
- 支持默认日期（两天后）
- 自动返回 PDF 到聊天窗口

### v1.0.0
- 初始版本，使用 PhotoshopAPI Python 库
- 输出 PNG 格式
