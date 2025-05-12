import os
import json
from openai import OpenAI
import requests
from flask import current_app
import logging

# APIキーの確認とデバッグメッセージ
api_key = os.getenv("OPENAI_API_KEY")
print(f"OPENAI_API_KEY環境変数: {'設定されています' if api_key else '設定されていません'}")
if api_key:
    # 最初の10文字と最後の5文字だけを表示（セキュリティのため）
    masked_key = f"{api_key[:10]}...{api_key[-5:]}"
    print(f"APIキー(マスク済み): {masked_key}")

# Google Places APIキーの確認
google_places_api_key = os.getenv("GOOGLE_PLACES_API_KEY")
print(f"GOOGLE_PLACES_API_KEY環境変数: {'設定されています' if google_places_api_key else '設定されていません'}")

# OpenAI APIクライアントの初期化
try:
    client = OpenAI(api_key=api_key)
    print("OpenAIクライアントの初期化に成功しました")
except Exception as e:
    print(f"OpenAIクライアントの初期化に失敗しました: {str(e)}")

def log_info(message):
    """ログ情報を出力する"""
    print(f"[INFO] {message}")
    if hasattr(current_app, 'logger'):
        current_app.logger.info(message)

def log_error(message):
    """エラーログを出力する"""
    print(f"[ERROR] {message}")
    if hasattr(current_app, 'logger'):
        current_app.logger.error(message)

def get_nearby_places(lat, lng, radius=500, type=None):
    """
    Google Places APIを使用して、指定された場所の近くの施設を検索します
    
    Args:
        lat: 緯度
        lng: 経度
        radius: 検索半径（メートル）
        type: 場所のタイプ（例：restaurant, cafe, park など）
        
    Returns:
        検索結果のリスト
    """
    try:
        api_key = os.getenv("GOOGLE_PLACES_API_KEY")
        if not api_key:
            print("GOOGLE_PLACES_API_KEYが設定されていません")
            return None
            
        url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
        params = {
            "location": f"{lat},{lng}",
            "radius": radius,
            "key": api_key,
            "language": "ja"
        }
        
        if type:
            params["type"] = type
            
        response = requests.get(url, params=params)
        if response.status_code != 200:
            print(f"Google Places API エラー: ステータスコード {response.status_code}")
            return None
            
        data = response.json()
        if data.get("status") != "OK":
            print(f"Google Places API エラー: {data.get('status')}")
            return None
            
        return data.get("results", [])
    except Exception as e:
        print(f"近くの施設検索エラー: {str(e)}")
        return None

def get_place_details(place_id):
    """
    Google Places APIを使用して、場所の詳細情報（レビューを含む）を取得します
    
    Args:
        place_id: Google Places APIの場所ID
        
    Returns:
        場所の詳細情報
    """
    try:
        api_key = os.getenv("GOOGLE_PLACES_API_KEY")
        if not api_key:
            print("GOOGLE_PLACES_API_KEYが設定されていません")
            return None
            
        url = "https://maps.googleapis.com/maps/api/place/details/json"
        params = {
            "place_id": place_id,
            "key": api_key,
            "language": "ja",
            "fields": "name,rating,reviews,types,formatted_address,website,editorial_summary"
        }
            
        response = requests.get(url, params=params)
        if response.status_code != 200:
            print(f"Google Places API エラー: ステータスコード {response.status_code}")
            return None
            
        data = response.json()
        if data.get("status") != "OK":
            print(f"Google Places API エラー: {data.get('status')}")
            return None
            
        return data.get("result")
    except Exception as e:
        print(f"場所の詳細取得エラー: {str(e)}")
        return None

