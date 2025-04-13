from flask import Blueprint, request, jsonify
from app.utils.jwt import generate_token
from app.models.user import get_user_by_email

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    user = get_user_by_email(email)
    if not user:
        return jsonify({"error": "ユーザーが存在しません"}), 401

    if not user.check_password(password):
        return jsonify({"error": "パスワードが間違っています"}), 401

    token = generate_token(user.id)
    return jsonify({"token": token})
