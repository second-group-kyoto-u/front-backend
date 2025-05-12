from flask import Blueprint, request, jsonify
from app.routes.protected.routes import get_authenticated_user
from app.models.user import User
from app.models.message import FriendRelationship, DirectMessage
from app.models import db
import uuid
from datetime import datetime, timezone, timedelta
import json

JST = timezone(timedelta(hours=9))


friend_bp = Blueprint("friend", __name__)

# フレンド一覧の取得
@friend_bp.route("/friends", methods=["GET"])
def get_friends():
    # ユーザー認証
    user, error_response, error_code = get_authenticated_user()
    if error_response:
        return jsonify(error_response), error_code
    
    # 承認済みのフレンド関係を取得
    sent_requests = FriendRelationship.query.filter_by(
        user_id=user.id,
        status='accepted'
    ).all()
    
    received_requests = FriendRelationship.query.filter_by(
        friend_id=user.id,
        status='accepted'
    ).all()
    
    # フレンドリスト作成
    friends = []
    
    # 自分がリクエストを送った側のフレンド
    for request in sent_requests:
        friend = User.query.get(request.friend_id)
        if friend:
            friends.append({
                "user": friend.to_dict(),
                "relationship_id": request.id,
                "since": request.updated_at.isoformat()
            })
    
    # 自分がリクエストを受けた側のフレンド
    for request in received_requests:
        friend = User.query.get(request.user_id)
        if friend:
            friends.append({
                "user": friend.to_dict(),
                "relationship_id": request.id,
                "since": request.updated_at.isoformat()
            })
    
    return jsonify({"friends": friends, "total": len(friends)})

# フレンドリクエスト一覧の取得
@friend_bp.route("/friend-requests", methods=["GET"])
def get_friend_requests():
    # ユーザー認証
    user, error_response, error_code = get_authenticated_user()
    if error_response:
        return jsonify(error_response), error_code
    
    # 保留中のフレンドリクエスト（自分宛）を取得
    pending_requests = FriendRelationship.query.filter_by(
        friend_id=user.id,
        status='pending'
    ).all()
    
    # 送信したリクエスト（自分から）を取得
    sent_requests = FriendRelationship.query.filter_by(
        user_id=user.id,
        status='pending'
    ).all()
    
    # 結果を整形
    received = []
    for request in pending_requests:
        sender = User.query.get(request.user_id)
        if sender:
            received.append({
                "id": request.id,
                "sender": sender.to_dict(),
                "created_at": request.created_at.isoformat()
            })
    
    sent = []
    for request in sent_requests:
        receiver = User.query.get(request.friend_id)
        if receiver:
            sent.append({
                "id": request.id,
                "receiver": receiver.to_dict(),
                "created_at": request.created_at.isoformat()
            })
    
    return jsonify({
        "received": received,
        "sent": sent
    })

# フレンドリクエストの送信
@friend_bp.route("/friend-request", methods=["POST"])
def send_friend_request():
    # ユーザー認証
    user, error_response, error_code = get_authenticated_user()
    if error_response:
        return jsonify(error_response), error_code
    
    # リクエストデータの取得
    data = request.get_json()
    friend_id = data.get('friend_id')
    
    # バリデーション
    if not friend_id:
        return jsonify({"error": "friend_idは必須です"}), 400
    
    if friend_id == user.id:
        return jsonify({"error": "自分自身にフレンドリクエストを送れません"}), 400
    
    # 相手ユーザーの存在確認
    friend = User.query.get(friend_id)
    if not friend:
        return jsonify({"error": "指定されたユーザーが見つかりません"}), 404
    
    # 既存の関係をチェック
    existing_relationship = FriendRelationship.query.filter(
        ((FriendRelationship.user_id == user.id) & (FriendRelationship.friend_id == friend_id)) |
        ((FriendRelationship.user_id == friend_id) & (FriendRelationship.friend_id == user.id))
    ).first()
    
    if existing_relationship:
        if existing_relationship.status == 'accepted':
            return jsonify({"error": "既にフレンドです"}), 400
        
        elif existing_relationship.status == 'pending':
            # 相手からのリクエストがある場合
            if existing_relationship.user_id == friend_id:
                # 承認する
                existing_relationship.status = 'accepted'
                existing_relationship.updated_at = datetime.now(JST)
                db.session.commit()
                
                return jsonify({
                    "message": "フレンドリクエストを承認しました",
                    "relationship": existing_relationship.to_dict()
                })
            
            # 自分からのリクエストがある場合
            else:
                return jsonify({"error": "既にフレンドリクエストを送信済みです"}), 400
    
    # 新規リクエストを作成
    relationship = FriendRelationship(
        id=str(uuid.uuid4()),
        user_id=user.id,
        friend_id=friend_id,
        status='pending',
        created_at=datetime.now(JST),
        updated_at=datetime.now(JST)
    )
    
    db.session.add(relationship)
    db.session.commit()
    
    return jsonify({
        "message": "フレンドリクエストを送信しました",
        "relationship": relationship.to_dict()
    })

