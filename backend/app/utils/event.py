from flask import jsonify, request, current_app
from app.models import db
from app.models.user import User
from app.models.event import Event, UserTagAssociation, EventTagAssociation, TagMaster, UserMemberGroup
from app.models.area import AreaList
from app.models.file import ImageList
from app.utils.jwt import verify_token
import os
import random
import requests
from openai import OpenAI
import time
import json
import traceback

# エリア名に対応する緯度経度のマッピング
AREA_COORDINATES = {
    '北海道': {'lat': 43.0642, 'lon': 141.3468},
    '青森県': {'lat': 40.8244, 'lon': 140.7400},
    '岩手県': {'lat': 39.7036, 'lon': 141.1527},
    '宮城県': {'lat': 38.2688, 'lon': 140.8721},
    '秋田県': {'lat': 39.7186, 'lon': 140.1024},
    '山形県': {'lat': 38.2404, 'lon': 140.3633},
    '福島県': {'lat': 37.7503, 'lon': 140.4676},
    '茨城県': {'lat': 36.3418, 'lon': 140.4468},
    '栃木県': {'lat': 36.5658, 'lon': 139.8836},
    '群馬県': {'lat': 36.3911, 'lon': 139.0608},
    '埼玉県': {'lat': 35.8569, 'lon': 139.6489},
    '千葉県': {'lat': 35.6046, 'lon': 140.1233},
    '東京都': {'lat': 35.6895, 'lon': 139.6917},
    '神奈川県': {'lat': 35.4478, 'lon': 139.6425},
    '新潟県': {'lat': 37.9026, 'lon': 139.0236},
    '富山県': {'lat': 36.6953, 'lon': 137.2113},
    '石川県': {'lat': 36.5947, 'lon': 136.6256},
    '福井県': {'lat': 36.0652, 'lon': 136.2216},
    '山梨県': {'lat': 35.6642, 'lon': 138.5684},
    '長野県': {'lat': 36.6513, 'lon': 138.1810},
    '岐阜県': {'lat': 35.3912, 'lon': 136.7223},
    '静岡県': {'lat': 34.9769, 'lon': 138.3831},
    '愛知県': {'lat': 35.1815, 'lon': 136.9066},
    '三重県': {'lat': 34.7303, 'lon': 136.5086},
    '滋賀県': {'lat': 35.0045, 'lon': 135.8686},
    '京都府': {'lat': 35.0212, 'lon': 135.7556},
    '大阪府': {'lat': 34.6937, 'lon': 135.5022},
    '兵庫県': {'lat': 34.6913, 'lon': 135.1830},
    '奈良県': {'lat': 34.6851, 'lon': 135.8048},
    '和歌山県': {'lat': 34.2260, 'lon': 135.1675},
    '鳥取県': {'lat': 35.5011, 'lon': 134.2351},
    '島根県': {'lat': 35.4723, 'lon': 133.0505},
    '岡山県': {'lat': 34.6618, 'lon': 133.9350},
    '広島県': {'lat': 34.3966, 'lon': 132.4596},
    '山口県': {'lat': 34.1859, 'lon': 131.4714},
    '徳島県': {'lat': 34.0658, 'lon': 134.5593},
    '香川県': {'lat': 34.3401, 'lon': 134.0434},
    '愛媛県': {'lat': 33.8417, 'lon': 132.7657},
    '高知県': {'lat': 33.5597, 'lon': 133.5311},
    '福岡県': {'lat': 33.5902, 'lon': 130.4017},
    '佐賀県': {'lat': 33.2635, 'lon': 130.3009},
    '長崎県': {'lat': 32.7503, 'lon': 129.8777},
    '熊本県': {'lat': 32.7898, 'lon': 130.7417},
    '大分県': {'lat': 33.2382, 'lon': 131.6126},
    '宮崎県': {'lat': 31.9111, 'lon': 131.4239},
    '鹿児島県': {'lat': 31.5602, 'lon': 130.5581},
    '沖縄県': {'lat': 26.2123, 'lon': 127.6809}
}

