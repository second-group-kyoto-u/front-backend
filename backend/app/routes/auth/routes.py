from flask import Blueprint, request, jsonify
from app.utils.jwt import generate_token
from app.models.user import get_user_by_email, verify_password

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    print("🔑 login リクエスト:", data)
    email = data.get('email')
    password = data.get('password')

    user = get_user_by_email(email)
    if not user:
        print("❌ ユーザーが見つかりません:", email)
        return jsonify({"error": "ユーザーが存在しません"}), 401

    if not verify_password(user["password"], password):
        print("❌ パスワード不一致:", password)
        return jsonify({"error": "パスワードが間違っています"}), 401

    token = generate_token(user["id"]) # DBと入力値のハッシュが一致した時
    print("✅ トークン生成成功:", token)
    return jsonify({"token": token})