## venv(仮想環境)の設定
'''
python3 -m venv venv
'''
### venvのアクティベート
'''
source venv/bin/activate
'''
### Flaskのインストール(仮想環境内で)
'''
pip install Flask
'''
## 動作確認
'''(仮想環境内で)
pip install -r requirements.txt
pip install flask-cors
python run.py
http://localhost:5000/api/hello 5000 ポートの/api/helloにアクセス
'''



<メモ>
## python-dotenv とは？
.env ファイルに書かれた環境変数を自動で読み込んでくれるライブラリ（セキュリティ用）
「秘密の設定（DB接続情報やAPIキーなど）」をコードに直書きせず、安全に管理するために使う
例）
DATABASE_URL=mysql://user:pass@localhost/dbname
FLASK_ENV=development

## Flaskの Blueprint とは？
Flaskではアプリを機能単位に分割するために「Blueprint（設計図）」を使う。
ルート（ルーティング処理）を分けて管理できる仕組み