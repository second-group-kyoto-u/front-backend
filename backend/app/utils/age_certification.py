# 身分証から生年月日を抽出し18歳以上かを確認するための画像認識プログラムを書く
import easyocr
import re
from datetime import datetime
import cv2
import numpy as np
from ultralytics import YOLO
from PIL import Image

# reader = easyocr.Reader(['ja', 'en'])

# 画像を読み込む(実験段階では画像をパスで指定しているが、実際はユーザが画像を送ってDBに登録？した画像を用いる)
image_path = 'mynumber.jpg'
image = cv2.imread(image_path)

# YOLOで生年月日欄を検出
model = YOLO('best.pt')
results = model(image_path, conf=0.25)
# YOLOで検出された領域のうち、最もスコアが高い1つを対象にする
# box = results[0].boxes.xyxy[0].cpu().numpy().astype(int)
# x1, y1, x2, y2 = box
# cropped = image[y1:y2, x1:x2]
# cv2.imwrite('cropped_birth.jpg', cropped)

print(results)

# # OCR実行
# reader = easyocr.Reader(['ja'])
# text_results = reader.readtext("学生証.jpg", contrast_ths=0.05, adjust_contrast=0.7, decoder='beamsearch', detail=0)  # テキストのみ抽出
# joined_text = ''.join(text_results)

# # --------------------------
# # STEP 4: 生年月日を抽出し、年齢を計算
# # --------------------------
# def convert_to_date(text):
#     # 和暦または西暦対応
#     m = re.search(r'(昭和|平成|令和)?\s*(\d+)\s*[年\.]?\s*(\d+)\s*[月\.]?\s*(\d+)', text)
#     if not m:
#         return None
#     era, year, month, day = m.groups()
#     year, month, day = int(year), int(month), int(day)
    
#     if era == '昭和':
#         year += 1925
#     elif era == '平成':
#         year += 1988
#     elif era == '令和':
#         year += 2018
#     elif not era and year > 1900:  # 西暦
#         pass
#     else:
#         return None
    
#     try:
#         return datetime(year, month, day)
#     except ValueError:
#         return None

# birth_date = convert_to_date(joined_text)

# if birth_date:
#     today = datetime.today()
#     age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
#     print(f'抽出された生年月日: {birth_date.strftime("%Y-%m-%d")}')
#     print(f'現在の年齢: {age}歳')
# else:
#     print('生年月日の抽出に失敗しました。')



