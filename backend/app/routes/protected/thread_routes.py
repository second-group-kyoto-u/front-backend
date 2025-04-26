from flask import Blueprint, request, jsonify
from app.routes.protected.routes import get_authenticated_user
from app.models.user import User
from app.models.thread import Thread, ThreadMessage, UserHeartThread
from app.models.event import TagMaster, TagAssociation
from app.models import db
import uuid
from datetime import datetime, timezone
import json

thread_bp = Blueprint("thread", __name__)

@thread_bp.route("/threads", methods=["GET"])
def get_threads():
    # 認証チェックなし
    # user, error_response, error_code = get_authenticated_user()
    # if error_response:
    #     return jsonify(error_response), error_code

    page = request.args.get('page', default=1, type=int)
    per_page = request.args.get('per_page', default=10, type=int)
    area_id = request.args.get('area_id')
    tags = request.args.getlist('tags')

    query = Thread.query

    if area_id:
        query = query.filter_by(area_id=area_id)

    if tags:
        for tag in tags:
            tag_master = TagMaster.query.filter_by(tag_name=tag).first()
            if tag_master:
                thread_ids = db.session.query(TagAssociation.entity_id).filter_by(
                    tag_id=tag_master.id,
                    entity_type='thread'
                ).all()
                thread_ids = [id[0] for id in thread_ids]
                query = query.filter(Thread.id.in_(thread_ids))

    total = query.count()

    offset = (page - 1) * per_page
    threads = query.order_by(Thread.published_at.desc()).offset(offset).limit(per_page).all()

    result = []
    for thread in threads:
        thread_dict = thread.to_dict()
        # ログインしてないのでいいね状態（is_hearted）は Falseにしておく
        thread_dict['is_hearted'] = False
        result.append(thread_dict)

    return jsonify({"threads": result, "total": total})


@thread_bp.route("/<thread_id>", methods=["GET"])
def get_thread(thread_id):
    # ユーザー認証
    user, error_response, error_code = get_authenticated_user()
    if error_response:
        return jsonify(error_response), error_code
    
    # スレッドの取得
    thread = Thread.query.get(thread_id)
    if not thread:
        return jsonify({"error": "スレッドが見つかりません"}), 404
    
    # スレッドのメッセージを取得
    messages = ThreadMessage.query.filter_by(
        thread_id=thread_id
    ).order_by(
        ThreadMessage.timestamp.asc()
    ).all()
    
    # メッセージを整形
    messages_data = [message.to_dict() for message in messages]
    
    # スレッドデータを取得
    thread_data = thread.to_dict()
    
    # タグを取得
    thread_tags = TagAssociation.query.filter_by(
        entity_id=thread_id,
        entity_type='thread'
    ).join(TagMaster, TagMaster.id == TagAssociation.tag_id).all()
    
    tags = []
    for assoc in thread_tags:
        tag = TagMaster.query.get(assoc.tag_id)
        if tag:
            tags.append({
                'id': tag.id,
                'name': tag.tag_name
            })
    
    # いいねしているかどうかを確認
    is_hearted = UserHeartThread.query.filter_by(
        user_id=user.id,
        thread_id=thread_id
    ).first() is not None
    
    # thread_dataにタグといいね情報を追加
    thread_data['tags'] = tags
    thread_data['is_hearted'] = is_hearted
    
    # 結果を返す
    return jsonify({
        "thread": thread_data,
        "messages": messages_data
    })