def get_recommended_events():
    """ユーザーのタグに基づいておすすめのイベントを取得
    ユーザーが登録しているタグとイベントのタグが部分一致するイベントを返す
    """
    current_app.logger.info("API呼び出し: get_recommended_events")
    start_time = time.time()
    auth_header = request.headers.get('Authorization')
    limit = request.args.get('limit', default=10, type=int)
    
    if not auth_header or not auth_header.startswith('Bearer '):
        current_app.logger.warning("認証エラー: トークンがありません")
        return jsonify({"error": "認証が必要です"}), 401
    
    token = auth_header.split(' ')[1]
    
    try:
        user_id = verify_token(token)
        if not user_id:
            current_app.logger.warning(f"認証エラー: 無効なトークン")
            return jsonify({"error": "無効なトークンです"}), 401
        
        current_app.logger.info(f"ユーザーID: {user_id}のおすすめイベント取得を開始")
        
        # ユーザーのタグを取得
        user_tags = UserTagAssociation.query.filter_by(user_id=user_id).all()
        user_tag_ids = [ut.tag_id for ut in user_tags]
        
        if not user_tag_ids:
            # タグが設定されていない場合は最新のイベントを返す
            current_app.logger.info(f"ユーザーID: {user_id}のタグが設定されていないため最新イベントを取得")
            events = Event.query.order_by(Event.published_at.desc()).limit(limit).all()
        else:
            # ユーザーのタグに一致するイベントを検索
            current_app.logger.info(f"ユーザーID: {user_id}のタグ({user_tag_ids})に一致するイベントを検索")
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
        
        elapsed_time = time.time() - start_time
        current_app.logger.info(f"API呼び出し完了: get_recommended_events - イベント数: {len(result)}, 処理時間: {elapsed_time:.2f}秒")
        return jsonify({"events": result, "count": len(result), "page": 1})
        
    except Exception as e:
        current_app.logger.error(f"get_recommended_events エラー: {str(e)}")
        return jsonify({"error": "サーバーエラーが発生しました"}), 500
        
# API呼び出し用の関数
def recommended_events_api():
    """ユーザーのタグに基づいておすすめのイベントを取得するエンドポイント"""
    current_app.logger.info(f"APIエンドポイント呼び出し: recommended_events_api ({request.method} {request.path})")
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
    current_app.logger.info(f"APIエンドポイント呼び出し: events_list_api ({request.method} {request.path})")
    start_time = time.time()
    
    area_id = request.args.get('area_id')
    tag = request.args.get('tag')
    page = request.args.get('page', default=1, type=int)
    per_page = request.args.get('per_page', default=10, type=int)
    status = request.args.get('status')
    
    current_app.logger.info(f"検索条件: area_id={area_id}, tag={tag}, page={page}, per_page={per_page}, status={status}")
    
    result = get_events_list(area_id, tag, page, per_page, status)
    
    elapsed_time = time.time() - start_time
    current_app.logger.info(f"API呼び出し完了: events_list_api - イベント数: {result['count']}, 総数: {result['total']}, 処理時間: {elapsed_time:.2f}秒")
    
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
    current_app.logger.info(f"APIエンドポイント呼び出し: event_detail_api ({request.method} {request.path}) - event_id: {event_id}")
    start_time = time.time()
    
    auth_header = request.headers.get('Authorization')
    user_id = None
    
    if auth_header and auth_header.startswith('Bearer '):
        token = auth_header.split(' ')[1]
        user_id = verify_token(token)
        current_app.logger.info(f"認証済みユーザー: {user_id}")
    else:
        current_app.logger.info("未認証ユーザーからのアクセス")
    
    try:
        result = get_event_detail(event_id, user_id)
        
        elapsed_time = time.time() - start_time
        current_app.logger.info(f"API呼び出し完了: event_detail_api - event_id: {event_id}, 処理時間: {elapsed_time:.2f}秒")
        
        return jsonify(result)
    except Exception as e:
        current_app.logger.error(f"event_detail_api エラー - event_id: {event_id}, エラー: {str(e)}")
        return jsonify({"error": "イベント情報の取得に失敗しました"}), 500

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

