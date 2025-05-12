from flask import jsonify, request
from app.models import db
from app.models.user import User
from app.models.event import Event, UserTagAssociation, EventTagAssociation, TagMaster, UserMemberGroup
from app.models.area import AreaList
from app.models.file import ImageList
from app.utils.jwt import verify_token

def get_recommended_events():
    """ユーザーのタグに基づいておすすめのイベントを取得
    ユーザーが登録しているタグとイベントのタグが部分一致するイベントを返す
    """
    auth_header = request.headers.get('Authorization')
    limit = request.args.get('limit', default=10, type=int)
    
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({"error": "認証が必要です"}), 401
    
    token = auth_header.split(' ')[1]
    
    try:
        user_id = verify_token(token)
        if not user_id:
            return jsonify({"error": "無効なトークンです"}), 401
        
        # ユーザーのタグを取得
        user_tags = UserTagAssociation.query.filter_by(user_id=user_id).all()
        user_tag_ids = [ut.tag_id for ut in user_tags]
        
        if not user_tag_ids:
            # タグが設定されていない場合は最新のイベントを返す
            events = Event.query.order_by(Event.published_at.desc()).limit(limit).all()
        else:
            # ユーザーのタグに一致するイベントを検索
            events_with_matching_tags = db.session.query(Event)\
                .join(EventTagAssociation, Event.id == EventTagAssociation.event_id)\
                .filter(EventTagAssociation.tag_id.in_(user_tag_ids))\
                .group_by(Event.id)\
                .order_by(Event.published_at.desc())\
                .limit(limit)\
                .all()
            
            events = events_with_matching_tags
        
        # イベント情報の加工
        result = []
        for event in events:
            event_data = event.to_dict()
            
            # タグ情報を追加
            event_tags = db.session.query(TagMaster)\
                .join(EventTagAssociation, TagMaster.id == EventTagAssociation.tag_id)\
                .filter(EventTagAssociation.event_id == event.id)\
                .all()
            
            event_data['tags'] = [{'id': tag.id, 'tag_name': tag.tag_name} for tag in event_tags]
            
            # 作成者情報を追加
            author = User.query.get(event.author_user_id)
            if author:
                event_data['author'] = {
                    'id': author.id,
                    'user_name': author.user_name,
                    'user_image_url': author.user_image_url,
                    'profile_message': author.profile_message,
                    'is_certificated': author.is_certificated
                }
            
            # エリア情報を追加
            area = AreaList.query.filter_by(area_id=event.area_id).first()
            if area:
                event_data['area'] = {
                    'id': area.area_id,
                    'name': area.area_name
                }
            
            result.append(event_data)
        
        return jsonify({"events": result, "count": len(result), "page": 1})
        
    except Exception as e:
        from flask import current_app as app
        app.logger.error(f"エラー: {str(e)}")
        return jsonify({"error": "サーバーエラーが発生しました"}), 500
        
# API呼び出し用の関数
def recommended_events_api():
    """ユーザーのタグに基づいておすすめのイベントを取得するエンドポイント"""
    return get_recommended_events()

def get_events_list(area_id=None, tag=None, page=1, per_page=10, status=None):
    """イベント一覧を取得する関数
    パラメータ:
    - area_id: エリアID
    - tag: タグID
    - page: ページ番号
    - per_page: ページあたりの件数
    - status: ステータス (pending, started, ended)
    """
    query = Event.query
    
    if area_id:
        query = query.filter_by(area_id=area_id)
    
    if tag:
        query = query.join(EventTagAssociation).filter(EventTagAssociation.tag_id == tag)
    
    if status:
        query = query.filter_by(status=status)
    
    # 公開日時が古い順にソート
    query = query.order_by(Event.published_at.desc())
    
    # ページネーション
    paginated = query.paginate(page=page, per_page=per_page, error_out=False)
    events = paginated.items
    
    # イベント情報の加工
    result = []
    for event in events:
        event_data = event.to_dict()
        
        # タグ情報を追加
        event_tags = db.session.query(TagMaster)\
            .join(EventTagAssociation, TagMaster.id == EventTagAssociation.tag_id)\
            .filter(EventTagAssociation.event_id == event.id)\
            .all()
        
        event_data['tags'] = [{'id': tag.id, 'tag_name': tag.tag_name} for tag in event_tags]
        
        # 作成者情報を追加
        author = User.query.get(event.author_user_id)
        if author:
            event_data['author'] = {
                'id': author.id,
                'user_name': author.user_name,
                'user_image_url': author.user_image_url,
                'profile_message': author.profile_message,
                'is_certificated': author.is_certificated
            }
        
        # エリア情報を追加
        area = AreaList.query.filter_by(area_id=event.area_id).first()
        if area:
            event_data['area'] = {
                'id': area.area_id,
                'name': area.area_name
            }
        
        result.append(event_data)
    
    return {
        "events": result,
        "count": len(result),
        "total": paginated.total,
        "pages": paginated.pages,
        "page": paginated.page
    }

# API呼び出し用の関数
def events_list_api():
    """イベント一覧を取得するエンドポイント"""
    area_id = request.args.get('area_id')
    tag = request.args.get('tag')
    page = request.args.get('page', default=1, type=int)
    per_page = request.args.get('per_page', default=10, type=int)
    status = request.args.get('status')
    
    result = get_events_list(area_id, tag, page, per_page, status)
    return jsonify(result)

def get_event_detail(event_id, user_id=None):
    """イベント詳細を取得する関数"""
    event = Event.query.get_or_404(event_id)
    event_data = event.to_dict()
    
    # タグ情報を追加
    event_tags = db.session.query(TagMaster)\
        .join(EventTagAssociation, TagMaster.id == EventTagAssociation.tag_id)\
        .filter(EventTagAssociation.event_id == event.id)\
        .all()
    
    event_data['tags'] = [{'id': tag.id, 'tag_name': tag.tag_name} for tag in event_tags]
    
    # 作成者情報を追加
    author = User.query.get(event.author_user_id)
    if author:
        event_data['author'] = {
            'id': author.id,
            'user_name': author.user_name,
            'user_image_url': author.user_image_url,
            'profile_message': author.profile_message,
            'is_certificated': author.is_certificated
        }
    
    # エリア情報を追加
    area = AreaList.query.filter_by(area_id=event.area_id).first()
    if area:
        event_data['area'] = {
            'id': area.area_id,
            'name': area.area_name
        }
    
    # イベントのイメージを追加
    image = ImageList.query.get(event.image_id) if event.image_id else None
    event_data['image_url'] = image.image_url if image else None
    
    # 参加済みかどうか
    is_joined = False
    if user_id:
        # ログインしている場合、参加しているかをチェック
        member = UserMemberGroup.query.filter_by(
            user_id=user_id, 
            event_id=event_id
        ).first()
        is_joined = member is not None
    
    return {
        "event": event_data,
        "is_joined": is_joined
    }

# API呼び出し用の関数
def event_detail_api(event_id):
    """イベント詳細を取得するエンドポイント"""
    auth_header = request.headers.get('Authorization')
    user_id = None
    
    if auth_header and auth_header.startswith('Bearer '):
        token = auth_header.split(' ')[1]
        user_id = verify_token(token)
    
    result = get_event_detail(event_id, user_id)
    return jsonify(result)

# 追加: イベントIDからEventオブジェクトを取得する関数
def get_event_by_id(event_id):
    """
    イベントIDからEventオブジェクトを取得する
    
    Args:
        event_id: 取得するイベントのID
        
    Returns:
        Event: 見つかったEventオブジェクト、見つからない場合はNone
    """
    return Event.query.get(event_id) 