@thread_bp.route("/", methods=["POST"])
def create_thread():
    # ユーザー認証
    user, error_response, error_code = get_authenticated_user()
    if error_response:
        return jsonify(error_response), error_code
    
    # リクエストデータの取得
    data = request.get_json()
    title = data.get('title')
    message = data.get('message')
    image_id = data.get('image_id')
    area_id = data.get('area_id')
    tags = data.get('tags', [])
    
    # バリデーション
    if not title:
        return jsonify({"error": "タイトルは必須です"}), 400
    
    if not message:
        return jsonify({"error": "メッセージは必須です"}), 400
    
    # スレッドの作成
    thread = Thread(
        id=str(uuid.uuid4()),
        title=title,
        message=message,
        image_id=image_id,
        area_id=area_id,
        published_at=datetime.now(timezone.utc),
        author_id=user.id
    )
    
    db.session.add(thread)
    
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
        
        # スレッドとタグの関連付け
        tag_assoc = TagAssociation(
            id=str(uuid.uuid4()),
            tag_id=tag.id,
            entity_id=thread.id,
            entity_type='thread',
            created_at=datetime.now(timezone.utc)
        )
        db.session.add(tag_assoc)
    
    # 最初のメッセージを作成
    thread_message = ThreadMessage(
        id=str(uuid.uuid4()),
        thread_id=thread.id,
        sender_user_id=user.id,
        content=message,
        timestamp=datetime.now(timezone.utc),
        image_id=image_id,
        message_type='text'
    )
    
    db.session.add(thread_message)
    db.session.commit()
    
    return jsonify({
        "message": "スレッドを作成しました",
        "thread_id": thread.id
    })

@thread_bp.route("/<thread_id>/message", methods=["POST"])
def post_thread_message(thread_id):
    # ユーザー認証
    user, error_response, error_code = get_authenticated_user()
    if error_response:
        return jsonify(error_response), error_code
    
    # スレッドの取得
    thread = Thread.query.get(thread_id)
    if not thread:
        return jsonify({"error": "スレッドが見つかりません"}), 404
    
    # リクエストデータの取得
    data = request.get_json()
    content = data.get('content')
    message_type = data.get('message_type', 'text')
    
    # バリデーション
    if not content:
        return jsonify({"error": "内容は必須です"}), 400
    
    # メッセージタイプに応じた処理
    image_id = None
    if message_type == 'image':
        # 画像の場合、contentはimage_idとして扱う
        image_id = content
        content = ""  # テキスト内容はクリア
    
    # スレッドメッセージの作成
    thread_message = ThreadMessage(
        id=str(uuid.uuid4()),
        thread_id=thread_id,
        sender_user_id=user.id,
        content=content,
        timestamp=datetime.now(timezone.utc),
        image_id=image_id,
        message_type=message_type
    )
    
    db.session.add(thread_message)
    db.session.commit()
    
    return jsonify({
        "message_id": thread_message.id
    })

@thread_bp.route("/<thread_id>/heart", methods=["POST"])
def heart_thread(thread_id):
    # ユーザー認証
    user, error_response, error_code = get_authenticated_user()
    if error_response:
        return jsonify(error_response), error_code
    
    # スレッドの取得
    thread = Thread.query.get(thread_id)
    if not thread:
        return jsonify({"error": "スレッドが見つかりません"}), 404
    
    # 既にいいねしているか確認
    heart = UserHeartThread.query.filter_by(
        user_id=user.id,
        thread_id=thread_id
    ).first()
    
    if heart:
        return jsonify({"error": "既にいいねしています"}), 400
    
    # いいねの作成
    heart = UserHeartThread(
        user_id=user.id,
        thread_id=thread_id
    )
    
    db.session.add(heart)
    db.session.commit()
    
    return jsonify({
        "message": "スレッドにいいねしました",
        "thread": thread.to_dict()
    })

@thread_bp.route("/<thread_id>/unheart", methods=["POST"])
def unheart_thread(thread_id):
    # ユーザー認証
    user, error_response, error_code = get_authenticated_user()
    if error_response:
        return jsonify(error_response), error_code
    
    # スレッドの取得
    thread = Thread.query.get(thread_id)
    if not thread:
        return jsonify({"error": "スレッドが見つかりません"}), 404
    
    # いいねの確認
    heart = UserHeartThread.query.filter_by(
        user_id=user.id,
        thread_id=thread_id
    ).first()
    
    if not heart:
        return jsonify({"error": "いいねしていません"}), 400
    
    # いいねの削除
    db.session.delete(heart)
    db.session.commit()
    
    return jsonify({
        "message": "いいねを取り消しました",
        "thread": thread.to_dict()
    }) 