def get_event_start_message(event_id=None, event_title=None, event_type=None):
    """
    天気・イベント内容に基づく過ごし方を含めた、イベント開始メッセージ生成
    """
    current_app.logger.info(f"get_event_start_message 呼び出し - event_id: {event_id}, event_title: {event_title}, event_type: {event_type}")
    start_time = time.time()

    base_messages = [
        "イベント開始時刻になりました。盛り上がっていきましょう！",
        "いよいよイベントが始まりました！皆さん、楽しんでいきましょう！",
        "ようこそ！イベントの時間です。どうぞお楽しみください！",
        "イベントがスタートしました。素敵な時間をお過ごしください！"
    ]

    event_description = None
    area_name = None
    area_lat = None
    area_lon = None

    # イベント情報の取得
    if event_id:
        try:
            event = Event.query.get(event_id)
            if event:
                current_app.logger.info(f"イベント情報取得成功: {event_id} - タイトル: {event.title}")
                event_title = event.title
                event_description = event.description
                if event.area_id:
                    area = AreaList.query.filter_by(area_id=event.area_id).first()
                    if area:
                        area_name = area.area_name
                        current_app.logger.info(f"イベントエリア情報: {area_name}")
            else:
                current_app.logger.warning(f"イベントが見つかりません: {event_id}")
        except Exception as e:
            current_app.logger.error(f"イベント情報取得エラー: {str(e)}")
            current_app.logger.error(traceback.format_exc())

    # エリア名から緯度経度を取得（データベースにない場合）
    if area_name and (area_lat is None or area_lon is None):
        # エリア名が完全一致する場合
        if area_name in AREA_COORDINATES:
            area_lat = AREA_COORDINATES[area_name]['lat']
            area_lon = AREA_COORDINATES[area_name]['lon']
            current_app.logger.info(f"エリア座標取得成功: {area_name} - 緯度: {area_lat}, 経度: {area_lon}")
        else:
            # 部分一致を試みる
            for key in AREA_COORDINATES:
                if key in area_name or area_name in key:
                    area_lat = AREA_COORDINATES[key]['lat']
                    area_lon = AREA_COORDINATES[key]['lon']
                    current_app.logger.info(f"エリア部分一致: {area_name} -> {key} - 緯度: {area_lat}, 経度: {area_lon}")
                    break
            if area_lat is None:
                current_app.logger.warning(f"エリア座標が見つかりません: {area_name}")

    # タイトル・エリア・説明メッセージの追加
    if event_title:
        base_messages.extend([
            f"「{event_title}」が始まりました！どうぞお楽しみください！",
            f"「{event_title}」へようこそ！素敵な時間をお過ごしください！"
        ])
        current_app.logger.debug(f"イベントタイトル用メッセージ追加: {event_title}")
    if area_name:
        base_messages.append(f"{area_name}でのイベント「{event_title}」が始まりました！")
        current_app.logger.debug(f"エリア情報付きメッセージ追加: {area_name}")
    if event_description:
        short_desc = event_description[:30] + "..." if len(event_description) > 30 else event_description
        base_messages.append(f"【イベント概要】{short_desc}")
        current_app.logger.debug(f"イベント概要メッセージ追加: {short_desc}")

    # 現在の天気を取得
    weather = None
    temp = None
    feels_like = None
    try:
        if area_lat and area_lon:
            weather_api_key = os.getenv("OPENWEATHER_API_KEY")
            if not weather_api_key:
                current_app.logger.warning("OPENWEATHER_API_KEYが設定されていません")
            else:
                # OpenWeather API 3.0のエンドポイントを使用
                # current_weather APIを使用（無料プランで利用可能）
                weather_url = (
                    f"https://api.openweathermap.org/data/3.0/onecall"
                    f"?lat={area_lat}&lon={area_lon}&appid={weather_api_key}&units=metric&lang=ja"
                    f"&exclude=minutely,hourly,daily,alerts"
                )
                
                # 旧APIのバックアップURL（API 3.0が利用できない場合用）
                backup_weather_url = (
                    f"https://api.openweathermap.org/data/2.5/weather"
                    f"?lat={area_lat}&lon={area_lon}&appid={weather_api_key}&units=metric&lang=ja"
                )
                
                current_app.logger.info(f"天気API呼び出し: {area_lat}, {area_lon}")
                
                try:
                    # 最初にAPI 3.0を試行
                    res = requests.get(weather_url, timeout=5)
                    current_app.logger.info(f"天気API 3.0応答: ステータスコード {res.status_code}")
                    
                    # API 3.0でエラーの場合（401など）、バックアップAPIを使用
                    if res.status_code != 200:
                        current_app.logger.warning(f"API 3.0でエラー: {res.status_code} - バックアップAPIを使用")
                        res = requests.get(backup_weather_url, timeout=5)
                        current_app.logger.info(f"天気APIバックアップ応答: ステータスコード {res.status_code}")
                    
                    if res.status_code == 200:
                        data = res.json()
                        
                        # API 3.0とAPI 2.5でレスポンス形式が異なるため分岐
                        if 'current' in data:  # API 3.0形式
                            current_data = data['current']
                            weather = current_data['weather'][0]['description']
                            temp = current_data['temp']
                            feels_like = current_data['feels_like']
                        else:  # API 2.5形式
                            weather = data['weather'][0]['description']
                            temp = data['main']['temp']
                            feels_like = data['main']['feels_like']
                            
                        current_app.logger.info(f"天気情報取得成功: {weather}, 気温: {temp}℃, 体感: {feels_like}℃")
                    else:
                        current_app.logger.error(f"両方の天気API応答エラー: {res.status_code} - {res.text}")
                        
                        # APIキーエラーの場合の追加ログ
                        if res.status_code == 401:
                            current_app.logger.error("APIキーエラー（401）：キーが無効か、アクティベートされていないか、有料機能へのアクセスが必要な可能性があります")
                            
                except requests.exceptions.Timeout:
                    current_app.logger.error("天気API呼び出しタイムアウト")
                except requests.exceptions.RequestException as e:
                    current_app.logger.error(f"天気API呼び出しエラー: {str(e)}")
    except Exception as e:
        current_app.logger.error(f"天気情報処理エラー: {str(e)}")
        current_app.logger.error(traceback.format_exc())

    # OpenAIで「おすすめの過ごし方」を生成
    suggestion = ""
    try:
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            current_app.logger.warning("OPENAI_API_KEYが設定されていません")
        else:
            client = OpenAI(api_key=openai_api_key)
            prompt = (
                f"以下の条件に基づいて、旅行者向けにおすすめの過ごし方を提案してください。\n\n"
                f"イベント名: {event_title or '不明'}\n"
                f"場所: {area_name or '不明'}\n"
                f"天気: {weather or '不明'}（気温{temp}℃、体感{feels_like}℃）\n"
                f"内容: {event_description or '詳細不明'}\n\n"
                f"おすすめの過ごし方を、丁寧で親しみやすい日本語で2〜3文で答えてください。"
            )
            current_app.logger.info(f"OpenAI API呼び出し - プロンプト長: {len(prompt)}文字")
            current_app.logger.debug(f"OpenAI プロンプト詳細: {prompt}")
            
            try:
                chat = client.chat.completions.create(
                    model="gpt-4.1-mini",  # フォールバックモデル
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=150,
                    temperature=0.8,
                    timeout=10,  # タイムアウト設定
                )
                suggestion = chat.choices[0].message.content.strip()
                current_app.logger.info(f"OpenAI API応答取得 - 応答長: {len(suggestion)}文字, モデル: gpt-4.1-mini")
                current_app.logger.debug(f"OpenAI 応答詳細: {suggestion}")
            except Exception as model_error:
                current_app.logger.error(f"OpenAI gpt-4.1-mini呼び出しエラー: {str(model_error)}")
                current_app.logger.info("フォールバックメッセージを使用します")
                
                # フォールバックメッセージ
                fallback_messages = [
                    f"{area_name or '現地'}の雰囲気を存分に楽しんでくださいね。素敵な思い出になりますように！",
                    f"イベントと共に、周辺の景観や文化にも触れてみると良いでしょう。素敵な一日をお過ごしください。",
                    f"皆さんと一緒に楽しい時間を過ごし、素敵な思い出を作ってくださいね。",
                    f"現地でしか味わえない体験を楽しみながら、素敵な時間をお過ごしください。"
                ]
                suggestion = random.choice(fallback_messages)
                current_app.logger.info(f"フォールバックメッセージ使用: {suggestion}")
    except Exception as e:
        current_app.logger.error(f"OpenAI API全体エラー: {str(e)}")
        current_app.logger.error(traceback.format_exc())
        
        # エラー時のフォールバックメッセージ
        fallback_messages = [
            "イベントの魅力を存分にお楽しみください！",
            "地元の文化や美味しいものを楽しみながら、素敵な時間をお過ごしください。",
            "参加者の皆さんと交流を深めながら、楽しい思い出を作ってくださいね。"
        ]
        suggestion = random.choice(fallback_messages)
        current_app.logger.info(f"エラー時フォールバックメッセージ使用: {suggestion}")

    # 最終メッセージの組み立て
    start_message = random.choice(base_messages)
    current_app.logger.debug(f"選択されたベースメッセージ: {start_message}")
    
    # 天気情報と提案を別々の段落として追加
    if weather:
        weather_info = f"\n\n今日の天気は「{weather}」です。気温は{temp}℃（体感{feels_like}℃）です。"
        start_message += weather_info
        current_app.logger.debug(f"天気情報追加: {weather_info}")
    
    if suggestion:
        suggestion_text = f"\n\n今日のおすすめは、{suggestion}\n\n張り切っていきましょう！"
        start_message += suggestion_text
        current_app.logger.debug(f"提案情報追加: {suggestion_text}")
    
    elapsed_time = time.time() - start_time
    current_app.logger.info(f"get_event_start_message 完了 - 処理時間: {elapsed_time:.2f}秒")
    current_app.logger.debug(f"最終メッセージ: {start_message}")
    
    return start_message

