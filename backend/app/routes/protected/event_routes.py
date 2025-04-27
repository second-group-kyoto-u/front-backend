from flask import Blueprint, request, jsonify
from app.routes.protected.routes import get_authenticated_user
from app.models.user import User
from app.models.event import Event, UserMemberGroup, UserHeartEvent, TagMaster, TagAssociation
from app.models.message import EventMessage, MessageReadStatus
from app.models import db
import uuid
from datetime import datetime, timezone
import json

event_bp = Blueprint("event", __name__)

@event_bp.route("/events", methods=["GET"])
def get_events():
    # 認証チェックなし
    # user, error_response, error_code = get_authenticated_user()
    # if error_response:
    #     return jsonify(error_response), error_code
    
    # クエリパラメータの取得
    area_id = request.args.get('area_id')
    tag = request.args.get('tag')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    # イベントクエリのベース
    query = Event.query.filter_by(is_deleted=False)
    
    # エリアでフィルタリング
    if area_id:
        query = query.filter_by(area_id=area_id)
    
    # タグでフィルタリング
    if tag:
        tag_obj = TagMaster.query.filter_by(tag_name=tag).first()
        if tag_obj:
            tag_associations = TagAssociation.query.filter_by(
                tag_id=tag_obj.id,
                entity_type='event'
            ).all()
            event_ids = [assoc.entity_id for assoc in tag_associations]
            query = query.filter(Event.id.in_(event_ids))
    
    # 総件数を取得
    total_count = query.count()
    
    # ページネーション
    events = query.order_by(Event.published_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    
    # 結果の整形
    result = {
        'events': [event.to_dict() for event in events.items],
        'total': total_count,
        'page': page,
        'per_page': per_page,
        'pages': events.pages
    }
    
    return jsonify(result)

@event_bp.route("/<event_id>", methods=["GET"])
def get_event(event_id):
    # 認証チェックなし
    # user, error_response, error_code = get_authenticated_user()
    # if error_response:
    #     return jsonify(error_response), error_code
    
    # イベントの取得
    event = Event.query.get(event_id)
    if not event:
        return jsonify({"error": "イベントが見つかりません"}), 404
    
    # イベントが削除されている場合
    if event.is_deleted:
        return jsonify({"error": "このイベントは削除されています"}), 404
    
    # メッセージも取得！
    messages = EventMessage.query.filter_by(event_id=event_id).order_by(EventMessage.timestamp.asc()).all()
    messages_data = [message.to_dict() for message in messages]

    # まとめて返す！
    return jsonify({
        "event": event.to_dict(),
        "messages": messages_data
    })

@event_bp.route("/", methods=["POST"])
def create_event():
    # ユーザー認証
    user, error_response, error_code = get_authenticated_user()
    if error_response:
        return jsonify(error_response), error_code
    
    # リクエストデータの取得
    data = request.get_json()
    message = data.get('message')
    image_id = data.get('image_id')
    limit_persons = data.get('limit_persons', 10)
    area_id = data.get('area_id')
    tags = data.get('tags', [])
    
    # 必須項目のバリデーション
    if not message:
        return jsonify({"error": "メッセージは必須です"}), 400
    
    # 新規イベントの作成
    event = Event(
        id=str(uuid.uuid4()),
        message=message,
        image_id=image_id,
        current_persons=1,  # 作成者を含む
        limit_persons=limit_persons,
        is_request=False,
        is_deleted=False,
        author_user_id=user.id,
        area_id=area_id,
        published_at=datetime.now(timezone.utc),
        status='pending'  # 初期状態は未開始
    )
    
    db.session.add(event)
    
    # 作成者を参加者に追加
    member = UserMemberGroup(
        user_id=user.id,
        event_id=event.id,
        joined_at=datetime.now(timezone.utc)
    )
    
    db.session.add(member)
    
    # タグの追加
    for tag_name in tags:
        # タグが存在するか確認
        tag = TagMaster.query.filter_by(tag_name=tag_name).first()
        if not tag:
            # 存在しない場合は新規作成
            tag = TagMaster(
                id=str(uuid.uuid4()),
                tag_name=tag_name,
                is_active=True,
                created_at=datetime.now(timezone.utc)
            )
            db.session.add(tag)
            db.session.flush()
        
        # イベントとタグの関連付け
        tag_assoc = TagAssociation(
            id=str(uuid.uuid4()),
            tag_id=tag.id,
            entity_id=event.id,
            entity_type='event',
            created_at=datetime.now(timezone.utc)
        )
        db.session.add(tag_assoc)
    
    db.session.commit()
    
    return jsonify({
        "message": "イベントを作成しました",
        "event": event.to_dict()
    })

@event_bp.route("/<event_id>/join", methods=["POST"])
def join_event(event_id):
    # ユーザー認証
    user, error_response, error_code = get_authenticated_user()
    if error_response:
        return jsonify(error_response), error_code
    
    # イベントの取得
    event = Event.query.get(event_id)
    if not event:
        return jsonify({"error": "イベントが見つかりません"}), 404
    
    # 既に参加しているか確認
    is_member = UserMemberGroup.query.filter_by(
        user_id=user.id,
        event_id=event_id
    ).first()
    
    if is_member:
        return jsonify({"error": "既にこのイベントに参加しています"}), 400
    
    # 定員確認
    if event.current_persons >= event.limit_persons:
        return jsonify({"error": "イベントの定員に達しています"}), 400
    
    # 参加処理
    member = UserMemberGroup(
        user_id=user.id,
        event_id=event_id,
        joined_at=datetime.now(timezone.utc)
    )
    
    # イベントの参加者数を増やす
    event.current_persons += 1
    
    # システムメッセージの作成
    system_message = EventMessage(
        id=str(uuid.uuid4()),
        event_id=event_id,
        sender_user_id=None,  # システムメッセージ
        content=f"{user.user_name}さんがイベントに参加しました",
        timestamp=datetime.now(timezone.utc),
        message_type='system'
    )
    
    db.session.add(member)
    db.session.add(system_message)
    db.session.commit()
    
    return jsonify({
        "message": "イベントに参加しました",
        "event": event.to_dict()
    })

@event_bp.route("/<event_id>/leave", methods=["POST"])
def leave_event(event_id):
    # ユーザー認証
    user, error_response, error_code = get_authenticated_user()
    if error_response:
        return jsonify(error_response), error_code
    
    # イベントの取得
    event = Event.query.get(event_id)
    if not event:
        return jsonify({"error": "イベントが見つかりません"}), 404
    
    # 参加しているか確認
    member = UserMemberGroup.query.filter_by(
        user_id=user.id,
        event_id=event_id
    ).first()
    
    if not member:
        return jsonify({"error": "このイベントに参加していません"}), 400
    
    # 作成者は退出できない
    if event.author_user_id == user.id:
        return jsonify({"error": "イベント作成者は退出できません"}), 400
    
    # 退出処理
    db.session.delete(member)
    
    # イベントの参加者数を減らす
    if event.current_persons > 1:
        event.current_persons -= 1
    
    # システムメッセージの作成
    system_message = EventMessage(
        id=str(uuid.uuid4()),
        event_id=event_id,
        sender_user_id=None,  # システムメッセージ
        content=f"{user.user_name}さんがイベントから退出しました",
        timestamp=datetime.now(timezone.utc),
        message_type='system'
    )
    
    db.session.add(system_message)
    db.session.commit()
    
    return jsonify({
        "message": "イベントから退出しました"
    })

@event_bp.route("/<event_id>/start", methods=["POST"])
def start_event(event_id):
    # ユーザー認証
    user, error_response, error_code = get_authenticated_user()
    if error_response:
        return jsonify(error_response), error_code
    
    # イベントの取得
    event = Event.query.get(event_id)
    if not event:
        return jsonify({"error": "イベントが見つかりません"}), 404
    
    # 作成者のみ開始可能
    if event.author_user_id != user.id:
        return jsonify({"error": "イベントを開始する権限がありません"}), 403
    
    # 既に開始されているか確認
    if event.status == 'started':
        return jsonify({"error": "イベントは既に開始されています"}), 400
    
    # 終了済みか確認
    if event.status == 'ended':
        return jsonify({"error": "終了したイベントは再開できません"}), 400
    
    # 位置情報（オプション）
    location_data = request.get_json()
    
    # イベント開始処理
    event.status = 'started'
    
    # システムメッセージの作成
    system_message = EventMessage(
        id=str(uuid.uuid4()),
        event_id=event_id,
        sender_user_id=None,  # システムメッセージ
        content="イベントが開始されました！",
        timestamp=datetime.now(timezone.utc),
        message_type='system'
    )
    
    db.session.add(system_message)
    
    # 位置情報がある場合は保存
    if location_data and 'latitude' in location_data and 'longitude' in location_data:
        location_message = EventMessage(
            id=str(uuid.uuid4()),
            event_id=event_id,
            sender_user_id=user.id,
            content="現在地を共有しました",
            timestamp=datetime.now(timezone.utc),
            message_type='location',
            metadata=json.dumps({
                'latitude': location_data.get('latitude'),
                'longitude': location_data.get('longitude'),
                'address': location_data.get('address', '')
            })
        )
        db.session.add(location_message)
    
    db.session.commit()
    
    return jsonify({
        "message": "イベントを開始しました",
        "event": event.to_dict()
    })

@event_bp.route("/<event_id>/end", methods=["POST"])
def end_event(event_id):
    # ユーザー認証
    user, error_response, error_code = get_authenticated_user()
    if error_response:
        return jsonify(error_response), error_code
    
    # イベントの取得
    event = Event.query.get(event_id)
    if not event:
        return jsonify({"error": "イベントが見つかりません"}), 404
    
    # 作成者のみ終了可能
    if event.author_user_id != user.id:
        return jsonify({"error": "イベントを終了する権限がありません"}), 403
    
    # 未開始の場合
    if event.status == 'pending':
        return jsonify({"error": "まだ開始されていないイベントは終了できません"}), 400
    
    # 既に終了済みか確認
    if event.status == 'ended':
        return jsonify({"error": "イベントは既に終了しています"}), 400
    
    # イベント終了処理
    event.status = 'ended'
    
    # システムメッセージの作成
    system_message = EventMessage(
        id=str(uuid.uuid4()),
        event_id=event_id,
        sender_user_id=None,  # システムメッセージ
        content="イベントが終了しました。お疲れ様でした！",
        timestamp=datetime.now(timezone.utc),
        message_type='system'
    )
    
    db.session.add(system_message)
    db.session.commit()
    
    return jsonify({
        "message": "イベントを終了しました",
        "event": event.to_dict()
    }) 