def get_location_info(lat, lng):
    """
    緯度・経度から位置情報の詳細を取得する
    
    Args:
        lat: 緯度
        lng: 経度
        
    Returns:
        位置情報の詳細（地名、住所など）を含む辞書
    """
    try:
        # OpenStreetMapのNominatimジオコーディングAPIを使用（無料でAPIキー不要）
        url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lng}&format=json&accept-language=ja"
        response = requests.get(
            url,
            headers={"User-Agent": "EventTalkApp/1.0"}  # User-Agentヘッダーは必須
        )
        data = response.json()
        
        # レスポンスから必要な情報を抽出
        location_info = {
            "display_name": data.get("display_name", ""),
            "address": {
                "country": data.get("address", {}).get("country", ""),
                "state": data.get("address", {}).get("state", ""),
                "city": data.get("address", {}).get("city", ""),
                "town": data.get("address", {}).get("town", ""),
                "suburb": data.get("address", {}).get("suburb", ""),
                "road": data.get("address", {}).get("road", "")
            }
        }
        return location_info
    except Exception as e:
        print(f"位置情報の詳細取得エラー: {str(e)}")
        return None

def get_place_info_for_prompt(lat, lng):
    """
    ユーザーの位置情報から、近くの場所の詳細とレビュー情報を取得し、プロンプト用に整形します
    
    Args:
        lat: 緯度
        lng: 経度
        
    Returns:
        プロンプト用の場所情報テキスト
    """
    try:
        print("=" * 50)
        log_info(f"位置情報から場所情報を取得開始: 緯度={lat}, 経度={lng}")
        
        # 位置情報の基本情報を取得
        location_info = get_location_info(lat, lng)
        if location_info:
            log_info(f"位置情報基本情報: {location_info.get('display_name', 'なし')}")
        
        # 近くの場所を検索
        log_info(f"周辺施設を検索中... (半径300m)")
        nearby_places = get_nearby_places(lat, lng, radius=300)
        
        if not nearby_places or len(nearby_places) == 0:
            log_info("周辺施設が見つかりませんでした")
            return {"location_basic": location_info, "nearby_places": []}
            
        log_info(f"周辺施設が{len(nearby_places)}件見つかりました")
            
        # 検索結果のうち、最も評価の高い場所をいくつか選ぶ
        top_places = sorted(
            [p for p in nearby_places if p.get("rating", 0) > 0], 
            key=lambda x: x.get("rating", 0), 
            reverse=True
        )[:3]
        
        log_info(f"上位{len(top_places)}件の施設情報を取得します")
        for i, place in enumerate(top_places):
            log_info(f"  - {i+1}. {place.get('name', '不明')} (評価: {place.get('rating', '不明')})")
        
        detailed_places = []
        
        # トップの場所について詳細情報を取得
        for place in top_places:
            log_info(f"施設詳細情報を取得中: {place.get('name', '不明')} (place_id: {place.get('place_id', '不明')})")
            place_details = get_place_details(place.get("place_id"))
            if place_details:
                place_info = {
                    "name": place_details.get("name", "不明"),
                    "address": place_details.get("formatted_address", ""),
                    "rating": place_details.get("rating", "なし"),
                    "types": place_details.get("types", []),
                    "website": place_details.get("website", ""),
                    "summary": place_details.get("editorial_summary", {}).get("overview", "")
                }
                
                log_info(f"取得成功: {place_info['name']}, 住所: {place_info['address']}, 評価: {place_info['rating']}")
                
                # レビューがあれば追加（最新の2つまで）
                reviews = place_details.get("reviews", [])
                if reviews:
                    log_info(f"レビュー {len(reviews)}件を取得")
                    place_info["reviews"] = [{
                        "text": review.get("text", ""),
                        "rating": review.get("rating", 0),
                        "time": review.get("relative_time_description", "")
                    } for review in reviews[:2]]
                else:
                    log_info("レビュー情報なし")
                
                detailed_places.append(place_info)
            else:
                log_info(f"施設詳細情報の取得に失敗")
        
        log_info(f"合計{len(detailed_places)}件の施設詳細情報を取得しました")
        print("=" * 50)
        return {"location_basic": location_info, "nearby_places": detailed_places}
        
    except Exception as e:
        log_error(f"場所情報取得エラー: {str(e)}")
        print("=" * 50)
        return {"location_basic": None, "nearby_places": []}

