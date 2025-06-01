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
from app.utils.recommend import get_event_recommendations_for_user,  get_initial_recommendations_for_user

# 日本時間タイムゾーン
JST = timezone(timedelta(hours=9))

event_bp = Blueprint("event", __name__)

# イベント一覧取得（認証なし）
@event_bp.route("/events", methods=["GET"])
def get_events():
    # クエリパラメータの取得
    area_id = request.args.get('area_id')
    tag = request.args.get('tag')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    status = request.args.get('status')  # pending, started, ended
    
    # イベントクエリのベース
    query = Event.query.filter_by(is_deleted=False)
    
    # エリアでフィルタリング
    if area_id:
        query = query.filter_by(area_id=area_id)
    
    # ステータスでフィルタリング
    if status:
        query = query.filter_by(status=status)
    
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

# おすすめイベントを表示（認証必要）
@event_bp.route("/recommended", methods=["GET"]) 
def get_recommended_events_for_authenticated_user():
    user, error_response, error_code = get_authenticated_user()
    if error_response:
        # 認証エラーの場合は、初期推薦 (人気イベントなど) を返す
        return jsonify(error_response), error_code

    user_id = user.id

    # recommend.py の推薦関数を呼び出す
    recommended_events_data = get_event_recommendations_for_user(user_id)

    if not recommended_events_data:
        # コンテンツベースで推薦が0件だった場合、フォールバックとして初期推薦を試みる
        print(f"ユーザー {user_id} へのコンテンツベース推薦結果が0件。初期推薦にフォールバックします。")
        recommended_events_data = get_initial_recommendations_for_user(user_id)

    # イベントの詳細情報を取得する必要があれば、IDリストからEventオブジェクトを取得する
    recommended_event_ids = [data['id'] for data in recommended_events_data]
    events = Event.query.filter(Event.id.in_(recommended_event_ids)).all()
    event_map = {event.id: event for event in events}
    
    # to_dict() を使って整形し、similarityやreasonも付加する
    response_data = []
    for data in recommended_events_data:
        event_obj = event_map.get(data['id'])
        if event_obj:
            event_dict = event_obj.to_dict()
            event_dict['similarity_score'] = data.get('similarity')
            event_dict['recommend_reason'] = data.get('reason')
            response_data.append(event_dict)
    
    return jsonify({'events': response_data})

