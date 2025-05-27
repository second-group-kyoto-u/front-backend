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
# recommend.py から新しい推薦関数をインポート
from app.utils.recommend import get_event_recommendations_for_user, get_initial_recommendations_for_user # 初期推薦もインポート

# 日本時間タイムゾーン
JST = timezone(timedelta(hours=9))

event_bp = Blueprint("event", __name__)

@event_bp.route("/events", methods=["GET"]) # <--- ルートを変更
def get_recommended_events_for_authenticated_user(): # <--- 関数名を変更
    user, error_response, error_code = get_authenticated_user()
    if error_response:
        # 認証エラーの場合は、初期推薦 (人気イベントなど) を返すか、エラーを返すか選択
        # ここでは初期推薦を返す例 (ユーザーIDなしで呼び出せるようにget_initial_recommendations_for_userを修正する必要があるかも)
        # initial_recommendations = get_initial_recommendations_for_user(user_id=None) # user_id=Noneで人気順などを返すように修正想定
        # return jsonify([event_data for event_data in initial_recommendations]), 200
        return jsonify(error_response), error_code # もしくは認証エラーをそのまま返す

    user_id = user.id

    # recommend.py の推薦関数を呼び出す
    # この関数は [{'id': event_id, 'title': title, 'similarity': score, 'reason': reason}, ...] の形式で返す想定
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
    return jsonify(response_data)

    # get_event_recommendations_for_user が既に整形済みの辞書のリストを返すと仮定
    return jsonify(recommended_events_data)

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

@event_bp.route('/<event_id>/bot/trivia', methods=['POST'])
def event_bot_trivia(event_id):
    """
    イベントに関連する豆知識やトリビアを生成する
    """
    from app.utils.openai_utils import generate_event_trivia, generate_conversation_starter
    from app.utils.event import get_event_by_id
    
    data = request.json
    
    # 豆知識の種類（デフォルトはtrivia）
    trivia_type = data.get('type', 'trivia')
    
    # 位置情報の取得
    location_data = data.get('location')

    # イベント情報を取得
    event = get_event_by_id(event_id)
    if not event:
        return jsonify({'error': 'イベントが見つかりません'}), 404
    
    # 豆知識の内容を生成
    if trivia_type == 'conversation':
        content_prefix = "💬 会話のきっかけ: "
        generated_content = generate_conversation_starter(event.title, location_data)
    else:
        # 位置情報があれば場所名を取得
        location_name = ""
        if location_data and 'latitude' in location_data and 'longitude' in location_data:
            try:
                from app.utils.openai_utils import get_location_info
                location_info = get_location_info(location_data['latitude'], location_data['longitude'])
                if location_info and 'address' in location_info:
                    address = location_info['address']
                    location_name = address.get('city', '') or address.get('town', '') or address.get('suburb', '')
            except Exception as e:
                current_app.logger.error(f"位置情報の取得エラー: {str(e)}")
        
        # 位置情報があれば場所名を含める
        if location_name:
            content_prefix = f"📍 {location_name}の豆知識: "
        else:
            content_prefix = f"📍 {event.title}の豆知識: "
        
        generated_content = generate_event_trivia(event.title, location_data)

    # メッセージを作成
    message_content = content_prefix + generated_content
    
    # データベースにメッセージを保存
    new_message = EventMessage(
        id=str(uuid.uuid4()),
        event_id=event_id,
        content=message_content,
        message_type='bot',
        timestamp=datetime.now(JST)
    )
    
    db.session.add(new_message)
    db.session.commit()
    
    # メッセージをJSONで返す
    return jsonify({
        'bot_message': new_message.to_dict(),
        'message': 'ボットメッセージを送信しました'
    }), 201

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