def generate_event_trivia(event_topic: str, location_info=None) -> str:
    """
    イベントのトピックに関連する豆知識を生成する
    
    Args:
        event_topic: イベントのトピックやテーマ
        location_info: ユーザーの位置情報（オプション）
        
    Returns:
        生成された豆知識のテキスト
    """
    try:
        print("=" * 50)
        log_info(f"豆知識生成開始: トピック='{event_topic}'")
            
        # システムプロンプトとユーザープロンプトを設定
        system_prompt = """
        あなたはイベント関連の豆知識を提供するbot assistantです。
        与えられたイベントトピックに関する面白い、役立つ、または意外な豆知識を1つ提供してください。
        回答は日本語で、100〜200文字程度に簡潔にまとめてください。
        豆知識は参加者の会話のきっかけになるような内容にしてください。
        現在地や周辺施設の情報が提供されている場合は、それらを活用した豆知識が望ましいです。
        """
        
        user_prompt = f"以下のイベントトピックに関する豆知識を教えてください: {event_topic}"
        
        # 位置情報が提供されている場合は、場所情報を取得してプロンプトに追加
        place_info = None
        if location_info and "latitude" in location_info and "longitude" in location_info:
            log_info(f"位置情報あり: 緯度={location_info['latitude']}, 経度={location_info['longitude']}")
            
            # 位置情報から場所の詳細情報を取得
            place_info = get_place_info_for_prompt(
                location_info["latitude"], 
                location_info["longitude"]
            )
            
            if place_info and place_info.get("location_basic"):
                loc_basic = place_info.get("location_basic", {})
                location_str = f"現在地は以下の場所です: {loc_basic.get('display_name', '')}"
                user_prompt += f"\n\n{location_str}"
                log_info(f"現在地情報をプロンプトに追加: {loc_basic.get('display_name', '')}")
            
            # 近くの場所情報があれば追加
            if place_info and place_info.get("nearby_places"):
                nearby = place_info.get("nearby_places", [])
                log_info(f"周辺施設情報({len(nearby)}件)をプロンプトに追加")
                user_prompt += "\n\n近くには以下の場所があります:"
                
                for i, place in enumerate(nearby):
                    log_info(f"施設{i+1}: {place.get('name', '不明')}")
                    user_prompt += f"\n\n【場所 {i+1}】"
                    user_prompt += f"\n名称: {place.get('name', '不明')}"
                    user_prompt += f"\n住所: {place.get('address', '不明')}"
                    user_prompt += f"\n評価: {place.get('rating', '不明')}/5.0"
                    
                    if place.get("summary"):
                        user_prompt += f"\n概要: {place['summary']}"
                        log_info(f"概要情報あり: {str(place['summary'])[:50]}...")
                    
                    if place.get("reviews"):
                        user_prompt += "\nレビュー:"
                        log_info(f"レビュー情報あり: {len(place.get('reviews', []))}件")
                        for review in place.get("reviews", []):
                            user_prompt += f"\n- 「{str(review.get('text', ''))[:100]}...」({review.get('rating', '不明')}点、{review.get('time', '不明')})"
                
                user_prompt += "\n\nこれらの場所に関連した豆知識や、現在地周辺に関連した豆知識を提供してください。"
        else:
            log_info("位置情報なし: イベントトピックのみで豆知識を生成します")
        
        log_info(f"OpenAI APIリクエスト: モデル=gpt-4.1-mini, システムプロンプト長={len(system_prompt)}文字, ユーザープロンプト長={len(user_prompt)}文字")
        
        # OpenAI APIを呼び出し
        response = client.chat.completions.create(
            model="gpt-4.1-mini",  # 指定のモデルを使用
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,  # 創造性のバランス
            max_tokens=200
        )
        
        # レスポンスから豆知識テキストを取得
        trivia_text = response.choices[0].message.content.strip()
        log_info(f"豆知識生成成功: 生成テキスト長={len(trivia_text)}文字")
        log_info(f"生成された豆知識: {trivia_text}")
        print("=" * 50)
        return trivia_text
        
    except Exception as e:
        # エラーが発生した場合はデフォルトの豆知識を返す
        error_msg = f"OpenAI API エラー: {str(e)}"
        log_error(error_msg)
        print("=" * 50)
        return "豆知識の生成中にエラーが発生しました。しばらく経ってからもう一度お試しください。"

