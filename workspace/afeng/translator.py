#!/usr/bin/env python3
"""
PDF账单翻译模块
支持将中文账单翻译为法语等其他语言
"""
from typing import Dict, Optional
from dataclasses import dataclass


@dataclass
class TranslationConfig:
    """翻译配置"""
    target_language: str = "french"
    use_ai_fallback: bool = True


class BillTranslator:
    """账单翻译器"""

    def __init__(self, config: Optional[TranslationConfig] = None):
        self.config = config or TranslationConfig()
        self._load_translations()

    def _load_translations(self):
        """加载翻译字典"""
        # 中文 -> 法语翻译字典
        self.translations = {
            # 标题和标签
            "户名": "Nom du titulaire",
            "户号": "Numéro de compte",
            "用电地址": "Adresse d'utilisation",
            "账单周期": "Période de facturation",
            "本期电量": "Consommation de cette période",
            "应缴电费": "Montant à payer",
            "抄表日期": "Date de relevé",
            "账单打印日期": "Date d'impression de la facture",

            # 表格标题
            "电量明细": "Détails de la consommation",
            "上期示数": "Relevé précédent",
            "本期示数": "Relevé actuel",
            "倍率": "Multiplicateur",
            "抄见电量": "Consommation relevée",
            "计费电量": "Consommation facturée",
            "合计": "Total",
            "账单详情": "Détails de la facture",
            "用能分析": "Analyse de la consommation",
            "电费明细": "Détails des frais",
            "费用项目": "Catégorie de frais",
            "计费标准": "Tarif",
            "电费": "Frais d'électricité",
            "加减变损": "Ajustement",
            "倍率抄见电量加减变损": "Multiplicateur Consommation relevée Ajustement",

            # 电价类型
            "峰": "Heures de pointe",
            "平": "Heures normales",
            "谷": "Heures creuses",
            "峰段": "Période de pointe",
            "平段": "Période normale",
            "谷段": "Période creuse",
            "尖峰": "Heures de pointe maximale",

            # 单位
            "千瓦时": "kWh",
            "元": "CNY",
            "元/千瓦时": "CNY/kWh",

            # 其他常用词
            "供电服务单位": "Fournisseur d'électricité",
            "国网": "State Grid",
            "供电公司": "Compagnie d'électricité",
            "电能表编号": "N° compteur",
            "电价": "Tarif",
            "用电户": "Utilisateur",
            "居民": "Résidentiel",
            "伏": "V",
            "本期": "Cette période",
            "上期": "Période précédente",
            "注": "Note",
            "网上国网": "State Grid en ligne",
            "号": "N°",
            "第一阶梯": "Premier palier",
            "第二阶梯": "Deuxième palier",
            "第三阶梯": "Troisième palier",
            "第四阶梯": "Quatrième palier",
            "较上期": "par rapport à la période précédente",
            "环比增长": "croissance",
            "您的电量为": "Votre consommation est de",
            "千瓦时": "kWh",
            "峰谷分时比例为": "Ratio heures de pointe/creuses:",
            "平均电价": "Tarif moyen",
            "增长": "augmentation",
            "用电的": "d'électricité",
            "您用电的": "Votre consommation",
            "您的": "Votre",
            "费用组成": "Composition des frais",
            "单位": "Unité",
            "千伏安": "kVA",
            "千瓦": "kW",
            "民生活户表用电": "Électricité résidentielle",
            "居民生活": "Résidentiel",
            "居民丰水期谷段": "Période creuse résidentielle",
            "丰水期": "Période humide",

            # 省份
            "浙江": "Zhejiang",
            "四川": "Sichuan",
            "北京": "Beijing",
            "上海": "Shanghai",
            "广东": "Guangdong",
            "建德": "Jiande",
            "乾潭": "Qiantan",
            "寿昌": "Shouchang",
            "童家": "Tongjia",
            "幸福": "Xingfu",

            # 数字和连接词
            "至": " à ",
            "省": " Province ",  # 修改：去掉"de"，因为在公司名称中不需要
            "市": " City ",
            "镇": " Town ",
            "村": " Village ",
            "街道": " Street ",
            "路": " Road ",

            # 新增缺失翻译
            "电 费 账 单": "FACTURE D'ÉLECTRICITÉ",
            "用电类": "Type d'utilisation",
            "别": "",  # 这是"类别"的"别"，单独出现时删除
            "居民生活用电": "Électricité résidentielle",
            "电压等级": "Niveau de tension",
            "交流": "AC",
            "供电服务单位": "Fournisseur d'électricité",
            "国网浙江省电力公司": "State Grid Zhejiang Province Electric Power Company",
            "国网浙江建德供电公司": "State Grid Jiande Electric Power Company",
            "浙江省电力公司": "Zhejiang Province Electric Power Company",
            "电力公司": "Electric Power Company",
            "单位：千瓦时、千伏安（千瓦）、元": "Unité: kWh, kVA (kW), CNY",
            "示数类型": "Type de relevé",
            "线损": "Perte en ligne",
            "退补": "Ajustement",
            "正向有功": "Énergie active positive",
            "总/平": "Total/Normal",
            "三档加价电费": "Supplément 3ème palier",
            "二档加价电费": "Supplément 2ème palier",
            "备": "Remarque",
            "您可以扫描账单右下角二维码，下载登录网上国网App，查询电价公示表、电费账单详情以及用能分析等": "Scannez le QR code en bas à droite pour télécharger l'application State Grid et consulter les tarifs, détails de facture et analyse de consommation",
            "网站": "Site web",
            "长": "croissance",
            "峰谷阶梯": "Paliers heures de pointe/creuses",

            # 新增：四川地区相关
            "四川": "Sichuan",
            "浙江": "Zhejiang",
            "建德": "Jiande",
            "浙江建德": "Zhejiang Jiande",
            "四川-用电户-220至380伏-居民生活户表用": "Sichuan-Utilisateur-220 à 380V-Électricité résidentielle",
            "浙江-用电户-220至380伏-居民生活户表用": "Zhejiang-Utilisateur-220 à 380V-Électricité résidentielle",
            "浙江-用电户-220至380伏-居民": "Zhejiang-Utilisateur-220 à 380V-Résidentiel",
            "浙江-用电户-220至380伏-居": "Zhejiang-Utilisateur-220 à 380V-Rés.",
            "电-居民生活-居民丰水期谷段0.175(峰)": "Électricité-Résidentiel-Période humide creuse 0.175(Pointe)",
            "电-居民生活-居民丰水期谷段0.175(平)": "Électricité-Résidentiel-Période humide creuse 0.175(Normal)",
            "电-居民生活-居民丰水期谷段0.175(谷)": "Électricité-Résidentiel-Période humide creuse 0.175(Creuse)",

            # 新增：动态文本片段
            "本期您的电量为": "Votre consommation est de",
            "千瓦时，较上期环比增": "kWh, croissance de",
            "本期您用电的峰谷分时比例为": "Votre ratio heures de pointe/creuses est de",
            "，上期峰谷分时比例为": ", période précédente:",
            "本期您的平均电价": "Votre tarif moyen est de",
            "元/千瓦时，较上期": "CNY/kWh, par rapport à la période précédente",
            "增长": "augmentation de",

            # 新增：电能表编号和电价组合
            "电能表编号：": "N° compteur: ",
            "，电价：": ", Tarif: ",
            "电力公司": "Electric Power Company",
        }

    def translate_field(self, chinese_text: str) -> str:
        """
        翻译单个字段

        Args:
            chinese_text: 中文文本

        Returns:
            翻译后的文本
        """
        # 1. 去除首尾空格
        text = chinese_text.strip()

        # 2. 检查是否是数字、日期或特殊格式（不翻译）
        if self._is_numeric_or_date(text):
            return chinese_text

        # 3. 检查固定翻译字典（完全匹配）
        if text in self.translations:
            return self.translations[text]

        # 3.5 特殊处理：公司名称（优先于地址翻译）
        if '电力公司' in text or '供电公司' in text:
            # 这是公司名称，不是地址，走组合文本翻译
            result = text
            sorted_items = sorted(self.translations.items(), key=lambda x: len(x[0]), reverse=True)
            for cn, fr in sorted_items:
                if cn in result:
                    result = result.replace(cn, fr)
            result = ' '.join(result.split())
            return result

        # 4. 特殊处理：地址翻译（包含省市镇村的长文本，但排除"电能表编号"等）
        # 只有真正的地址才走地址翻译逻辑
        # 排除包含"电能表编号"、"电价"等非地址关键词的文本
        if any(keyword in text for keyword in ['电能表编号', '电价', '千瓦时', 'kWh']):
            # 这不是地址，走组合文本翻译
            pass
        else:
            is_address = any(keyword in text for keyword in ['省', '市', '镇', '村', '街道', '路'])
            # 如果只包含"号"但不包含其他地址关键词，不当作地址处理
            if '号' in text and not is_address:
                # 检查是否是"XX号"这种地址格式（数字+号）
                import re
                if re.search(r'\d+号', text):
                    is_address = True

            if is_address:
                result = self._translate_address(text)
                # 地址翻译后直接返回，不再检查是否包含中文（因为地名保留中文是正常的）
                return result

        # 5. 处理组合文本（按长度排序，优先匹配长词组）
        result = text
        # 按中文长度降序排序，避免"用电"被替换后"用电户"无法匹配
        sorted_items = sorted(self.translations.items(), key=lambda x: len(x[0]), reverse=True)
        for cn, fr in sorted_items:
            if cn in result:
                result = result.replace(cn, fr)

        # 清理多余空格
        result = ' '.join(result.split())

        # 6. 如果还是中文，返回原文（或使用AI翻译）
        if self._contains_chinese(result):
            if self.config.use_ai_fallback:
                # TODO: 集成AI翻译
                return chinese_text
            return chinese_text

        return result

    def _translate_address(self, address: str) -> str:
        """
        专门处理地址翻译
        策略：完全翻译成法语，地名使用拼音

        Args:
            address: 中文地址

        Returns:
            翻译后的地址
        """
        result = address

        # 先翻译已知的地名
        place_names = {
            "浙江": "Zhejiang",
            "建德": "Jiande",
            "乾潭": "Qiantan",
            "幸福": "Xingfu",
            "苏圹": "Sukuang",
        }

        for cn, pinyin in place_names.items():
            result = result.replace(cn, pinyin)

        # 再翻译行政级别关键词
        admin_keywords = {
            "省": " Province ",
            "市": " City ",
            "镇": " Town ",
            "村": " Village ",
            "街道": " Street ",
            "路": " Road ",
            "号": " No. ",
        }

        for cn, fr in admin_keywords.items():
            result = result.replace(cn, fr)

        # 清理多余空格
        result = ' '.join(result.split())

        return result

    def _is_numeric_or_date(self, text: str) -> bool:
        """判断是否是数字、日期或特殊格式"""
        # 数字（可能包含小数点、逗号、负号）
        if text.replace('.', '').replace(',', '').replace('-', '').replace(' ', '').isdigit():
            return True

        # 日期格式（YYYY-MM-DD, YYYY/MM/DD, YYYY.MM.DD）
        import re
        date_patterns = [
            r'^\d{4}[-/\.]\d{1,2}[-/\.]\d{1,2}$',  # 2026-04-17
            r'^\d{4}年\d{1,2}月\d{1,2}日$',  # 2026年4月17日
        ]
        for pattern in date_patterns:
            if re.match(pattern, text):
                return True

        # 编号格式（纯数字或数字+字母，且长度>10）
        # 但排除包含中文的文本（如地址）
        if len(text) > 10 and text.replace(' ', '').isalnum() and not self._contains_chinese(text):
            return True

        return False

    def _contains_chinese(self, text: str) -> bool:
        """判断文本是否包含中文字符"""
        for char in text:
            if '\u4e00' <= char <= '\u9fff':
                return True
        return False

    def translate_all_fields(self, fields: Dict[str, str]) -> Dict[str, str]:
        """
        翻译所有字段

        Args:
            fields: 字段字典 {字段名: 中文值}

        Returns:
            翻译后的字典 {字段名: 法语值}
        """
        translated = {}
        for field_name, chinese_value in fields.items():
            translated[field_name] = self.translate_field(chinese_value)

        return translated


if __name__ == "__main__":
    # 测试翻译功能
    translator = BillTranslator()

    test_cases = [
        "户名",
        "陈天浩",
        "浙江省建德市寿昌镇童家村",
        "2026-03-18至2026-04-17",
        "762",
        "430.54",
        "峰",
        "千瓦时",
        "5130001000000361446389",
        "浙江-用电户-220至380伏-居民",
    ]

    print("翻译测试：")
    print("=" * 60)
    for text in test_cases:
        translated = translator.translate_field(text)
        print(f"{text:30} -> {translated}")
