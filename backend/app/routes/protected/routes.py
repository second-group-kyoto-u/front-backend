from flask import Blueprint, request, jsonify
from app.utils.jwt import decode_token
from app.models.user import User
from app.models.event import Event, UserMemberGroup, TagMaster, UserTagAssociation
from app.models.message import FriendRelationship
from app.models import db
import uuid
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

protected_bp = Blueprint("protected", __name__)

# ユーザー認証を確認するヘルパー関数
def get_authenticated_user():
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None, {"error": "認証トークンがありません"}, 401

    token = auth_header.split()[1]
    user_id = decode_token(token)
    if not user_id:
        return None, {"error": "無効または期限切れのトークンです"}, 401

    user = User.query.get(user_id)
    if not user:
        return None, {"error": "ユーザーが見つかりません"}, 404

    return user, None, None

@protected_bp.route("/mypage", methods=["GET", "OPTIONS"])
def mypage():
    if request.method == "OPTIONS":
        # Flask-CORSがヘッダーを追加してくれるので、空の200 OKで返して良い
        print("🧪 OPTIONSリクエスト受信")
        return '', 204
    
    # ユーザー認証
    user, error_response, error_code = get_authenticated_user()
    if error_response:
        return jsonify(error_response), error_code
    
    # ユーザーのタグを取得
    user_tags = UserTagAssociation.query.filter_by(
        user_id=user.id
    ).all()
    
    favorite_tags = []
    for assoc in user_tags:
        tag = TagMaster.query.get(assoc.tag_id)
        if tag:
            favorite_tags.append(tag.tag_name)
    
    # ユーザーが参加しているイベント数を取得
    joined_events_count = UserMemberGroup.query.filter_by(user_id=user.id).count()
    
    # ユーザーデータをJSON形式で返す
    user_data = {
        "id": user.id,
        "user_name": user.user_name,
        "profile_message": user.profile_message or "",
        "profile_image_url": user.user_image_url or "",
        "age": 999,
        "location":"sample area",
        "gender":"sample gender",
    }

    # イベントデータをJSON形式で返す
    created_events = [
    {
        "id": event.id,
        "title": event.title,
        "description": event.description
    }
    for event in Event.query.filter_by(author_user_id=user.id).all()
]

    
    return jsonify({
        "user": user_data,
        "joined_events_count": joined_events_count,
        "favorite_tags": favorite_tags,
        "created_events": created_events,
        "message": f"ようこそ、{user.user_name}さん！"
    })