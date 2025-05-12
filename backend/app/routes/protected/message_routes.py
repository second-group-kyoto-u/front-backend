from flask import Blueprint, request, jsonify
from app.routes.protected.routes import get_authenticated_user
from app.models.user import User
from app.models.event import Event, UserMemberGroup
from app.models.message import EventMessage, MessageReadStatus
from app.models import db
import uuid
from datetime import datetime, timezone, timedelta
import json

JST = timezone(timedelta(hours=9))

message_bp = Blueprint("message", __name__)

# イベントメッセージ関連のAPI
@message_bp.route("/event/<event_id>/messages", methods=["GET"])
def get_event_messages(event_id):
    # ユーザー認証
    user, error_response, error_code = get_authenticated_user()
    if error_response:
        return jsonify(error_response), error_code
    
    # イベントの取得
    event = Event.query.get(event_id)
    if not event:
        return jsonify({"error": "イベントが見つかりません"}), 404
    
    # 参加しているか確認（イベント作成者または参加者のみメッセージを閲覧可能）
    if event.author_user_id != user.id:
        is_member = UserMemberGroup.query.filter_by(
            user_id=user.id,
            event_id=event_id
        ).first()
        
        if not is_member:
            return jsonify({"error": "このイベントのメッセージを閲覧する権限がありません"}), 403
    
    # クエリパラメータ
    limit = request.args.get('limit', default=50, type=int)
    offset = request.args.get('offset', default=0, type=int)
    
    # メッセージを取得（新しい順）
    messages = EventMessage.query.filter_by(
        event_id=event_id
    ).order_by(
        EventMessage.timestamp.desc()
    ).offset(offset).limit(limit).all()
    
    # 結果を整形
    result = []
    for message in messages:
        result.append(message.to_dict())
    
    # 未読メッセージを既読にする
    for message in messages:
        # 自分のメッセージは既読にしない
        if message.sender_user_id == user.id:
            continue
        
        # 既に既読か確認
        read_status = MessageReadStatus.query.filter_by(
            message_id=message.id,
            user_id=user.id
        ).first()
        
        if not read_status:
            # 既読ステータスを作成
            read_status = MessageReadStatus(
                message_id=message.id,
                user_id=user.id,
                read_at=datetime.now(JST)
            )
            db.session.add(read_status)
    
    db.session.commit()
    
    # 新しい順で返されたメッセージを古い順に並び替えて返す
    result.reverse()
    
    return jsonify({"messages": result, "total": len(result)})

@message_bp.route("/event/<event_id>/message", methods=["POST"])
def send_event_message(event_id):
    # ユーザー認証
    user, error_response, error_code = get_authenticated_user()
    if error_response:
        return jsonify(error_response), error_code
    
    # イベントの取得
    event = Event.query.get(event_id)
    if not event:
        return jsonify({"error": "イベントが見つかりません"}), 404
    
    # 参加しているか確認（イベント作成者または参加者のみメッセージを送信可能）
    if event.author_user_id != user.id:
        is_member = UserMemberGroup.query.filter_by(
            user_id=user.id,
            event_id=event_id
        ).first()
        
        if not is_member:
            return jsonify({"error": "このイベントにメッセージを送信する権限がありません"}), 403
    
    # リクエストデータの取得
    data = request.get_json()
    content = data.get('content')
    image_id = data.get('image_id')
    message_type = data.get('message_type', 'text')
    metadata = data.get('metadata')
    
    # バリデーション
    if message_type == 'text' and not content:
        return jsonify({"error": "テキストメッセージにはcontentが必須です"}), 400
    
    if message_type == 'image' and not image_id:
        return jsonify({"error": "画像メッセージにはimage_idが必須です"}), 400
    
    # メッセージの作成
    message = EventMessage(
        id=str(uuid.uuid4()),
        event_id=event_id,
        sender_user_id=user.id,
        content=content,
        timestamp=datetime.now(JST),
        image_id=image_id,
        message_type=message_type,
        metadata=json.dumps(metadata) if metadata else None
    )
    
    db.session.add(message)
    db.session.commit()
    
    return jsonify({
        "message": "メッセージを送信しました",
        "event_message": message.to_dict()
    }) 