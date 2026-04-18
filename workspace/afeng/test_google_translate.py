#!/usr/bin/env python3
"""
测试Google翻译API连接
"""
import requests
import re

def test_google_translate(text, target_lang='fr'):
    """测试Google翻译"""
    session = requests.Session()
    base_link = "http://translate.google.com/m"
    headers = {
        "User-Agent": "Mozilla/4.0 (compatible;MSIE 6.0;Windows NT 5.1;SV1;.NET CLR 1.1.4322;.NET CLR 2.0.50727;.NET CLR 3.0.04506.30)"
    }

    try:
        response = session.get(
            base_link,
            params={"tl": target_lang, "sl": "zh-CN", "q": text},
            headers=headers,
            timeout=10
        )

        print(f"状态码: {response.status_code}")
        print(f"响应长度: {len(response.text)}")

        if response.status_code == 200:
            re_result = re.findall(
                r'(?s)class="(?:t0|result-container)">(.*?)<', response.text
            )
            if re_result:
                translated = html.unescape(re_result[0])
                print(f"原文: {text}")
                print(f"译文: {translated}")
                return translated
            else:
                print("未找到翻译结果")
                print(f"响应内容前500字符:\n{response.text[:500]}")
        else:
            print(f"请求失败: {response.status_code}")

    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import html
    test_google_translate("电费账单", "fr")
    print("\n" + "="*50 + "\n")
    test_google_translate("国网浙江省电力公司", "fr")
