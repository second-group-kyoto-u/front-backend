from flask import Blueprint, request, jsonify
from app.utils.jwt import decode_token
from app.models.user import User
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

protected_bp = Blueprint("protected", __name__)

@protected_bp.route("/mypage", methods=["GET"])
def mypage():
    auth_header = request.headers.get("Authorization")
    logger.info("📥 Authorizationヘッダー: %s", auth_header)
    
    if not auth_header or not auth_header.startswith("Bearer "):
        logger.warning("⚠️ トークンが存在しない")
        return jsonify({"error": "Missing token"}), 401

    token = auth_header.split()[1]
    user_id = decode_token(token)
    if not user_id:
        logger.error("❌ トークン不正 or 期限切れ")
        return jsonify({"error": "Invalid or expired token"}), 401

    logger.info("✅ 認証成功, user_id=%s", user_id)

    # 🔽 ユーザー情報を取得
    user = User.query.get(user_id)
    if not user:
        logger.error("❌ ユーザーが見つかりません: user_id=%s", user_id)
        return jsonify({"error": "ユーザーが存在しません"}), 404

    return jsonify({
        "message": f"ようこそ、ユーザーID {user_id} さん！",
        "profile_image_url": user.profile_image_url or ""
    })