# PDF账单法语翻译功能规划

## 一、需求分析

### 用户流程
1. 用户通过阿峰Agent生成中文电费账单
2. 系统展示生成的账单（对比图）
3. 用户确认账单无误
4. 用户选择"翻译为法语"
5. 系统生成法语版本的账单
6. 用户下载中文版和法语版

### 核心需求
- 保持PDF原有格式和布局
- 将所有中文文本翻译为法语
- 数字、日期、金额保持不变
- 字体需要支持法语字符（带重音符号）

---

## 二、技术方案

### 方案A：文本替换法（推荐）
**原理**：提取所有中文文本 → 翻译 → 替换回PDF

**优点**：
- 保持原有布局和样式
- 可以精确控制每个字段的翻译
- 复用现有的PDF编辑代码

**缺点**：
- 法语文本可能比中文长，需要调整字号或换行
- 需要处理字体兼容性

### 方案B：重新生成法（备选）
**原理**：使用法语模板 + 数据生成新PDF

**优点**：
- 布局完全可控
- 不受原PDF限制

**缺点**：
- 需要维护法语模板
- 工作量大

**推荐使用方案A**

---

## 三、翻译策略

### 3.1 需要翻译的内容

#### 固定文本（可预先翻译）
```python
TRANSLATIONS = {
    # 标题和标签
    "户名": "Nom du titulaire",
    "户号": "Numéro de compte",
    "用电地址": "Adresse d'utilisation",
    "账单周期": "Période de facturation",
    "本期电量": "Consommation de cette période",
    "应缴电费": "Montant à payer",
    "抄表日期": "Date de relevé",
    "账单打印日期": "Date d'impression",
    
    # 表格标题
    "电量明细": "Détails de la consommation",
    "上期示数": "Relevé précédent",
    "本期示数": "Relevé actuel",
    "倍率": "Multiplicateur",
    "抄见电量": "Consommation relevée",
    "计费电量": "Consommation facturée",
    "合计": "Total",
    
    # 电价类型
    "峰": "Heures de pointe",
    "平": "Heures normales",
    "谷": "Heures creuses",
    
    # 单位
    "千瓦时": "kWh",
    "元": "CNY",
    "元/千瓦时": "CNY/kWh",
    
    # 其他
    "供电服务单位": "Fournisseur d'électricité",
    "国网": "State Grid",
    "供电公司": "Compagnie d'électricité",
}
```

#### 动态文本（需要AI翻译）
- 地址（每个用户不同）
- 姓名（保持拼音或翻译）
- 长文本说明

### 3.2 翻译方法

#### 方法1：预定义字典（快速）
```python
def translate_fixed_text(chinese_text: str) -> str:
    """翻译固定文本"""
    return TRANSLATIONS.get(chinese_text, chinese_text)
```

#### 方法2：AI翻译（灵活）
```python
def translate_with_ai(text: str) -> str:
    """使用LLM翻译"""
    prompt = f"将以下中文翻译为法语，保持简洁：{text}"
    # 调用LLM API
    return translated_text
```

#### 方法3：混合方式（推荐）
- 固定文本用字典
- 动态文本用AI
- 数字和日期不翻译

---

## 四、字体处理

### 4.1 法语字符要求
法语包含特殊字符：
- 重音符号：é, è, ê, ë, à, â, ù, û, ô, î, ï
- 连字：œ, æ
- 大写重音：É, È, À, Ç

### 4.2 字体选择
**选项1：使用支持法语的字体**
- Arial Unicode MS
- DejaVu Sans
- Liberation Sans

**选项2：继续使用华文仿宋/微软雅黑**
- 测试是否支持法语字符
- 如果不支持，fallback到Arial

### 4.3 字号调整
法语文本通常比中文长20-30%，需要：
- 自动缩小字号以适应原有空间
- 或者允许文本换行

---

## 五、实施步骤

### 第1步：创建翻译模块
```python
# translation.py
class BillTranslator:
    def __init__(self):
        self.translations = TRANSLATIONS
        
    def translate_field(self, field_name: str, chinese_text: str) -> str:
        """翻译单个字段"""
        # 1. 检查是否是固定文本
        if chinese_text in self.translations:
            return self.translations[chinese_text]
        
        # 2. 检查是否是数字/日期（不翻译）
        if self._is_numeric(chinese_text):
            return chinese_text
        
        # 3. 使用AI翻译
        return self._translate_with_ai(chinese_text)
    
    def translate_pdf(self, input_pdf: str, output_pdf: str):
        """翻译整个PDF"""
        # 1. 提取所有文本
        # 2. 翻译每个文本块
        # 3. 替换回PDF
        pass
```

### 第2步：集成到工作流
```python
# 在 test_smart.py 中添加
if user_confirms:
    print("步骤8：生成法语翻译版")
    translator = BillTranslator()
    french_pdf = translator.translate_pdf(
        input_pdf=str(output_path),
        output_pdf=str(output_dir / f"电费账单-{id_info.name}-{timestamp}-FR.pdf")
    )
    print(f"  ✓ 法语版已生成: {french_pdf}")
```

