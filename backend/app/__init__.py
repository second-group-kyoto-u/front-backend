from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv
import os


def create_app():
    load_dotenv()  # ← .env を読み込む
    app = Flask(__name__)
    CORS(app)  # これで全オリジンからのリクエストを許可

    app.config['ENV'] = os.getenv('FLASK_ENV', 'production') # FLASK_ENVに値を入れてたら自動的に開発モード（development）になる。本番では絶対に debug=True にしない：セキュリティリスクが極めて高くなるから。アプリの内部情報（ソースコード・環境変数・サーバー情報）まで外部から丸見えになる。。
    app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', '') # .env に FLASK_SECRET_KEY が定義されてなければ 'fallback-key' を代わりに使うことで、開発中の事故防止

    # Blueprint登録（example_bp というBlueprintをFlaskのappのモジュールとして追加。ルートの先頭に /api を付けて登録する）
    from app.routes.protected.routes import protected_bp
    app.register_blueprint(protected_bp, url_prefix="/api")

    from app.routes.auth.routes import auth_bp
    app.register_blueprint(auth_bp, url_prefix="/api")


    return app