# 追加: イベント終了時のメッセージを生成する関数
def get_event_end_message(event_id=None, event_title=None, event_type=None):
    """
    天気・イベント内容に基づくお帰り情報を含めた、イベント終了メッセージ生成
    """
    current_app.logger.info(f"get_event_end_message 呼び出し - event_id: {event_id}, event_title: {event_title}, event_type: {event_type}")
    start_time = time.time()
    
    base_messages = [
        "イベントが終了しました。ご参加ありがとうございました！",
        "イベントは終了しました。本日は皆様のご参加、誠にありがとうございました！",
        "お疲れ様でした！イベントは終了となります。素敵な時間をありがとうございました！",
        "イベントの終了時刻となりました。本日はご参加いただき、ありがとうございました！"
    ]
    
    event_description = None
    area_name = None
    area_lat = None
    area_lon = None
    
    # イベント情報の取得
    if event_id:
        try:
            event = Event.query.get(event_id)
            if event:
                current_app.logger.info(f"イベント情報取得成功: {event_id} - タイトル: {event.title}")
                event_title = event.title
                event_description = event.description
                if event.area_id:
                    area = AreaList.query.filter_by(area_id=event.area_id).first()
                    if area:
                        area_name = area.area_name
                        current_app.logger.info(f"イベントエリア情報: {area_name}")
            else:
                current_app.logger.warning(f"イベントが見つかりません: {event_id}")
        except Exception as e:
            current_app.logger.error(f"イベント情報取得エラー: {str(e)}")
            current_app.logger.error(traceback.format_exc())
    
    # エリア名から緯度経度を取得（データベースにない場合）
    if area_name and (area_lat is None or area_lon is None):
        # エリア名が完全一致する場合
        if area_name in AREA_COORDINATES:
            area_lat = AREA_COORDINATES[area_name]['lat']
            area_lon = AREA_COORDINATES[area_name]['lon']
            current_app.logger.info(f"エリア座標取得成功: {area_name} - 緯度: {area_lat}, 経度: {area_lon}")
        else:
            # 部分一致を試みる
            for key in AREA_COORDINATES:
                if key in area_name or area_name in key:
                    area_lat = AREA_COORDINATES[key]['lat']
                    area_lon = AREA_COORDINATES[key]['lon']
                    current_app.logger.info(f"エリア部分一致: {area_name} -> {key} - 緯度: {area_lat}, 経度: {area_lon}")
                    break
            if area_lat is None:
                current_app.logger.warning(f"エリア座標が見つかりません: {area_name}")
    
    # タイトル・エリア・説明メッセージの追加
    if event_title:
        base_messages.extend([
            f"「{event_title}」は終了しました。ご参加いただき、ありがとうございました！",
            f"「{event_title}」の時間は終了です。素敵な時間をありがとうございました！"
        ])
        current_app.logger.debug(f"イベントタイトル用メッセージ追加: {event_title}")
    if area_name:
        base_messages.append(f"{area_name}でのイベント「{event_title}」は終了しました。ありがとうございました！")
        current_app.logger.debug(f"エリア情報付きメッセージ追加: {area_name}")
    
    # 現在の天気を取得
    weather = None
    temp = None
    feels_like = None
    try:
        if area_lat and area_lon:
            weather_api_key = os.getenv("OPENWEATHER_API_KEY")
            if not weather_api_key:
                current_app.logger.warning("OPENWEATHER_API_KEYが設定されていません")
            else:
                # OpenWeather API 3.0のエンドポイントを使用
                # current_weather APIを使用（無料プランで利用可能）
                weather_url = (
                    f"https://api.openweathermap.org/data/3.0/onecall"
                    f"?lat={area_lat}&lon={area_lon}&appid={weather_api_key}&units=metric&lang=ja"
                    f"&exclude=minutely,hourly,daily,alerts"
                )
                
                # 旧APIのバックアップURL（API 3.0が利用できない場合用）
                backup_weather_url = (
                    f"https://api.openweathermap.org/data/2.5/weather"
                    f"?lat={area_lat}&lon={area_lon}&appid={weather_api_key}&units=metric&lang=ja"
                )
                
                current_app.logger.info(f"天気API呼び出し: {area_lat}, {area_lon}")
                
                try:
                    # 最初にAPI 3.0を試行
                    res = requests.get(weather_url, timeout=5)
                    current_app.logger.info(f"天気API 3.0応答: ステータスコード {res.status_code}")
                    
                    # API 3.0でエラーの場合（401など）、バックアップAPIを使用
                    if res.status_code != 200:
                        current_app.logger.warning(f"API 3.0でエラー: {res.status_code} - バックアップAPIを使用")
                        res = requests.get(backup_weather_url, timeout=5)
                        current_app.logger.info(f"天気APIバックアップ応答: ステータスコード {res.status_code}")
                    
                    if res.status_code == 200:
                        data = res.json()
                        
                        # API 3.0とAPI 2.5でレスポンス形式が異なるため分岐
                        if 'current' in data:  # API 3.0形式
                            current_data = data['current']
                            weather = current_data['weather'][0]['description']
                            temp = current_data['temp']
                            feels_like = current_data['feels_like']
                        else:  # API 2.5形式
                            weather = data['weather'][0]['description']
                            temp = data['main']['temp']
                            feels_like = data['main']['feels_like']
                            
                        current_app.logger.info(f"天気情報取得成功: {weather}, 気温: {temp}℃, 体感: {feels_like}℃")
                    else:
                        current_app.logger.error(f"両方の天気API応答エラー: {res.status_code} - {res.text}")
                        
                        # APIキーエラーの場合の追加ログ
                        if res.status_code == 401:
                            current_app.logger.error("APIキーエラー（401）：キーが無効か、アクティベートされていないか、有料機能へのアクセスが必要な可能性があります")
                            
                except requests.exceptions.Timeout:
                    current_app.logger.error("天気API呼び出しタイムアウト")
                except requests.exceptions.RequestException as e:
                    current_app.logger.error(f"天気API呼び出しエラー: {str(e)}")
    except Exception as e:
        current_app.logger.error(f"天気情報処理エラー: {str(e)}")
        current_app.logger.error(traceback.format_exc())

    # OpenAIでお帰り時のおすすめ情報を生成
    suggestion = ""
    try:
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            current_app.logger.warning("OPENAI_API_KEYが設定されていません")
        else:
            client = OpenAI(api_key=openai_api_key)
            prompt = (
                f"以下の条件に基づいて、イベント終了後の帰り道や周辺での活動について提案してください。\n\n"
                f"イベント名: {event_title or '不明'}\n"
                f"場所: {area_name or '不明'}\n"
                f"天気: {weather or '不明'}（気温{temp}℃、体感{feels_like}℃）\n"
                f"内容: {event_description or '詳細不明'}\n\n"
                f"帰り道のアドバイスや周辺でのディナーなど、参加者へのお帰りの提案を、丁寧で親しみやすい日本語で2〜3文で答えてください。"
            )
            current_app.logger.info(f"OpenAI API呼び出し - プロンプト長: {len(prompt)}文字")
            current_app.logger.debug(f"OpenAI プロンプト詳細: {prompt}")
            
            try:
                chat = client.chat.completions.create(
                    model="gpt-4.1-mini",  # フォールバックモデル
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=150,
                    temperature=0.8,
                    timeout=10,  # タイムアウト設定
                )
                suggestion = chat.choices[0].message.content.strip()
                current_app.logger.info(f"OpenAI API応答取得 - 応答長: {len(suggestion)}文字, モデル: gpt-4.1-mini")
                current_app.logger.debug(f"OpenAI 応答詳細: {suggestion}")
            except Exception as model_error:
                current_app.logger.error(f"OpenAI gpt-4.1-mini呼び出しエラー: {str(model_error)}")
                current_app.logger.info("フォールバックメッセージを使用します")
                
                # フォールバックメッセージ
                fallback_messages = [
                    f"帰り道は安全に気をつけて、今日の素敵な思い出を大切にしてくださいね。",
                    f"周辺にはおいしいレストランがあるので、食事を楽しむのもお勧めです。お気をつけてお帰りください。",
                    f"今日の体験を振り返りながら、ゆっくり休んでください。また次回のイベントでお会いしましょう。",
                    f"今日の素敵な思い出とともに、安全にお帰りください。"
                ]
                suggestion = random.choice(fallback_messages)
                current_app.logger.info(f"フォールバックメッセージ使用: {suggestion}")
    except Exception as e:
        current_app.logger.error(f"OpenAI API全体エラー: {str(e)}")
        current_app.logger.error(traceback.format_exc())
        
        # エラー時のフォールバックメッセージ
        fallback_messages = [
            "お帰りの際はお気をつけて、今日の素敵な思い出を大切にしてくださいね。",
            "今日の体験が皆様の良い思い出になりますように。お気をつけてお帰りください。", 
            "素敵な時間をありがとうございました。安全にお帰りくださいね。"
        ]
        suggestion = random.choice(fallback_messages)
        current_app.logger.info(f"エラー時フォールバックメッセージ使用: {suggestion}")
    
    # 最終メッセージの組み立て
    end_message = random.choice(base_messages)
    current_app.logger.debug(f"選択されたベースメッセージ: {end_message}")
    
    # 天気情報と提案を別々の段落として追加
    if weather:
        weather_info = f"\n\n今日の天気は「{weather}」です。気温は{temp}℃（体感{feels_like}℃）です。"
        end_message += weather_info
        current_app.logger.debug(f"天気情報追加: {weather_info}")
    
    if suggestion:
        suggestion_text = f"\n\nお帰りの際のおすすめは、{suggestion}\n\nお気をつけてお帰りください。"
        end_message += suggestion_text
        current_app.logger.debug(f"提案情報追加: {suggestion_text}")
    
    elapsed_time = time.time() - start_time
    current_app.logger.info(f"get_event_end_message 完了 - 処理時間: {elapsed_time:.2f}秒")
    current_app.logger.debug(f"最終メッセージ: {end_message}")
    
    return end_message

