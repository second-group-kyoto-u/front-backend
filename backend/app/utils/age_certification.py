# 身分証から生年月日を抽出し18歳以上かを確認するための画像認識プログラムを書く
import easyocr
import re
from datetime import datetime

reader = easyocr.Reader(['ja', 'en'])

# 画像を読み込む(実験段階では画像をパスで指定しているが、実際はユーザが画像を送ってDBに登録？した画像を用いる)
image_path = 'license_sample.jpg'
results = reader.readtext(image_path, detail=0)
print(results)