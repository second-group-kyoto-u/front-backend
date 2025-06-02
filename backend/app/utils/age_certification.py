# 身分証から生年月日を抽出し18歳以上かを確認するための画像認識プログラムを書く
import easyocr
import re
from datetime import datetime
import numpy as np


# 処理を一つの関数に書く
def age_certify(image):
    print(f"[OCR] 年齢認証処理開始")
    
    # PIL ImageをEasyOCRが処理できる形式に変換
    if hasattr(image, 'mode'):  # PIL Imageの場合
        print(f"[OCR] PIL Image検出: モード={image.mode}, サイズ={image.size}")
        image_array = np.array(image)
        print(f"[OCR] Numpy配列に変換: shape={image_array.shape}")
    else:
        print(f"[OCR] 既にnumpy配列形式")
        image_array = image
        
    # OCR実行
    print(f"[OCR] EasyOCR開始...")
    reader = easyocr.Reader(['ja'])
    results = reader.readtext(image_array, contrast_ths=0.05, adjust_contrast=0.7, decoder='beamsearch', detail=0)  # テキストのみ抽出
    print(f"[OCR] 抽出されたテキスト数: {len(results)}")
    print(f"[OCR] 抽出されたテキスト: {results}")
    
    # フラット化＆前後連結しておく
    texts = [t.strip() for t in results if t.strip()]
    print(f"[OCR] フィルタ後のテキスト: {texts}")
    
    if len(texts) < 3:
        print(f"[OCR] テキストが不足しています（{len(texts)}個）")
        windows = texts
    else:
        windows = [''.join(texts[i:i+3]) for i in range(len(texts)-2)]
    print(f"[OCR] 検索対象ウィンドウ: {windows}")

    ocr_corrections = {
        '呂': '8',
    }
    def correct_text(text):
        for wrong, right in ocr_corrections.items():
            text = text.replace(wrong, right)
        return text

    corrected_windows = [correct_text(text) for text in windows]
    print(f"[OCR] 補正後ウィンドウ: {corrected_windows}")

    # 和暦パターン
    wareki_pattern = re.compile(r'(昭和|平成|令和)(\d{1,2})年\s*(\d{1,2})月\s*(\d{1,2})日')
    # 西暦パターン
    seireki_pattern = re.compile(r'(\d{4})[./年\s]*(\d{1,2})[./月\s]*(\d{1,2})日?')

    candidate_dates = []

    for chunk in corrected_windows:
        # 和暦チェック
        m = wareki_pattern.search(chunk)
        if m:
            print(f"[OCR] 和暦マッチ: {m.groups()}")
            era, y, m_, d = m.group(1), int(m.group(2)), int(m.group(3)), int(m.group(4))
            if era == '昭和':
                year = 1925 + y
            elif era == '平成':
                year = 1988 + y
            elif era == '令和':
                year = 2018 + y
            try:
                date = datetime(year, m_, d)
                print(f"[OCR] 和暦から変換された日付: {date}")
                candidate_dates.append(date)
            except:
                print(f"[OCR] 和暦日付変換エラー: {year}/{m_}/{d}")
                continue
            continue  # 両方マッチしないように（重複防止）

        # 西暦チェック
        m = seireki_pattern.search(chunk)
        if m:
            print(f"[OCR] 西暦マッチ: {m.groups()}")
            y, m_, d = map(int, m.groups())
            try:
                date = datetime(y, m_, d)
                print(f"[OCR] 西暦日付: {date}")
                candidate_dates.append(date)
            except:
                print(f"[OCR] 西暦日付変換エラー: {y}/{m_}/{d}")
                continue
                
    print(f"[OCR] 候補日付: {candidate_dates}")
    
    age = 0
    # 最古の日付を生年月日とみなす
    if candidate_dates:
        birthdate = min(candidate_dates)
        today = datetime.today()
        age = today.year - birthdate.year - ((today.month, today.day) < (birthdate.month, birthdate.day))
        print(f"[OCR] 推定生年月日: {birthdate.strftime('%Y年%m月%d日')}")
        print(f"[OCR] 推定年齢: {age}歳")
    else:
        print(f"[OCR] 日付情報が見つかりませんでした。")
    
    print(f"[OCR] 年齢認証処理完了: age={age}")
    return age