# 追加: イベントの天気情報とアドバイスを取得する関数
def get_event_weather_info(event_id, location=None):
    """
    イベントIDと位置情報に基づいて、天気情報とアドバイスを取得する
    
    Args:
        event_id: イベントID
        location: 位置情報 (緯度・経度)
    
    Returns:
        dict: 天気情報とアドバイス
    """
    current_app.logger.info(f"get_event_weather_info 呼び出し - event_id: {event_id}")
    start_time = time.time()
    
    event_title = None
    area_name = None
    area_lat = None
    area_lon = None
    
    # イベント情報の取得
    if event_id:
        try:
            event = Event.query.get(event_id)
            if event:
                current_app.logger.info(f"イベント情報取得成功: {event_id} - タイトル: {event.title}")
                event_title = event.title
                if event.area_id:
                    area = AreaList.query.filter_by(area_id=event.area_id).first()
                    if area:
                        area_name = area.area_name
                        current_app.logger.info(f"イベントエリア情報: {area_name}")
            else:
                current_app.logger.warning(f"イベントが見つかりません: {event_id}")
        except Exception as e:
            current_app.logger.error(f"イベント情報取得エラー: {str(e)}")
            current_app.logger.error(traceback.format_exc())
    
    # 位置情報の処理
    if location and 'latitude' in location and 'longitude' in location:
        # クライアントから送信された位置情報を使用
        area_lat = location['latitude']
        area_lon = location['longitude']
        current_app.logger.info(f"クライアント位置情報使用: 緯度: {area_lat}, 経度: {area_lon}")
    elif area_name:
        # エリア名から緯度経度を取得
        if area_name in AREA_COORDINATES:
            area_lat = AREA_COORDINATES[area_name]['lat']
            area_lon = AREA_COORDINATES[area_name]['lon']
            current_app.logger.info(f"エリア座標取得成功: {area_name} - 緯度: {area_lat}, 経度: {area_lon}")
        else:
            # 部分一致を試みる
            for key in AREA_COORDINATES:
                if key in area_name or area_name in key:
                    area_lat = AREA_COORDINATES[key]['lat']
                    area_lon = AREA_COORDINATES[key]['lon']
                    current_app.logger.info(f"エリア部分一致: {area_name} -> {key} - 緯度: {area_lat}, 経度: {area_lon}")
                    break
            if area_lat is None:
                current_app.logger.warning(f"エリア座標が見つかりません: {area_name}")
    
    # 天気情報の初期化
    weather_info = {
        'weather': '不明',
        'temp': 20,
        'feels_like': 20
    }
    
    # 服装やアドバイスの初期値
    clothing_advice = "今日の天気は取得できませんでしたが、季節に合わせた服装でお出かけください。"
    event_advice = "イベントを楽しむために、水分補給を忘れずにしましょう。"
    
    # 天気情報の取得
    try:
        if area_lat and area_lon:
            weather_api_key = os.getenv("OPENWEATHER_API_KEY")
            if not weather_api_key:
                current_app.logger.warning("OPENWEATHER_API_KEYが設定されていません")
            else:
                # OpenWeather API 3.0のエンドポイントを使用
                # current_weather APIを使用（無料プランで利用可能）
                weather_url = (
                    f"https://api.openweathermap.org/data/3.0/onecall"
                    f"?lat={area_lat}&lon={area_lon}&appid={weather_api_key}&units=metric&lang=ja"
                    f"&exclude=minutely,hourly,daily,alerts"
                )
                
                # 旧APIのバックアップURL（API 3.0が利用できない場合用）
                backup_weather_url = (
                    f"https://api.openweathermap.org/data/2.5/weather"
                    f"?lat={area_lat}&lon={area_lon}&appid={weather_api_key}&units=metric&lang=ja"
                )
                
                current_app.logger.info(f"天気API呼び出し: {area_lat}, {area_lon}")
                
                try:
                    # 最初にAPI 3.0を試行
                    res = requests.get(weather_url, timeout=5)
                    current_app.logger.info(f"天気API 3.0応答: ステータスコード {res.status_code}")
                    
                    # API 3.0でエラーの場合（401など）、バックアップAPIを使用
                    if res.status_code != 200:
                        current_app.logger.warning(f"API 3.0でエラー: {res.status_code} - バックアップAPIを使用")
                        res = requests.get(backup_weather_url, timeout=5)
                        current_app.logger.info(f"天気APIバックアップ応答: ステータスコード {res.status_code}")
                    
                    if res.status_code == 200:
                        data = res.json()
                        
                        # API 3.0とAPI 2.5でレスポンス形式が異なるため分岐
                        if 'current' in data:  # API 3.0形式
                            current_data = data['current']
                            weather_info = {
                                'weather': current_data['weather'][0]['description'],
                                'temp': current_data['temp'],
                                'feels_like': current_data['feels_like']
                            }
                        else:  # API 2.5形式
                            weather_info = {
                                'weather': data['weather'][0]['description'],
                                'temp': data['main']['temp'],
                                'feels_like': data['main']['feels_like']
                            }
                            
                        current_app.logger.info(f"天気情報取得成功: {weather_info['weather']}, 気温: {weather_info['temp']}℃, 体感: {weather_info['feels_like']}℃")
                    else:
                        current_app.logger.error(f"両方の天気API応答エラー: {res.status_code} - {res.text}")
                        
                        # APIキーエラーの場合の追加ログ
                        if res.status_code == 401:
                            current_app.logger.error("APIキーエラー（401）：キーが無効か、アクティベートされていないか、有料機能へのアクセスが必要な可能性があります")
                            
                except requests.exceptions.Timeout:
                    current_app.logger.error("天気API呼び出しタイムアウト")
                except requests.exceptions.RequestException as e:
                    current_app.logger.error(f"天気API呼び出しエラー: {str(e)}")
    except Exception as e:
        current_app.logger.error(f"天気情報処理エラー: {str(e)}")
        current_app.logger.error(traceback.format_exc())
    
    # OpenAIで服装アドバイスとイベント楽しみ方のアドバイスを生成
    try:
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            current_app.logger.warning("OPENAI_API_KEYが設定されていません")
        else:
            client = OpenAI(api_key=openai_api_key)
            prompt = (
                f"以下の条件に基づいて、イベント参加者への服装とイベントの楽しみ方のアドバイスをください。\n\n"
                f"イベント名: {event_title or '不明'}\n"
                f"場所: {area_name or '不明'}\n"
                f"天気: {weather_info['weather']}（気温{weather_info['temp']}℃、体感{weather_info['feels_like']}℃）\n\n"
                f"このイベントに参加する人が着るべき服装と、イベントを楽しむために気をつけるべきことを日本語で2〜3文でアドバイスしてください。"
            )
            current_app.logger.info(f"OpenAI API呼び出し - プロンプト長: {len(prompt)}文字")
            
            try:
                chat = client.chat.completions.create(
                    model="gpt-4.1-mini",  # フォールバックモデル
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=150,
                    temperature=0.8,
                    timeout=10,  # タイムアウト設定
                )
                advice = chat.choices[0].message.content.strip()
                current_app.logger.info(f"OpenAI API応答取得 - 応答長: {len(advice)}文字")
                
                # 服装とイベントのアドバイスを統合
                clothing_advice = advice
            except Exception as model_error:
                current_app.logger.error(f"OpenAI gpt-4.1-mini呼び出しエラー: {str(model_error)}")
                current_app.logger.info("フォールバックメッセージを使用します")
                
                # フォールバックメッセージ
                if weather_info['temp'] >= 30:
                    clothing_advice = "気温が高いので、軽装で熱中症対策を忘れずに。帽子や日傘、こまめな水分補給がおすすめです。イベントを楽しむために、無理せず休憩を取りながら参加しましょう。"
                elif weather_info['temp'] >= 25:
                    clothing_advice = "暖かい気温なので、軽めの服装がおすすめです。日差しが強い場合は日焼け対策も。イベントを楽しむために、水分補給を忘れずに行いましょう。"
                elif weather_info['temp'] >= 15:
                    clothing_advice = "過ごしやすい気温ですが、長袖や薄手のジャケットがあると安心です。イベントに集中できるよう、快適な服装で参加しましょう。"
                elif weather_info['temp'] >= 5:
                    clothing_advice = "肌寒いので、上着やセーターなど温かい服装がおすすめです。イベント会場の温度差に備えて、脱ぎ着しやすい服装だと便利でしょう。"
                else:
                    clothing_advice = "気温が低いので、コートやマフラーなど防寒対策をしっかりと。イベントを楽しむためには、体調管理が大切です。温かい飲み物を持参すると良いでしょう。"
                
                if weather_info['weather'] == '雨' or '雨' in weather_info['weather']:
                    clothing_advice += " 雨が降っているので、傘や雨具をお忘れなく。足元が濡れないよう注意して、イベントを楽しみましょう。"
                
                current_app.logger.info(f"フォールバックメッセージ使用: {clothing_advice}")
    except Exception as e:
        current_app.logger.error(f"OpenAI API全体エラー: {str(e)}")
        current_app.logger.error(traceback.format_exc())
    
    response = {
        'weather_info': weather_info,
        'advice': clothing_advice
    }
    
    elapsed_time = time.time() - start_time
    current_app.logger.info(f"get_event_weather_info 完了 - 処理時間: {elapsed_time:.2f}秒")
    
    return response

# API呼び出し用の関数
def event_weather_info_api(event_id):
    """イベントの天気情報とアドバイスを取得するエンドポイント"""
    current_app.logger.info(f"APIエンドポイント呼び出し: event_weather_info_api ({request.method} {request.path}) - event_id: {event_id}")
    
    auth_header = request.headers.get('Authorization')
    
    if not auth_header or not auth_header.startswith('Bearer '):
        current_app.logger.warning("認証エラー: トークンがありません")
        return jsonify({"error": "認証が必要です"}), 401
    
    token = auth_header.split(' ')[1]
    
    try:
        user_id = verify_token(token)
        if not user_id:
            current_app.logger.warning(f"認証エラー: 無効なトークン")
            return jsonify({"error": "無効なトークンです"}), 401
        
        # リクエストボディの取得
        data = request.json or {}
        location = data.get('location')
        
        result = get_event_weather_info(event_id, location)
        return jsonify(result)
    except Exception as e:
        current_app.logger.error(f"event_weather_info_api エラー: {str(e)}")
        current_app.logger.error(traceback.format_exc())
        return jsonify({"error": "天気情報の取得に失敗しました"}), 500 