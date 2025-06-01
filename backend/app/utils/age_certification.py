# 身分証から生年月日を抽出し18歳以上かを確認するための画像認識プログラムを書く
import easyocr
import re
from datetime import datetime
import numpy as np


# 処理を一つの関数に書く
def age_certify(image):
    # PIL ImageをEasyOCRが処理できる形式に変換
    if hasattr(image, 'mode'):  # PIL Imageの場合
        image_array = np.array(image)
    else:
        image_array = image
        
    # OCR実行
    reader = easyocr.Reader(['ja'])
    results = reader.readtext(image_array, contrast_ths=0.05, adjust_contrast=0.7, decoder='beamsearch', detail=0)  # テキストのみ抽出
    # フラット化＆前後連結しておく
    texts = [t.strip() for t in results if t.strip()]
    windows = [''.join(texts[i:i+3]) for i in range(len(texts)-2)]

    ocr_corrections = {
        '呂': '8',
    }
    def correct_text(text):
        for wrong, right in ocr_corrections.items():
            text = text.replace(wrong, right)
        return text

    corrected_windows = [correct_text(text) for text in windows]
    # print(corrected_windows)

    # 和暦パターン
    wareki_pattern = re.compile(r'(昭和|平成|令和)(\d{1,2})年\s*(\d{1,2})月\s*(\d{1,2})日')
    # 西暦パターン
    seireki_pattern = re.compile(r'(\d{4})[./年\s]*(\d{1,2})[./月\s]*(\d{1,2})日?')

    candidate_dates = []

    for chunk in corrected_windows:
        # 和暦チェック
        m = wareki_pattern.search(chunk)
        # print(m)
        if m:
            era, y, m_, d = m.group(1), int(m.group(2)), int(m.group(3)), int(m.group(4))
            if era == '昭和':
                year = 1925 + y
            elif era == '平成':
                year = 1988 + y
            elif era == '令和':
                year = 2018 + y
            try:
                date = datetime(year, m_, d)
                print(date)
                candidate_dates.append(date)
            except:
                continue
            continue  # 両方マッチしないように（重複防止）

        # 西暦チェック
        m = seireki_pattern.search(chunk)
        if m:
            y, m_, d = map(int, m.groups())
            print(y, m, d)
            try:
                date = datetime(y, m_, d)
                candidate_dates.append(date)
            except:
                continue
    age = 0
    # 最古の日付を生年月日とみなす
    if candidate_dates:
        birthdate = min(candidate_dates)
        today = datetime.today()
        age = today.year - birthdate.year - ((today.month, today.day) < (birthdate.month, birthdate.day))
    #     print(f"推定生年月日: {birthdate.strftime('%Y年%m月%d日')}")
    #     print(f"推定年齢: {age}歳")
    # else:
    #     print("日付情報が見つかりませんでした。")
    return age