### 第3步：测试和优化
- 测试各种长度的文本
- 调整字号和布局
- 验证法语语法正确性

---

## 六、文本长度处理

### 问题：法语文本更长
```
中文: "户名" (2字符)
法语: "Nom du titulaire" (17字符) - 8.5倍

中文: "本期电量" (4字符)
法语: "Consommation de cette période" (30字符) - 7.5倍
```

### 解决方案

#### 方案1：缩小字号
```python
def adjust_font_size(original_size: float, chinese_len: int, french_len: int) -> float:
    """根据文本长度调整字号"""
    ratio = chinese_len / french_len
    if ratio < 0.5:  # 法语超过2倍长
        return original_size * 0.7
    elif ratio < 0.7:
        return original_size * 0.85
    else:
        return original_size
```

#### 方案2：使用缩写
```python
SHORT_TRANSLATIONS = {
    "户名": "Nom",
    "户号": "N° compte",
    "本期电量": "Consommation",
    "应缴电费": "Montant",
}
```

#### 方案3：换行
对于长文本，允许自动换行

---

## 七、API设计

### 新增API端点
```python
# knowledge/server_patch/app.py

@app.post("/bill/translate")
async def translate_bill(
    pdf_path: str,
    target_language: str = "french",
    output_path: Optional[str] = None
):
    """
    翻译账单
    
    Args:
        pdf_path: 原始PDF路径
        target_language: 目标语言（french, english, spanish等）
        output_path: 输出路径（可选）
    
    Returns:
        {
            "translated_pdf": "/path/to/translated.pdf",
            "language": "french",
            "field_count": 50
        }
    """
    translator = BillTranslator(target_language)
    result = translator.translate_pdf(pdf_path, output_path)
    return result
```

---

## 八、阿峰Agent集成

### 交互流程
```
用户: 阿峰，帮我生成一份电费账单
阿峰: 好的！请上传身份证照片。

[用户上传照片]

阿峰: ✓ 识别完成
     姓名: 陈天浩
     地址: 浙江省建德市...
     
     正在生成账单...
     
     ✓ 账单已生成！
     [显示对比图]
     
     请确认账单信息是否正确？
     1. 确认无误，下载账单
     2. 生成法语翻译版
     3. 重新生成

用户: 2

阿峰: 正在生成法语翻译版...
     
     ✓ 法语版已生成！
     📄 中文版: 电费账单-陈天浩-20260417.pdf
     📄 法语版: 电费账单-陈天浩-20260417-FR.pdf
     
     是否需要其他语言版本？
```

---

## 九、扩展性

### 支持多语言
```python
SUPPORTED_LANGUAGES = {
    "french": "法语",
    "english": "英语",
    "spanish": "西班牙语",
    "german": "德语",
    "japanese": "日语",
}

class MultiLanguageTranslator:
    def __init__(self, target_language: str):
        self.target = target_language
        self.load_translations()
    
    def load_translations(self):
        """加载对应语言的翻译字典"""
        translation_file = f"translations/{self.target}.json"
        with open(translation_file) as f:
            self.translations = json.load(f)
```

---

## 十、实施优先级

### P0 - 核心功能（第一版）
- [ ] 创建翻译模块
- [ ] 实现固定文本翻译（字典）
- [ ] 实现PDF文本替换
- [ ] 处理字号调整
- [ ] 测试法语版生成

### P1 - 增强功能（第二版）
- [ ] 集成AI翻译（动态文本）
- [ ] 优化文本长度处理
- [ ] 添加API端点
- [ ] 集成到阿峰Agent

### P2 - 扩展功能（第三版）
- [ ] 支持多语言（英语、西班牙语等）
- [ ] 批量翻译
- [ ] 翻译质量检查

---

## 十一、风险和挑战

### 风险1：文本溢出
- **问题**：法语文本太长，超出原有空间
- **解决**：自动缩小字号或换行

### 风险2：字体不支持
- **问题**：华文仿宋可能不支持法语重音符号
- **解决**：fallback到Arial或DejaVu Sans

### 风险3：翻译质量
- **问题**：AI翻译可能不准确
- **解决**：使用预定义字典 + 人工审核

### 风险4：布局错乱
- **问题**：替换文本后布局可能变形
- **解决**：精确控制每个字段的位置和大小

---

## 十二、测试用例

### 用例1：短文本
- 中文: "户名"
- 法语: "Nom"
- 预期: 正常显示

### 用例2：长文本
- 中文: "本期您的电量为762千瓦时"
- 法语: "Votre consommation de cette période est de 762 kWh"
- 预期: 自动缩小字号或换行

### 用例3：特殊字符
- 中文: "供电公司"
- 法语: "Compagnie d'électricité"
- 预期: 正确显示撇号

---

## 十三、下一步行动

1. **确认需求**：用户确认翻译功能的具体要求
2. **创建翻译字典**：整理所有需要翻译的固定文本
3. **实现翻译模块**：编写 `translation.py`
4. **测试字体支持**：验证华文仿宋是否支持法语字符
5. **集成到工作流**：修改 `test_smart.py` 添加翻译步骤
6. **测试和优化**：生成样本并调整
