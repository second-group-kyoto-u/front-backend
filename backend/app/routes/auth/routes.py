from flask import Blueprint, request, jsonify
from app.utils.jwt import generate_token, decode_token
from app.models.user import get_user_by_email, get_user_by_id, User
from app.models import db
from backend.app.utils.email_certification import send_email_verification, send_password_reset_email, verify_token
import uuid
from datetime import datetime, timezone

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    user = get_user_by_email(email)
    if not user:
        # セキュリティのために具体的なエラー原因を隠す
        return jsonify({"error": "メールアドレスが異なっています。"}), 401

    if not user.check_password(password):
        # セキュリティのために具体的なエラー原因を隠す
        return jsonify({"error": "パスワードが異なっています。"}), 401

    # ログイン日時を記録
    user.record_login()
    db.session.commit()
    
    token = generate_token(user.id)
    return jsonify({"token": token})

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    user_name = data.get('userName')
    
    # バリデーション
    if not email or not password or not user_name:
        return jsonify({"error": "必須フィールドが不足しています"}), 400
    
    # メールアドレスの重複チェック
    existing_user = get_user_by_email(email)
    if existing_user:
        return jsonify({"error": "このメールアドレスは既に登録されています"}), 400
    
    # 新規ユーザー作成
    user = User(
        id=str(uuid.uuid4()),
        user_name=user_name,
        email_address=email,
        profile_message="",
        is_certificated=False,
        email_verified=False,
        created_at=datetime.now(timezone.utc)
    )
    user.set_password(password)
    
    db.session.add(user)
    db.session.commit()
    
    # メール認証メールを送信
    send_email_verification(user)
    
    # ログイントークン発行
    token = generate_token(user.id)
    return jsonify({
        "token": token, 
        "message": "ユーザー登録が完了しました。メールアドレスの認証を行ってください。",
        "user": user.to_dict()
    })

@auth_bp.route('/verify-email/<token>', methods=['GET'])
def verify_email(token):
    # トークンを検証
    payload = verify_token(token)
    if not payload or payload.get('action') != 'email_verification':
        return jsonify({"error": "無効または期限切れのトークンです"}), 400
    
    user_id = payload.get('user_id')
    user = get_user_by_id(user_id)
    if not user:
        return jsonify({"error": "ユーザーが見つかりません"}), 404
    # 既に登録済みのメールアドレスである場合
    if user.is_certificated:
        return jsonify({"error": "既に認証済みのメールアドレスです"}), 409
    
    # メール認証を完了
    user.verify_email()
    db.session.commit()
    
    return jsonify({"message": "メールアドレスの認証が完了しました"})

@auth_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    data = request.get_json()
    email = data.get('email')
    
    if not email:
        return jsonify({"error": "メールアドレスを入力してください"}), 400
    
    user = get_user_by_email(email)
    if not user:
        # セキュリティ上の理由から、ユーザーが存在しなくても同じメッセージを返す
        return jsonify({"message": "パスワードリセットの手順をメールで送信しました"}), 200
    
    # パスワードリセットメールを送信
    send_password_reset_email(user)
    
    return jsonify({"message": "パスワードリセットの手順をメールで送信しました"})

@auth_bp.route('/reset-password/<token>', methods=['POST'])
def reset_password(token):
    # トークンを検証
    payload = verify_token(token)
    if not payload or payload.get('action') != 'password_reset':
        return jsonify({"error": "無効または期限切れのトークンです"}), 400
    
    data = request.get_json()
    new_password = data.get('password')
    
    if not new_password:
        return jsonify({"error": "新しいパスワードを入力してください"}), 400
    
    user_id = payload.get('user_id')
    user = get_user_by_id(user_id)
    if not user:
        return jsonify({"error": "ユーザーが見つかりません"}), 404
    
    # パスワードを更新
    user.set_password(new_password)
    db.session.commit()
    
    return jsonify({"message": "パスワードが正常に更新されました"})

@auth_bp.route('/resend-verification', methods=['POST'])
def resend_verification():
    data = request.get_json()
    email = data.get('email')
    
    if not email:
        return jsonify({"error": "メールアドレスを入力してください"}), 400
    
    user = get_user_by_email(email)
    if not user:
        return jsonify({"error": "ユーザーが見つかりません"}), 404
    
    if user.email_verified:
        return jsonify({"message": "既にメール認証が完了しています"}), 200
    
    # 認証メールを再送
    send_email_verification(user)
    
    return jsonify({"message": "認証メールを再送しました"})

@auth_bp.route('/verify', methods=['GET'])
def verify_token_route():
    auth_header = request.headers.get('Authorization')
    
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({"error": "認証トークンがありません"}), 401
        
    token = auth_header.split()[1]
    user_id = decode_token(token)
    
    if not user_id:
        return jsonify({"error": "無効または期限切れのトークンです"}), 401
        
    user = get_user_by_id(user_id)
    if not user:
        return jsonify({"error": "ユーザーが見つかりません"}), 404
        
    return jsonify({"message": "トークンは有効です", "user_id": user_id})