# フレンドリクエストの承認
@friend_bp.route("/friend-request/<request_id>/accept", methods=["POST"])
def accept_friend_request(request_id):
    # ユーザー認証
    user, error_response, error_code = get_authenticated_user()
    if error_response:
        return jsonify(error_response), error_code
    
    # リクエストの取得
    request = FriendRelationship.query.get(request_id)
    if not request:
        return jsonify({"error": "リクエストが見つかりません"}), 404
    
    # リクエスト受信者の確認
    if request.friend_id != user.id:
        return jsonify({"error": "このリクエストを承認する権限がありません"}), 403
    
    # 既に処理済みかチェック
    if request.status != 'pending':
        return jsonify({"error": "このリクエストは既に処理されています"}), 400
    
    # リクエスト承認
    request.status = 'accepted'
    request.updated_at = datetime.now(JST)
    
    db.session.commit()
    
    return jsonify({
        "message": "フレンドリクエストを承認しました",
        "relationship": request.to_dict()
    })

# フレンドリクエストの拒否
@friend_bp.route("/friend-request/<request_id>/reject", methods=["POST"])
def reject_friend_request(request_id):
    # ユーザー認証
    user, error_response, error_code = get_authenticated_user()
    if error_response:
        return jsonify(error_response), error_code
    
    # リクエストの取得
    request = FriendRelationship.query.get(request_id)
    if not request:
        return jsonify({"error": "リクエストが見つかりません"}), 404
    
    # リクエスト受信者の確認
    if request.friend_id != user.id:
        return jsonify({"error": "このリクエストを拒否する権限がありません"}), 403
    
    # 既に処理済みかチェック
    if request.status != 'pending':
        return jsonify({"error": "このリクエストは既に処理されています"}), 400
    
    # リクエスト拒否
    request.status = 'rejected'
    request.updated_at = datetime.now(JST)
    
    db.session.commit()
    
    return jsonify({
        "message": "フレンドリクエストを拒否しました"
    })

# ダイレクトメッセージの取得
@friend_bp.route("/direct-messages/<friend_id>", methods=["GET"])
def get_direct_messages(friend_id):
    # ユーザー認証
    user, error_response, error_code = get_authenticated_user()
    if error_response:
        return jsonify(error_response), error_code
    
    # フレンド関係の確認
    is_friend = FriendRelationship.query.filter(
        ((FriendRelationship.user_id == user.id) & (FriendRelationship.friend_id == friend_id)) |
        ((FriendRelationship.user_id == friend_id) & (FriendRelationship.friend_id == user.id)),
        FriendRelationship.status == 'accepted'
    ).first()
    
    if not is_friend:
        return jsonify({"error": "フレンドのメッセージのみ閲覧できます"}), 403
    
    # クエリパラメータ
    limit = request.args.get('limit', default=50, type=int)
    offset = request.args.get('offset', default=0, type=int)
    
    # メッセージを取得（新しい順）
    messages = DirectMessage.query.filter(
        ((DirectMessage.sender_id == user.id) & (DirectMessage.receiver_id == friend_id)) |
        ((DirectMessage.sender_id == friend_id) & (DirectMessage.receiver_id == user.id))
    ).order_by(
        DirectMessage.sent_at.desc()
    ).offset(offset).limit(limit).all()
    
    # 結果を整形
    result = []
    for message in messages:
        result.append(message.to_dict())
    
    # 自分宛の未読メッセージを既読にする
    for message in messages:
        if message.receiver_id == user.id and not message.is_read:
            message.is_read = True
            message.read_at = datetime.now(JST)
    
    db.session.commit()
    
    # 新しい順で返されたメッセージを古い順に並び替えて返す
    result.reverse()
    
    return jsonify({"messages": result, "total": len(result)})

# ダイレクトメッセージの送信
@friend_bp.route("/direct-message", methods=["POST"])
def send_direct_message():
    # ユーザー認証
    user, error_response, error_code = get_authenticated_user()
    if error_response:
        return jsonify(error_response), error_code
    
    # リクエストデータの取得
    data = request.get_json()
    receiver_id = data.get('receiver_id')
    content = data.get('content')
    image_id = data.get('image_id')
    message_type = data.get('message_type', 'text')
    metadata = data.get('metadata')
    
    # バリデーション
    if not receiver_id:
        return jsonify({"error": "receiver_idは必須です"}), 400
    
    if message_type == 'text' and not content:
        return jsonify({"error": "テキストメッセージにはcontentが必須です"}), 400
    
    if message_type == 'image' and not image_id:
        return jsonify({"error": "画像メッセージにはimage_idが必須です"}), 400
    
    # 相手ユーザーの存在確認
    receiver = User.query.get(receiver_id)
    if not receiver:
        return jsonify({"error": "指定されたユーザーが見つかりません"}), 404
    
    # フレンド関係の確認
    is_friend = FriendRelationship.query.filter(
        ((FriendRelationship.user_id == user.id) & (FriendRelationship.friend_id == receiver_id)) |
        ((FriendRelationship.user_id == receiver_id) & (FriendRelationship.friend_id == user.id)),
        FriendRelationship.status == 'accepted'
    ).first()
    
    if not is_friend:
        return jsonify({"error": "フレンドにのみメッセージを送信できます"}), 403
    
    # メッセージの作成
    message = DirectMessage(
        id=str(uuid.uuid4()),
        sender_id=user.id,
        receiver_id=receiver_id,
        content=content,
        image_id=image_id,
        message_type=message_type,
        metadata=json.dumps(metadata) if metadata else None,
        sent_at=datetime.now(JST),
        is_read=False
    )
    
    db.session.add(message)
    db.session.commit()
    
    return jsonify({
        "message": "メッセージを送信しました",
        "direct_message": message.to_dict()
    })
