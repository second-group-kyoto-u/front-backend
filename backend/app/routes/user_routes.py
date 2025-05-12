from flask import Blueprint, jsonify, request
from app.models.user import User, get_user_by_id
from app.models import db
from app.routes.protected.routes import get_authenticated_user
from app.models.event import Event, UserMemberGroup, UserTagAssociation
from app.models.message import FriendRelationship
import uuid
from datetime import datetime, timezone, timedelta

JST = timezone(timedelta(hours=9))  # 日本標準時

user_bp = Blueprint("user", __name__)

@user_bp.route("/<user_id>/profile", methods=["GET"])
def get_user_profile(user_id):
    """
    ユーザーのプロフィール情報を取得するAPI
    認証は不要（公開プロフィール）
    """
    try:
        user = get_user_by_id(user_id)
        if not user:
            return jsonify({"error": "ユーザーが見つかりません"}), 404

        current_user, error_response, error_code = get_authenticated_user()
        is_authenticated = current_user is not None

        joined_events_count = UserMemberGroup.query.filter_by(user_id=user_id).count()

        user_tags = db.session.query(UserTagAssociation).join(
            UserTagAssociation.tag
        ).filter(
            UserTagAssociation.user_id == user_id
        ).all()
        
        favorite_tags = [tag_assoc.tag.tag_name for tag_assoc in user_tags]

        created_events = Event.query.filter_by(
            author_user_id=user_id, 
            is_deleted=False
        ).order_by(
            Event.published_at.desc()
        ).limit(5).all()

        events_data = []
        for event in created_events:
            events_data.append({
                "id": event.id,
                "title": event.title,
                "description": event.description,
                "published_at": event.published_at.isoformat() if event.published_at else None,
                "current_persons": event.current_persons,
                "limit_persons": event.limit_persons,
                "status": event.status,
                "image_url": event.image.image_url if event.image else None
            })

        follow_status = {
            "is_following": False,
            "is_followed_by": False,
            "relationship_id": None,
            "relationship_status": None
        }

        if is_authenticated and current_user.id != user_id:
            following_relationship = FriendRelationship.query.filter_by(
                user_id=current_user.id,
                friend_id=user_id
            ).first()
            
            followed_by_relationship = FriendRelationship.query.filter_by(
                user_id=user_id,
                friend_id=current_user.id
            ).first()
            
            if following_relationship:
                follow_status["is_following"] = True
                follow_status["relationship_id"] = following_relationship.id
                follow_status["relationship_status"] = following_relationship.status
            
            if followed_by_relationship:
                follow_status["is_followed_by"] = True

        response_data = {
            "user": {
                "id": user.id,
                "user_name": user.user_name,
                "profile_message": user.profile_message,
                "user_image_url": user.user_image_url,
                "is_certificated": user.is_certificated,
                "email_verified": user.email_verified
            },
            "joined_events_count": joined_events_count,
            "favorite_tags": favorite_tags,
            "created_events": events_data,
            "follow_status": follow_status,
            "is_authenticated": is_authenticated
        }

        return jsonify(response_data)

    except Exception as e:
        print(f"ユーザープロフィール取得エラー: {str(e)}")
        return jsonify({"error": "ユーザープロフィールの取得中にエラーが発生しました"}), 500

@user_bp.route("/<user_id>/follow", methods=["POST"])
def follow_user(user_id):
    """
    ユーザーをフォローするAPI（フレンドリクエスト送信）
    """
    user, error_response, error_code = get_authenticated_user()
    if error_response:
        return jsonify(error_response), error_code
    
    if user.id == user_id:
        return jsonify({"error": "自分自身をフォローすることはできません"}), 400
    
    target_user = User.query.get(user_id)
    if not target_user:
        return jsonify({"error": "ユーザーが見つかりません"}), 404
    
    existing_relationship = FriendRelationship.query.filter_by(
        user_id=user.id,
        friend_id=user_id
    ).first()
    
    if existing_relationship:
        return jsonify({
            "message": "既にフォロー済みです",
            "relationship": {
                "id": existing_relationship.id,
                "status": existing_relationship.status
            }
        })
    
    relationship = FriendRelationship(
        id=str(uuid.uuid4()),
        user_id=user.id,
        friend_id=user_id,
        status='pending',
        created_at=datetime.now(JST),
        updated_at=datetime.now(JST)
    )
    
    db.session.add(relationship)
    db.session.commit()
    
    return jsonify({
        "message": "フォローリクエストを送信しました",
        "relationship": {
            "id": relationship.id,
            "status": relationship.status
        }
    })

@user_bp.route("/<user_id>/unfollow", methods=["POST"])
def unfollow_user(user_id):
    """
    ユーザーのフォローを解除するAPI
    """
    user, error_response, error_code = get_authenticated_user()
    if error_response:
        return jsonify(error_response), error_code
    
    if user.id == user_id:
        return jsonify({"error": "自分自身のフォローを解除することはできません"}), 400
    
    relationship = FriendRelationship.query.filter_by(
        user_id=user.id,
        friend_id=user_id
    ).first()
    
    if not relationship:
        return jsonify({"message": "フォローしていません"}), 200
    
    db.session.delete(relationship)
    db.session.commit()
    
    return jsonify({"message": "フォローを解除しました"})
