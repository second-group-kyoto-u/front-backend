from flask import Flask, request
from flask_cors import CORS
from dotenv import load_dotenv
import os
from app.models import db
import pymysql
from app.models.user import User
from app.models.area import AreaList
from app.models.thread import Thread, ThreadMessage, UserHeartThread
from flask_jwt_extended import JWTManager

# MySQLをSQLAlchemyに接続するためのセットアップ
pymysql.install_as_MySQLdb()

def create_app():
    env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../.env'))
    load_dotenv()  # ← .env を読み込む

    app = Flask(__name__)
    
    # CORS設定
    # 環境変数から許可するオリジンのリストを取得
    cors_allowed = os.getenv('CORS_ALLOWED', 'http://localhost:3000')
    allowed_origins = cors_allowed.split(',')
    
    # より詳細なCORS設定 - 特定のオリジンを許可
    cors = CORS(app,
        resources={r"/*": {"origins": allowed_origins}},  # 環境変数で指定されたオリジンを許可
        supports_credentials=True,  # Cookieの送受信を許可
        methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization", "X-Requested-With"])
    
    app.logger.info(f"CORS設定: 許可オリジン = {allowed_origins}")

    # エラーハンドラーを追加して、500エラー時にもCORSヘッダーを設定
    @app.errorhandler(500)
    def handle_500_error(e):
        # エラーメッセージをログ記録
        app.logger.error(f"500エラー: {str(e)}")
        
        # リクエスト元のオリジンを取得
        origin = request.headers.get('Origin', allowed_origins[0] if allowed_origins else 'http://localhost:3000')
        
        # レスポンスを作成
        response = app.response_class(
            response='{"error": "内部サーバーエラーが発生しました"}',
            status=500,
            mimetype='application/json'
        )
        
        # CORSヘッダーを追加
        response.headers['Access-Control-Allow-Origin'] = origin
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With'
        
        return response

    app.config['ENV'] = os.getenv('FLASK_ENV', 'production') # FLASK_ENVに値を入れてたら自動的に開発モード（development）になる。本番では絶対に debug=True にしない：セキュリティリスクが極めて高くなるから。アプリの内部情報（ソースコード・環境変数・サーバー情報）まで外部から丸見えになる。。
    app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', '') # .env に FLASK_SECRET_KEY が定義されてなければ 'fallback-key' を代わりに使うことで、開発中の事故防止
    
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # JWT設定
    app.config['JWT_SECRET_KEY'] = app.config['SECRET_KEY']
    app.config['JWT_TOKEN_LOCATION'] = ['headers']
    app.config['JWT_HEADER_NAME'] = 'Authorization'
    app.config['JWT_HEADER_TYPE'] = 'Bearer'
    jwt = JWTManager(app)

    # アップロードフォルダ設定
    app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'uploads')

    # SQLAlchemyとFlaskを接続
    db.init_app(app)

    # Blueprint登録（example_bp というBlueprintをFlaskのappのモジュールとして追加。ルートの先頭に /api を付けて登録する）
    from app.routes.protected.routes import protected_bp
    app.register_blueprint(protected_bp, url_prefix="/api/protected")

    from app.routes.auth.routes import auth_bp
    app.register_blueprint(auth_bp, url_prefix="/api/auth")

    from app.routes.protected.thread_routes import thread_bp
    app.register_blueprint(thread_bp, url_prefix="/api/thread")

    from app.routes.upload.routes import upload_bp
    app.register_blueprint(upload_bp, url_prefix="/api/upload")

    from app.routes.protected.event_routes import event_bp
    app.register_blueprint(event_bp, url_prefix="/api/event")
    
    from app.routes.protected.message_routes import message_bp
    app.register_blueprint(message_bp, url_prefix="/api/message")
    
    from app.routes.protected.friend_routes import friend_bp
    app.register_blueprint(friend_bp, url_prefix="/api/friend")
    
    from app.routes.user_routes import user_bp
    app.register_blueprint(user_bp, url_prefix="/api/user")

    from app.routes.area_routes import area_bp
    app.register_blueprint(area_bp, url_prefix="/api/area")


    # modelsに定義されたモデルクラスと見て、対応するテーブルをデータベースに作成し、appではモデルクラスを介してデータベーステーブルと対話する。
    with app.app_context():
        db.create_all()
        
        # ストレージの初期化（バケットの確認/作成）
        try:
            from app.utils.storage import ensure_bucket_exists
            
            bucket_name = os.getenv('MINIO_BUCKET')
            if bucket_name:
                ensure_bucket_exists(bucket_name)
        except Exception as e:
            app.logger.error(f"ストレージ初期化エラー: {e}")
    
    return app