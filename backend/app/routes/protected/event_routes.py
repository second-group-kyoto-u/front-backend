from flask import Blueprint, request, jsonify, current_app, make_response
from app.routes.protected.routes import get_authenticated_user
from app.models.user import User
from app.models.event import Event, UserMemberGroup, UserHeartEvent, TagMaster, EventTagAssociation, UserTagAssociation
from app.models.message import EventMessage, MessageReadStatus, FriendRelationship
from app.models import db
import uuid
from datetime import datetime, timezone, timedelta
import json
from flask import g
from flask_jwt_extended import jwt_required, get_jwt_identity
import traceback
import os
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor

# 日本時間タイムゾーン
JST = timezone(timedelta(hours=9))

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
            tag_associations = EventTagAssociation.query.filter_by(
                tag_id=tag_obj.id
            ).all()
            event_ids = [assoc.event_id for assoc in tag_associations]
            query = query.filter(Event.id.in_(event_ids))
    
    # 総件数を取得
    total_count = query.count()
    
    # ページネーション
    events = query.order_by(Event.published_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    
    # 結果の整形
    events_data = []
    for event in events.items:
        event_data = event.to_dict()
        
        # タグ情報を追加
        event_tags = db.session.query(TagMaster)\
            .join(EventTagAssociation, TagMaster.id == EventTagAssociation.tag_id)\
            .filter(EventTagAssociation.event_id == event.id)\
            .all()
            
        event_data['tags'] = [{'id': tag.id, 'tag_name': tag.tag_name} for tag in event_tags]
        events_data.append(event_data)
    
    result = {
        'events': events_data,
        'total': total_count,
        'page': page,
        'per_page': per_page,
        'pages': events.pages
    }
    
    return jsonify(result)

@event_bp.route("/<event_id>", methods=["GET"])
def get_event(event_id):
    # トークルームへ遷移する権利があるかの検証に用いる
    user, error_response, error_code = get_authenticated_user()
    
    # 認証に失敗しても OK（エラーを返さず、未ログイン状態として進める）
    if error_response and error_code == 401:
        user = None


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


    # イベントの参加者かどうか
    is_joined = False

    if user:
        is_joined = UserMemberGroup.query.filter_by(
            user_id=user.id,
            event_id=event_id
    ).first() is not None
    
    # イベント情報の加工
    event_data = event.to_dict()
    
    # タグ情報を追加
    event_tags = db.session.query(TagMaster)\
        .join(EventTagAssociation, TagMaster.id == EventTagAssociation.tag_id)\
        .filter(EventTagAssociation.event_id == event.id)\
        .all()
        
    event_data['tags'] = [{'id': tag.id, 'tag_name': tag.tag_name} for tag in event_tags]

    return jsonify({
        "event": event_data,
        "messages": [message.to_dict() for message in messages],
        "is_joined": is_joined
    })

@event_bp.route("/", methods=["POST"])
def create_event():
    # ユーザー認証
    user, error_response, error_code = get_authenticated_user()
    if error_response:
        return jsonify(error_response), error_code
    
    # リクエストデータの取得
    data = request.get_json()
    title = data.get('title')
    description = data.get('description')
    image_id = data.get('image_id')
    limit_persons = data.get('limit_persons', 10)
    area_id = data.get('area_id')
    tags = data.get('tags', [])
    
    # 必須項目のバリデーション
    if not title:
       return jsonify({"error": "タイトルは必須です"}), 400
    
    if not description:
        return jsonify({"error": "イベントの詳細は必須です"}), 400
    
    # 新規イベントの作成
    event = Event(
        id=str(uuid.uuid4()),
        title=title,
        description=description,
        image_id=image_id,
        current_persons=1,  # 作成者を含む
        limit_persons=limit_persons,
        is_request=False,
        is_deleted=False,
        author_user_id=user.id,
        area_id=area_id,
        published_at=datetime.now(JST),
        status='pending'  # 初期状態は未開始
    )
    
    db.session.add(event)
    
    # 作成者を参加者に追加
    member = UserMemberGroup(
        user_id=user.id,
        event_id=event.id,
        joined_at=datetime.now(JST)
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
                created_at=datetime.now(JST)
            )
            db.session.add(tag)
            db.session.flush()
        
        # イベントとタグの関連付け
        tag_assoc = EventTagAssociation(
            id=str(uuid.uuid4()),
            tag_id=tag.id,
            event_id=event.id,
            created_at=datetime.now(JST)
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
        joined_at=datetime.now(JST)
    )
    
    # イベントの参加者数を増やす
    event.current_persons += 1
    
    # システムメッセージの作成
    system_message = EventMessage(
        id=str(uuid.uuid4()),
        event_id=event_id,
        sender_user_id=None,  # システムメッセージ
        content=f"{user.user_name}さんがイベントに参加しました",
        timestamp=datetime.now(JST),
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
        timestamp=datetime.now(JST),
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
        timestamp=datetime.now(JST),
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
            timestamp=datetime.now(JST),
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
        timestamp=datetime.now(JST),
        message_type='system'
    )
    
    db.session.add(system_message)
    
    # Botメッセージの作成（get_event_end_message関数を使用）
    from app.utils.event import get_event_end_message
    bot_message_content = get_event_end_message(event_id=event_id)
    
    bot_message = EventMessage(
        id=str(uuid.uuid4()),
        event_id=event_id,
        sender_user_id=None,  # Botメッセージ
        content=bot_message_content,
        timestamp=datetime.now(JST),
        message_type='bot'
    )
    
    db.session.add(bot_message)
    db.session.commit()
    
    return jsonify({
        "message": "イベントを終了しました",
        "event": event.to_dict()
    })

@event_bp.route("/<event_id>/message", methods=["POST"])
def send_event_message(event_id):
    user, error_response, error_code = get_authenticated_user()
    if error_response:
        return jsonify(error_response), error_code

    data = request.get_json()
    content = data.get('content')
    image_id = data.get('image_id')
    message_type = data.get('message_type', 'text')

    new_message = EventMessage(
        id=str(uuid.uuid4()),
        event_id=event_id,
        sender_user_id=user.id,
        content=content,
        timestamp=datetime.now(JST),
        message_type=message_type,
        image_id=image_id,
    )
    db.session.add(new_message)
    db.session.commit()

    return jsonify(new_message.to_dict())

@event_bp.route("/<event_id>/members", methods=["GET"])
def get_event_members(event_id):
    # ユーザー認証チェック（認証情報があれば使用するが、なくても続行する）
    user, error_response, error_code = get_authenticated_user()
    
    # 認証エラーでも処理を続行（userがNoneになる）
    # ✅ 認証なしアクセスを許可
    if error_response and error_code == 401:
        user = None
    elif error_response:
        # 401以外のエラー（例：無効なトークン）の場合はエラーを返す
        return jsonify(error_response), error_code
    
    # イベントの存在確認
    event = Event.query.get(event_id)
    if not event:
        return jsonify({"error": "イベントが見つかりません"}), 404
    
    # イベントメンバーの取得
    members = UserMemberGroup.query.filter_by(event_id=event_id).join(
        User, UserMemberGroup.user_id == User.id
    ).all()
    
    # ユーザーが認証済みかどうかでレスポンスを調整
    if user:
        # 認証済みユーザーには詳細情報を提供
        return jsonify({
            "members": [
                {
                    "user_id": member.user_id,
                    "event_id": member.event_id,
                    "joined_at": member.joined_at.isoformat() if member.joined_at else None,
                    "user": member.user.to_dict()
                } for member in members
            ],
            "authenticated": True
        })
    else:
        # 未認証ユーザーには限定的な情報を提供
        return jsonify({
            "members": [
                {
                    "user_id": member.user_id,
                    "event_id": member.event_id,
                    "joined_at": member.joined_at.isoformat() if member.joined_at else None,
                    "user": {
                        "id": member.user.id,
                        "user_name": member.user.user_name,
                        "user_image_url": member.user.user_image_url,
                        "is_certificated": member.user.is_certificated if hasattr(member.user, 'is_certificated') else False
                    }
                } for member in members
            ],
            "authenticated": False
        })

@event_bp.route("/recommended", methods=["GET"])
def get_recommended_events():
    """ユーザーのタグ設定に基づいたおすすめイベントを取得"""
    # ユーザー認証チェック
    user, error_response, error_code = get_authenticated_user()
    if error_response:
        # 未認証の場合は最新のイベントを返す
        limit = request.args.get('limit', 10, type=int)
        latest_events = Event.query.filter_by(is_deleted=False).order_by(Event.published_at.desc()).limit(limit).all()
        
        # イベント情報の加工
        events_data = []
        for event in latest_events:
            event_data = event.to_dict()
            
            # タグ情報を追加
            event_tags = db.session.query(TagMaster)\
                .join(EventTagAssociation, TagMaster.id == EventTagAssociation.tag_id)\
                .filter(EventTagAssociation.event_id == event.id)\
                .all()
                
            event_data['tags'] = [{'id': tag.id, 'tag_name': tag.tag_name} for tag in event_tags]
            events_data.append(event_data)
            
        return jsonify({
            "events": events_data,
            "authenticated": False
        })
    
    # ユーザーのタグ設定を取得
    user_tags = UserTagAssociation.query.filter_by(user_id=user.id).all()
    user_tag_ids = [ut.tag_id for ut in user_tags]
    
    limit = request.args.get('limit', 10, type=int)
    events = []
    
    if user_tag_ids:
        # ユーザーのタグに関連するイベントを取得
        tag_events = Event.query.join(
            EventTagAssociation,
            Event.id == EventTagAssociation.event_id
        ).filter(
            EventTagAssociation.tag_id.in_(user_tag_ids),
            Event.is_deleted == False
        ).order_by(Event.published_at.desc()).limit(limit).all()
        
        events = tag_events
    else:
        # タグ設定がない場合は最新のイベントを返す
        events = Event.query.filter_by(is_deleted=False).order_by(Event.published_at.desc()).limit(limit).all()
    
    # イベント情報の加工
    events_data = []
    for event in events:
        event_data = event.to_dict()
        
        # タグ情報を追加
        event_tags = db.session.query(TagMaster)\
            .join(EventTagAssociation, TagMaster.id == EventTagAssociation.tag_id)\
            .filter(EventTagAssociation.event_id == event.id)\
            .all()
            
        event_data['tags'] = [{'id': tag.id, 'tag_name': tag.tag_name} for tag in event_tags]
        events_data.append(event_data)
    
    return jsonify({
        "events": events_data,
        "authenticated": True
    })

@event_bp.route("/friends", methods=["GET"])
def get_friends_events():
    """フレンド（フォロー中のユーザー）が主催するイベントを取得"""
    # ユーザー認証チェック
    user, error_response, error_code = get_authenticated_user()
    if error_response:
        return jsonify(error_response), error_code
    
    # フレンド（フォロー）関係を取得
    friend_relationships = FriendRelationship.query.filter(
        FriendRelationship.user_id == user.id,
        FriendRelationship.status == 'accepted'
    ).all()
    
    friend_ids = [fr.friend_id for fr in friend_relationships]
    
    if not friend_ids:
        # フレンドがいない場合は空のリストを返す
        return jsonify({"events": []})
    
    # フレンドが主催するイベントを取得
    limit = request.args.get('limit', 10, type=int)
    events = Event.query.filter(
        Event.author_user_id.in_(friend_ids),
        Event.is_deleted == False
    ).order_by(Event.published_at.desc()).limit(limit).all()
    
    # イベント情報の加工
    events_data = []
    for event in events:
        event_data = event.to_dict()
        
        # タグ情報を追加
        event_tags = db.session.query(TagMaster)\
            .join(EventTagAssociation, TagMaster.id == EventTagAssociation.tag_id)\
            .filter(EventTagAssociation.event_id == event.id)\
            .all()
            
        event_data['tags'] = [{'id': tag.id, 'tag_name': tag.tag_name} for tag in event_tags]
        events_data.append(event_data)
    
    return jsonify({
        "events": events_data
    })

@event_bp.route("/joined-events", methods=["GET", "OPTIONS"])
def get_joined_events():
    if request.method == "OPTIONS":
        # プリフライトリクエストに対しては何もしないで 200 を返す
        response = make_response('', 200)
        response.headers['Access-Control-Allow-Origin'] = request.headers.get('Origin', '*')
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response

    """認証済みユーザーが参加しているイベントのリストを返す"""
    user, error_response, error_code = get_authenticated_user()
    if error_response:
        return jsonify(error_response), error_code

    memberships = UserMemberGroup.query.filter_by(user_id=user.id).all()
    event_ids = [m.event_id for m in memberships]

    events = Event.query.filter(
        Event.id.in_(event_ids),
        Event.is_deleted == False
    ).order_by(Event.published_at.desc()).all()

    event_data = [
        {
            "id": e.id,
            "title": e.title,
            "description": e.description
        } for e in events
    ]

    return jsonify({"events": event_data})

@event_bp.route('/<event_id>/weather-info', methods=['POST'])
def get_event_weather_info_route(event_id):
    """
    イベントに関する天気情報とアドバイスを取得するエンドポイント
    """
    from app.utils.event import event_weather_info_api
    
    return event_weather_info_api(event_id)

@event_bp.route('/<event_id>/advisor-response', methods=['POST'])
def get_advisor_response(event_id):
    """
    アドバイザー（ボット）の応答を生成するエンドポイント
    
    ユーザーのメッセージに対して、以下のプロセスで応答を生成します：
    1. メッセージ内容を分析し、天気情報や位置情報が必要かどうか判断
    2. 必要な情報を取得（天気API、位置情報API）
    3. 会話履歴とともに統合して応答を生成
    """
    from app.utils.openai_utils import analyze_message_needs, generate_advisor_response, get_place_info_for_prompt
    from app.utils.event import get_event_by_id, get_event_weather_info

    # ユーザー認証
    user, error_response, error_code = get_authenticated_user()
    if error_response:
        return jsonify(error_response), error_code
    
    try:
        # リクエストデータの取得
        data = request.json
        if not data:
            return jsonify({"error": "リクエストデータがありません"}), 400
        
        # パラメータの取得と検証
        message = data.get('message')
        if not message:
            return jsonify({"error": "メッセージが必要です"}), 400
        
        # キャラクター情報
        character_id = data.get('character_id', 'default')
        
        # 位置情報（オプション）
        location_data = data.get('location')
        
        # イベント情報の取得
        event = get_event_by_id(event_id)
        if not event:
            return jsonify({"error": "イベントが見つかりません"}), 404

        # ★★★ ユーザーのメッセージをまず保存する ★★★
        user_message = EventMessage(
            id=str(uuid.uuid4()),
            event_id=event_id,
            sender_user_id=user.id,
            content=message,
            message_type='text',
            timestamp=datetime.now(JST)
        )
        db.session.add(user_message)
        db.session.commit()

        # 過去の会話履歴取得（最新5件に制限）
        chat_history = []
        try:
            messages = EventMessage.query.filter_by(event_id=event_id).order_by(EventMessage.timestamp.desc()).limit(5).all()
            chat_history = [
                {
                    "content": msg.content,
                    "is_bot": msg.message_type.startswith('bot_') or msg.message_type == 'bot',  # bot_で始まるメッセージタイプとbotをbotとして扱う
                    "timestamp": msg.timestamp.isoformat() if msg.timestamp else None
                }
                for msg in messages
            ]
            chat_history.reverse()  # 古い順に並べ替え
        except Exception as e:
            current_app.logger.error(f"会話履歴取得エラー: {str(e)}")
            # 履歴取得に失敗しても処理は続行
        
        # メッセージを分析して必要な情報を判断
        try:
            # アプリケーションコンテキストを確保して分析を実行
            analysis = analyze_message_needs(message, event.title)
        except Exception as e:
            current_app.logger.error(f"メッセージ分析エラー: {str(e)}")
            analysis = {
                "needs_weather": False,
                "needs_location": False
            }
        
        current_app.logger.info(f"メッセージ分析結果: {analysis}")
        
        # 追加情報の初期化
        additional_info = {}
        
        # 天気情報が必要な場合は取得
        if analysis.get('needs_weather', False):
            current_app.logger.info("天気情報を取得します")
            try:
                weather_info = get_event_weather_info(event_id, location_data)
                additional_info['weather_info'] = weather_info.get('weather_info')
            except Exception as e:
                current_app.logger.error(f"天気情報取得エラー: {str(e)}")
        
        # 位置情報が必要な場合は取得
        if analysis.get('needs_location', False) and location_data and 'latitude' in location_data and 'longitude' in location_data:
            current_app.logger.info("位置情報と周辺施設情報を取得します")
            try:
                place_info = get_place_info_for_prompt(
                    location_data["latitude"],
                    location_data["longitude"]
                )
                additional_info['location_info'] = place_info
            except Exception as e:
                current_app.logger.error(f"位置情報取得エラー: {str(e)}")
        
        # アドバイザーの応答を生成
        try:
            # アプリケーションコンテキストを確保して応答を生成
            advisor_response = generate_advisor_response(
                message=message,
                event_title=event.title,
                character_id=character_id,
                chat_history=chat_history,
                additional_info=additional_info
            )
        except Exception as e:
            current_app.logger.error(f"アドバイザー応答生成エラー: {str(e)}")
            # キャラクターごとのエラー応答
            error_responses = {
                "nyanta": "ごめんニャ、ちょっと考えるのに時間がかかってるニャ。もう少し待ってほしいニャ。",
                "hitsuji": "申し訳ありません～。少し考えるのに時間がかかっているようです～。もう一度お願いできますか～？",
                "koko": "ごめんね！ちょっと今考え中で時間がかかってるみたい！もう一度聞いてくれる？",
                "fukurou": "申し訳ございません。只今処理に時間を要しております。少々お待ちいただくか、再度ご質問いただけますと幸いです。",
                "toraberu": "おっと！ちょっと今考えるのに時間かかってるみたいだぜ！もう一度聞いてくれるかな？"
            }
            advisor_response = error_responses.get(
                character_id,
                "申し訳ありません、応答の生成中にエラーが発生しました。もう一度お試しください。"
            )
        
        # アドバイザーの応答をメッセージとして保存
        bot_message = EventMessage(
            id=str(uuid.uuid4()),
            event_id=event_id,
            content=advisor_response,
            message_type=f'bot_{character_id}',  # キャラクターごとに異なるメッセージタイプを設定
            timestamp=datetime.now(JST),
            metadata={"character_id": character_id}
        )
        
        db.session.add(bot_message)
        db.session.commit()
        
        # レスポンスを返す
        return jsonify({
            'response': advisor_response,
            'message': 'アドバイザー応答を生成しました',
            'message_id': bot_message.id,
            'analysis': analysis
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"アドバイザー応答生成エラー: {str(e)}")
        current_app.logger.error(traceback.format_exc())
        return jsonify({"error": f"アドバイザー応答の生成に失敗しました: {str(e)}"}), 500

# CORSヘッダー付きのレスポンスを作成するヘルパー関数
def create_cors_response(data, status_code=200):
    """
    CORSヘッダーを付けたレスポンスを作成する
    """
    # フロントエンドのオリジンを取得（Refererヘッダーから）
    origin = request.headers.get('Origin', 'http://localhost:3000')
    
    response = make_response(jsonify(data), status_code)
    # ワイルドカード(*)ではなく、特定のオリジンを許可
    response.headers['Access-Control-Allow-Origin'] = origin
    response.headers['Access-Control-Allow-Credentials'] = 'true'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With'
    return response