def generate_conversation_starter(event_topic: str, location_info=None) -> str:
    """
    イベントのトピックに関連する会話のきっかけとなる質問を生成する
    
    Args:
        event_topic: イベントのトピックやテーマ
        location_info: ユーザーの位置情報（オプション）
        
    Returns:
        生成された会話のきっかけとなる質問
    """
    try:
        print("=" * 50)
        log_info(f"会話のきっかけ生成開始: トピック='{event_topic}'")
            
        # システムプロンプトとユーザープロンプトを設定
        system_prompt = """
        あなたは会話を促進するbot assistantです。
        与えられたイベントトピックに関連する、参加者同士の会話のきっかけとなる質問を1つ提供してください。
        質問は日本語で、簡潔で、回答しやすく、参加者全員が参加できるものにしてください。
        現在地や周辺施設の情報が提供されている場合は、それらを活用した質問が望ましいです。
        """
        
        user_prompt = f"以下のイベントトピックに関連する会話のきっかけとなる質問を作成してください: {event_topic}"
        
        # 位置情報が提供されている場合は、場所情報を取得してプロンプトに追加
        place_info = None
        if location_info and "latitude" in location_info and "longitude" in location_info:
            log_info(f"位置情報あり: 緯度={location_info['latitude']}, 経度={location_info['longitude']}")
            
            # 位置情報から場所の詳細情報を取得
            place_info = get_place_info_for_prompt(
                location_info["latitude"], 
                location_info["longitude"]
            )
            
            if place_info and place_info.get("location_basic"):
                loc_basic = place_info.get("location_basic", {})
                location_str = f"現在地は以下の場所です: {loc_basic.get('display_name', '')}"
                user_prompt += f"\n\n{location_str}"
                log_info(f"現在地情報をプロンプトに追加: {loc_basic.get('display_name', '')}")
            
            # 近くの場所情報があれば追加
            if place_info and place_info.get("nearby_places"):
                nearby = place_info.get("nearby_places", [])
                log_info(f"周辺施設情報({len(nearby)}件)をプロンプトに追加")
                user_prompt += "\n\n近くには以下の場所があります:"
                
                for i, place in enumerate(nearby):
                    log_info(f"施設{i+1}: {place.get('name', '不明')}")
                    user_prompt += f"\n\n【場所 {i+1}】"
                    user_prompt += f"\n名称: {place.get('name', '不明')}"
                    user_prompt += f"\n住所: {place.get('address', '不明')}"
                    user_prompt += f"\n評価: {place.get('rating', '不明')}/5.0"
                    
                    if place.get("summary"):
                        user_prompt += f"\n概要: {place['summary']}"
                        log_info(f"概要情報あり: {str(place['summary'])[:50]}...")
                    
                    if place.get("reviews"):
                        user_prompt += "\nレビュー:"
                        log_info(f"レビュー情報あり: {len(place.get('reviews', []))}件")
                        for review in place.get("reviews", []):
                            user_prompt += f"\n- 「{str(review.get('text', ''))[:100]}...」({review.get('rating', '不明')}点、{review.get('time', '不明')})"
                
                user_prompt += "\n\nこれらの場所に関連した質問や、現在地周辺に関連した質問を提供してください。"
        else:
            log_info("位置情報なし: イベントトピックのみで会話のきっかけを生成します")
        
        log_info(f"OpenAI APIリクエスト: モデル=gpt-4.1-mini, システムプロンプト長={len(system_prompt)}文字, ユーザープロンプト長={len(user_prompt)}文字")
        
        # OpenAI APIを呼び出し
        response = client.chat.completions.create(
            model="gpt-4.1-mini",  # 指定のモデルを使用
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=100
        )
        
        # レスポンスから質問テキストを取得
        question = response.choices[0].message.content.strip()
        log_info(f"会話のきっかけ生成成功: 生成テキスト長={len(question)}文字")
        log_info(f"生成された会話のきっかけ: {question}")
        print("=" * 50)
        return question
        
    except Exception as e:
        # エラーが発生した場合はデフォルトの質問を返す
        error_msg = f"OpenAI API エラー: {str(e)}"
        log_error(error_msg)
        print("=" * 50)
        return "みなさん、このイベントに参加した理由を教えていただけますか？" 