# 人気イベントを表示（認証不要）
@event_bp.route("/popular", methods=["GET"])
def get_popular_events():
    """人気のイベント（認証不要）"""
    try:
        limit = request.args.get('limit', 10, type=int)
        
        # 人気イベントを取得（参加者数順、最新順でソート）
        events = Event.query.filter_by(is_deleted=False)\
            .order_by(Event.current_persons.desc(), Event.published_at.desc())\
            .limit(limit).all()
        
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
        
        return jsonify({'events': events_data})
        
    except Exception as e:
        current_app.logger.error(f"人気イベント取得エラー: {str(e)}")
        return jsonify({"error": "人気イベントの取得に失敗しました"}), 500

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
        members_data = [
            {
                "user_id": member.user_id,
                "event_id": member.event_id,
                "joined_at": member.joined_at.isoformat() if member.joined_at else None,
                "user": member.user.to_dict()
            } for member in members
        ]
        return jsonify({"message": "イベントのメンバー情報を取得しました", "members": members_data})
    else:
        # 未認証ユーザーには限定的な情報を提供
        members_data = [
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
        ]
        return jsonify({"message": "イベントのメンバー情報を取得しました", "members": members_data})

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
    アドバイザー（ボット）の応答を生成するエンドポイント（AI判定による柔軟処理）
    
    音声チャットと同様の高度なAI分析機能：
    1. AI解析による詳細な意図分析
    2. 時間指定対応の天気情報取得
    3. AI判定による柔軟な場所検索
    4. インテリジェントプロンプト生成
    """
    from app.routes.voice.routes import (
        ai_analyze_user_intent, 
        ai_generate_time_specification, 
        ai_enhanced_nearby_places,
        get_detailed_weather_info,
        create_ai_intelligent_prompt,
        get_character_system_prompt
    )
    from app.utils.event import get_event_by_id
    import openai
    import os

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

        # AI解析によるユーザーの意図分析（音声チャットと同じ高度分析）
        current_app.logger.info(f"AI意図解析開始: '{message[:50]}...'")
        ai_analysis = ai_analyze_user_intent(message)
        current_app.logger.info(f"AI意図解析結果: {ai_analysis}")
        
        # 必要に応じてAPIを呼び出し
        weather_data = None
        nearby_places = None
        
        # 天気情報が必要な場合のみ取得（AI判定による詳細天気）
        if ai_analysis.get('needs_weather') and location_data:
            current_app.logger.info("AI判定による詳細天気情報を取得中...")
            time_spec = ai_generate_time_specification(ai_analysis.get('weather_analysis', {}))
            weather_data = get_detailed_weather_info(event_id, location_data, time_spec)
        
        # 場所情報が必要な場合のみ取得（AI判定による拡張場所検索）
        if ai_analysis.get('needs_location') and location_data:
            current_app.logger.info("AI判定による拡張場所検索を実行中...")
            nearby_places = ai_enhanced_nearby_places(
                location_data['latitude'], 
                location_data['longitude'],
                ai_analysis.get('location_analysis', {})
            )
        
        # 過去の会話履歴取得（簡潔化）
        chat_history = []
        try:
            messages = EventMessage.query.filter_by(event_id=event_id).order_by(EventMessage.timestamp.desc()).limit(3).all()
            chat_history = [
                {
                    "content": msg.content,
                    "is_bot": msg.message_type.startswith('bot_') or msg.message_type == 'bot',
                    "timestamp": msg.timestamp.isoformat() if msg.timestamp else None
                }
                for msg in messages if msg.content
            ]
            chat_history.reverse()
        except Exception as e:
            current_app.logger.error(f"会話履歴取得エラー: {str(e)}")
        
        # AI解析に基づくインテリジェントプロンプトを作成（音声チャットと同じシステム）
        system_prompt = create_ai_intelligent_prompt(
            character_id, 
            message, 
            ai_analysis, 
            weather_data, 
            nearby_places
        )
        
        # ChatGPT APIでレスポンスを生成（音声チャットと同じ設定）
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            raise Exception("OPENAI_API_KEY環境変数が設定されていません")
        
        client = openai.OpenAI(api_key=openai_api_key)
        
        # 会話履歴を考慮したメッセージ構築
        messages_for_api = [{"role": "system", "content": system_prompt}]
        
        # 簡潔な履歴を追加
        if chat_history:
            recent_history = chat_history[-2:] if len(chat_history) > 2 else chat_history
            for msg in recent_history:
                role = "assistant" if msg.get("is_bot") else "user"
                messages_for_api.append({"role": role, "content": msg.get("content", "")})
        
        # 最新のユーザーメッセージを追加
        messages_for_api.append({"role": "user", "content": message})
        
        current_app.logger.info("ChatGPT API呼び出し開始（テキストチャット版）")
        chat_response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=messages_for_api,
            max_tokens=200,  # テキストチャット用に調整
            temperature=0.8
        )
        
        advisor_response = chat_response.choices[0].message.content
        current_app.logger.info(f"AI応答生成成功 (GPT-4.1-mini): {advisor_response[:100]}...")
        
        # アドバイザーの応答をメッセージとして保存
        bot_message = EventMessage(
            id=str(uuid.uuid4()),
            event_id=event_id,
            content=advisor_response,
            message_type=f'bot_{character_id}',
            timestamp=datetime.now(JST),
            metadata=json.dumps({"character_id": character_id})
        )
        
        db.session.add(bot_message)
        db.session.commit()
        
        # レスポンスを返す（音声チャットと同様のデバッグ情報付き）
        return jsonify({
            'response': advisor_response,
            'message': 'AI判定によるアドバイザー応答を生成しました',
            'message_id': bot_message.id,
            'debug_info': {
                'ai_analysis': ai_analysis,
                'weather_used': weather_data is not None,
                'location_used': nearby_places is not None,
                'weather_data': weather_data,
                'location_count': len(nearby_places) if nearby_places else 0
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"AI判定アドバイザー応答生成エラー: {str(e)}")
        current_app.logger.error(traceback.format_exc())
        
        # キャラクターごとのエラー応答
        error_responses = {
            "nyanta": "ごめんニャ、ちょっと今処理が混んでるみたいニャ。もう一度話しかけてくれるニャ？💫",
            "hitsuji": "申し訳ありません～。少し処理に時間がかかっているようです～。もう一度お願いできますか～？✨",
            "koko": "ごめんね！ちょっと今システムが忙しいみたい！もう一度聞いてくれる？🌟",
            "fukurou": "申し訳ございません。現在処理に時間を要しております。少々お待ちいただくか、再度ご質問いただけますと幸いです📚💫",
            "toraberu": "おっと！ちょっと今システムが忙しいみたいだぜ！もう一度話しかけてくれるかな？🗺️✈️"
        }
        
        fallback_response = error_responses.get(
            character_id,
            "申し訳ありません、AI応答の生成中にエラーが発生しました。もう一度お試しください。"
        )
        
        # エラー時もメッセージとして保存
        try:
            bot_message = EventMessage(
                id=str(uuid.uuid4()),
                event_id=event_id,
                content=fallback_response,
                message_type=f'bot_{character_id}',
                timestamp=datetime.now(JST),
                metadata=json.dumps({"character_id": character_id, "error": True})
            )
            db.session.add(bot_message)
            db.session.commit()
            
            return jsonify({
                'response': fallback_response,
                'message': 'エラー時のフォールバック応答を生成しました',
                'message_id': bot_message.id,
                'error': str(e)
            }), 500
        except:
            return jsonify({"error": f"AI判定アドバイザー応答の生成に失敗しました: {str(e)}"}), 500

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
