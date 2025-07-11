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
        "birthdate": user.birthdate,
        "living_place": user.living_place or "",
        "gender": user.gender or "",
        "is_certificated": user.is_certificated if hasattr(user, "is_certificated") else False,
        "is_age_verified": user.age_verification_status == 'approved' if hasattr(user, "age_verification_status") else False
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

@protected_bp.route("/update-profile", methods=["PUT"])
def update_profile():
    user, error_response, error_code = get_authenticated_user()
    if error_response:
        return jsonify(error_response), error_code

    data = request.get_json()

    # ユーザー基本情報更新
    user.user_name = data.get("user_name", user.user_name)
    user.profile_message = data.get("profile_message", user.profile_message)
    user.birthdate = data.get("birthdate", user.birthdate)
    user.living_place = data.get("living_place", user.living_place)
    user.gender = data.get("gender", user.gender)

    # 🔽 タグ更新処理
    tag_names = data.get("favorite_tags", [])
    if isinstance(tag_names, list):
        # 現在のタグ関連を全削除
        UserTagAssociation.query.filter_by(user_id=user.id).delete()

        for tag_name in tag_names:
            tag = TagMaster.query.filter_by(tag_name=tag_name).first()
            if tag:
                new_assoc = UserTagAssociation(
                    id=str(uuid.uuid4()),
                    user_id=user.id,
                    tag_id=tag.id,
                    created_at=datetime.now(timezone.utc)
                )
                db.session.add(new_assoc)

    db.session.commit()

    return jsonify({"message": "プロフィールを更新しました", "user": user.to_dict()})
