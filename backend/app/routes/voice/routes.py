from flask import Blueprint, request, jsonify, current_app
from app.routes.protected.routes import get_authenticated_user
import openai
import os
import base64
import tempfile
import io
from pydub import AudioSegment
import requests
import json
import re
from datetime import datetime, timedelta
import pytz

voice_bp = Blueprint("voice", __name__)

# 専用のOpenAI APIキーを取得
CHAT_OPENAI_API_KEY = os.getenv("CHAT_OPENAI_API")

def get_character_system_prompt(character_id: str) -> str:
    """キャラクターIDに基づいてシステムプロンプトを取得"""
    character_prompts = {
        'nyanta': "あなたはイベントの「ニャンタ」アドバイザーです。ツンデレな猫ちゃんの口調で、語尾に「ニャ♪」「ニャー」をつけて話します。会話を盛り上げたり、おすすめの場所を提案したりして、イベントを楽しくサポートしてください💕 ちょっぴり照れ屋だけど、みんなのことを思って一生懸命アドバイスします！",
        'hitsuji': "あなたはイベントの「ヒツジ」アドバイザーです。優しくふわふわな口調で「〜だよ♪」「〜なんです✨」という感じで話します。会話を盛り上げたり、素敵な場所をおすすめしたりして、みんなを笑顔にするお手伝いをしてください☁️😊 温かい雰囲気でイベントをサポートします！",
        'koko': "あなたはイベントの「ココ」アドバイザーです。超元気で明るい口調で「だよー！」「だねっ！」「やったー！」など、ポジティブに話します。会話を盛り上げたり、ワクワクする場所をおすすめしたりして、みんなをテンション上げちゃいます🌟🎉 楽しいイベントになるよう全力でサポート！",
        'fukurou': "あなたはイベントの「フクロウ」アドバイザーです。知識豊富で親しみやすい口調で「〜だよん♪」「なるほどね〜✨」という感じで話します。会話を盛り上げたり、おすすめスポットを分かりやすく教えたりして、みんなの役に立つアドバイスをしてください🦉📚 賢くて頼れるサポーターです！",
        'toraberu': "あなたはイベントの「トラベル」アドバイザーです。冒険大好きで超テンション高めの口調で「だぜー！」「最高だー！」「行こうぜ〜♪」などノリノリに話します。会話を盛り上げたり、冒険心をくすぐる場所をおすすめしたりして、みんなをワクワクさせてください🗺️✈️🌍 一緒に素敵な冒険（イベント）を楽しもう！"
    }
    return character_prompts.get(character_id, "あなたはイベントアドバイザーです。会話を盛り上げたり、おすすめの場所を提案したりして、楽しいイベントをサポートしてください♪")

def get_character_voice(character_id: str) -> str:
    """キャラクターIDに基づいてTTS音声を取得"""
    character_voices = {
        'nyanta': "shimmer",    # ツンデレな猫 - 可愛らしく少し高めの音声
        'hitsuji': "nova",      # 優しい羊 - 優しく丁寧な音声
        'koko': "fable",        # 元気で明るい - 活発で明るい音声
        'fukurou': "onyx",      # 知的で落ち着いた - 深みがあり落ち着いた音声
        'toraberu': "echo"      # 冒険好きで活発 - 元気で豪快な音声
    }
    return character_voices.get(character_id, "alloy")  # デフォルトはalloy

def analyze_time_specification(user_text: str) -> dict:
    """ユーザーの発話から時間指定を解析"""
    user_text_lower = user_text.lower()
    
    # 現在時刻を取得（日本時間）
    jst = pytz.timezone('Asia/Tokyo')
    now = datetime.now(jst)
    
    time_patterns = {
        # 相対時間指定
        '今': {'type': 'current', 'offset_hours': 0},
        '現在': {'type': 'current', 'offset_hours': 0},
        '明日': {'type': 'daily', 'offset_days': 1},
        '明後日': {'type': 'daily', 'offset_days': 2},
        '来週': {'type': 'daily', 'offset_days': 7},
        
        # 時間後指定
        '1時間後': {'type': 'hourly', 'offset_hours': 1},
        '2時間後': {'type': 'hourly', 'offset_hours': 2},
        '3時間後': {'type': 'hourly', 'offset_hours': 3},
        '4時間後': {'type': 'hourly', 'offset_hours': 4},
        '5時間後': {'type': 'hourly', 'offset_hours': 5},
        '6時間後': {'type': 'hourly', 'offset_hours': 6},
        
        # 時間帯指定
        '朝': {'type': 'time_of_day', 'target_hour': 8},
        '午前': {'type': 'time_of_day', 'target_hour': 10},
        '昼': {'type': 'time_of_day', 'target_hour': 12},
        '午後': {'type': 'time_of_day', 'target_hour': 14},
        '夕方': {'type': 'time_of_day', 'target_hour': 17},
        '夜': {'type': 'time_of_day', 'target_hour': 20},
        '深夜': {'type': 'time_of_day', 'target_hour': 23},
    }
    
    # マッチした時間指定を検索
    matched_time = None
    for pattern, time_spec in time_patterns.items():
        if pattern in user_text:
            matched_time = time_spec
            matched_time['keyword'] = pattern
            break
    
    # 数字＋時間後のパターンをチェック
    if not matched_time:
        hour_match = re.search(r'(\d+)時間後', user_text)
        if hour_match:
            hours = int(hour_match.group(1))
            matched_time = {'type': 'hourly', 'offset_hours': hours, 'keyword': f'{hours}時間後'}
    
    return matched_time

def analyze_user_intent(user_text: str) -> dict:
    """ユーザーの発話内容を分析して必要なAPIを判断"""
    user_text_lower = user_text.lower()
    
    # 天気関連のキーワード
    weather_keywords = [
        '天気', '気温', '暑い', '寒い', '雨', '晴れ', '曇り', '雪',
        '服装', '着る', '傘', '日傘', '気候', '湿度', '風', '降水',
        '予報', '明日', '今日', '時間後', '朝', '昼', '夜', '夕方'
    ]
    
    # 場所・おすすめ関連のキーワード
    location_keywords = [
        '場所', 'おすすめ', 'カフェ', 'レストラン', '店', '施設',
        '近く', '周辺', 'どこ', '食事', '観光', 'スポット',
        '行く', '訪れる', '見る', '買い物', 'ショッピング', '美味しい',
        'コンビニ', 'ATM', '駅', '公園', '病院', 'ホテル', '銀行'
    ]
    
    # 詳細検索キーワード（より具体的な場所検索）
    detailed_location_keywords = [
        'ランチ', 'ディナー', 'デート', '安い', '高級', '24時間',
        '個室', 'テラス', 'ペット', '子供', 'ファミリー', 'カップル'
    ]
    
    needs_weather = any(keyword in user_text for keyword in weather_keywords)
    needs_location = any(keyword in user_text for keyword in location_keywords)
    needs_detailed_search = any(keyword in user_text for keyword in detailed_location_keywords)
    
    # 時間指定の解析
    time_specification = analyze_time_specification(user_text)
    
    return {
        'needs_weather': needs_weather,
        'needs_location': needs_location,
        'needs_detailed_search': needs_detailed_search,
        'time_specification': time_specification,
        'analysis_reason': {
            'weather_match': [kw for kw in weather_keywords if kw in user_text],
            'location_match': [kw for kw in location_keywords if kw in user_text],
            'detailed_match': [kw for kw in detailed_location_keywords if kw in user_text]
        }
    }

def get_detailed_weather_info(event_id: str, location_data: dict, time_spec: dict = None) -> dict:
    """詳細な天気情報を時間指定に応じて取得"""
    try:
        if not location_data or 'latitude' not in location_data or 'longitude' not in location_data:
            return None
            
        lat = location_data['latitude']
        lon = location_data['longitude']
        
        weather_api_key = os.getenv("OPENWEATHER_API_KEY")
        if not weather_api_key:
            print("OPENWEATHER_API_KEYが設定されていません")
            return None
        
        # OneCall API 3.0を使用（hourly、dailyデータ含む）
        weather_url = (
            f"https://api.openweathermap.org/data/3.0/onecall"
            f"?lat={lat}&lon={lon}&appid={weather_api_key}&units=metric&lang=ja"
        )
        
        response = requests.get(weather_url, timeout=30)
        if response.status_code != 200:
            print(f"天気API応答エラー: {response.status_code}")
            return None
            
        data = response.json()
        
        # 時間指定に応じたデータを抽出
        if time_spec:
            return extract_weather_by_time(data, time_spec)
        else:
            # 現在の天気情報のみ
            current = data.get('current', {})
            return {
                'weather': current.get('weather', [{}])[0].get('description', '不明'),
                'temp': current.get('temp', 20),
                'feels_like': current.get('feels_like', 20),
                'humidity': current.get('humidity', 50),
                'wind_speed': current.get('wind_speed', 0),
                'time_type': 'current'
            }
            
    except Exception as e:
        print(f"詳細天気情報取得エラー: {str(e)}")
        return None

def extract_weather_by_time(weather_data: dict, time_spec: dict) -> dict:
    """時間指定に応じて適切な天気データを抽出"""
    jst = pytz.timezone('Asia/Tokyo')
    now = datetime.now(jst)
    
    if time_spec['type'] == 'current':
        current = weather_data.get('current', {})
        return {
            'weather': current.get('weather', [{}])[0].get('description', '不明'),
            'temp': current.get('temp', 20),
            'feels_like': current.get('feels_like', 20),
            'humidity': current.get('humidity', 50),
            'wind_speed': current.get('wind_speed', 0),
            'time_type': 'current',
            'time_description': '現在'
        }
    
    elif time_spec['type'] == 'hourly':
        # 時間後の天気予報
        target_hour = time_spec['offset_hours']
        hourly_data = weather_data.get('hourly', [])
        
        if target_hour < len(hourly_data):
            hour_weather = hourly_data[target_hour]
            return {
                'weather': hour_weather.get('weather', [{}])[0].get('description', '不明'),
                'temp': hour_weather.get('temp', 20),
                'feels_like': hour_weather.get('feels_like', 20),
                'humidity': hour_weather.get('humidity', 50),
                'wind_speed': hour_weather.get('wind_speed', 0),
                'time_type': 'hourly',
                'time_description': f'{target_hour}時間後'
            }
    
    elif time_spec['type'] == 'daily':
        # 明日以降の天気予報
        target_day = time_spec['offset_days']
        daily_data = weather_data.get('daily', [])
        
        if target_day < len(daily_data):
            day_weather = daily_data[target_day]
            return {
                'weather': day_weather.get('weather', [{}])[0].get('description', '不明'),
                'temp': day_weather.get('temp', {}).get('day', 20),
                'temp_min': day_weather.get('temp', {}).get('min', 15),
                'temp_max': day_weather.get('temp', {}).get('max', 25),
                'humidity': day_weather.get('humidity', 50),
                'wind_speed': day_weather.get('wind_speed', 0),
                'time_type': 'daily',
                'time_description': '明日' if target_day == 1 else f'{target_day}日後'
            }
    
    elif time_spec['type'] == 'time_of_day':
        # 特定時間帯の天気予報
        target_hour = time_spec['target_hour']
        current_hour = now.hour
        
        if target_hour < current_hour:
            # 翌日の同時刻
            hours_ahead = (24 - current_hour) + target_hour
        else:
            # 今日の指定時刻
            hours_ahead = target_hour - current_hour
        
        hourly_data = weather_data.get('hourly', [])
        if hours_ahead < len(hourly_data):
            hour_weather = hourly_data[hours_ahead]
            return {
                'weather': hour_weather.get('weather', [{}])[0].get('description', '不明'),
                'temp': hour_weather.get('temp', 20),
                'feels_like': hour_weather.get('feels_like', 20),
                'humidity': hour_weather.get('humidity', 50),
                'wind_speed': hour_weather.get('wind_speed', 0),
                'time_type': 'time_of_day',
                'time_description': time_spec['keyword']
            }
    
    # フォールバック：現在の天気
    current = weather_data.get('current', {})
    return {
        'weather': current.get('weather', [{}])[0].get('description', '不明'),
        'temp': current.get('temp', 20),
        'feels_like': current.get('feels_like', 20),
        'time_type': 'current',
        'time_description': '現在'
    }

def get_enhanced_nearby_places(lat, lng, user_text: str, radius=500):
    """ユーザーの要求に応じた詳細な場所検索"""
    try:
        from app.utils.openai_utils import get_nearby_places
        
        # ユーザーの検索意図に応じて検索タイプを決定
        search_types = []
        
        if any(word in user_text for word in ['カフェ', 'コーヒー', '休憩']):
            search_types.append('cafe')
        if any(word in user_text for word in ['レストラン', '食事', 'ランチ', 'ディナー', '美味しい']):
            search_types.append('restaurant')
        if any(word in user_text for word in ['コンビニ', 'セブン', 'ローソン', 'ファミマ']):
            search_types.append('convenience_store')
        if any(word in user_text for word in ['ATM', '銀行', '引き出し']):
            search_types.append('atm')
        if any(word in user_text for word in ['駅', '電車', '地下鉄']):
            search_types.append('transit_station')
        if any(word in user_text for word in ['公園', '緑', '散歩']):
            search_types.append('park')
        if any(word in user_text for word in ['病院', '薬局', '医療']):
            search_types.extend(['hospital', 'pharmacy'])
        if any(word in user_text for word in ['ホテル', '宿泊', '泊まる']):
            search_types.append('lodging')
        if any(word in user_text for word in ['買い物', 'ショッピング', '店']):
            search_types.extend(['shopping_mall', 'store'])
        
        # 検索タイプが指定されていない場合は一般的な検索
        if not search_types:
            search_types = [None]  # 一般検索
        
        all_places = []
        for search_type in search_types:
            places = get_nearby_places(lat, lng, radius, search_type)
            if places:
                all_places.extend(places)
        
        # 重複を除去し、評価順にソート
        unique_places = {}
        for place in all_places:
            place_id = place.get('place_id')
            if place_id and place_id not in unique_places:
                unique_places[place_id] = place
        
        # 評価の高い順に最大5件まで
        sorted_places = sorted(
            [p for p in unique_places.values() if p.get("rating", 0) > 0], 
            key=lambda x: x.get("rating", 0), 
            reverse=True
        )[:5]
        
        result = []
        for place in sorted_places:
            result.append({
                "name": place.get("name", "不明"),
                "rating": place.get("rating", 0),
                "types": place.get("types", []),
                "vicinity": place.get("vicinity", ""),
                "price_level": place.get("price_level")
            })
        
        return result
        
    except Exception as e:
        print(f"拡張場所検索エラー: {str(e)}")
        return []

def get_nearby_places_for_voice(lat, lng, radius=300):
    """音声チャット用の簡略化された近くの場所取得"""
    try:
        from app.utils.openai_utils import get_nearby_places, get_place_details
        
        # 近くの場所を検索
        nearby_places = get_nearby_places(lat, lng, radius)
        if not nearby_places:
            return []
            
        # 評価の高い上位3つを取得
        top_places = sorted(
            [p for p in nearby_places if p.get("rating", 0) > 0], 
            key=lambda x: x.get("rating", 0), 
            reverse=True
        )[:3]
        
        result = []
        for place in top_places:
            result.append({
                "name": place.get("name", "不明"),
                "rating": place.get("rating", 0),
                "types": place.get("types", [])
            })
        
        return result
    except Exception as e:
        print(f"近くの場所取得エラー: {str(e)}")
        return []

def create_ai_intelligent_prompt(character_id: str, user_text: str, ai_analysis: dict, weather_data=None, nearby_places=None):
    """AI解析結果に基づいたインテリジェントプロンプトを作成"""
    # 基本的なキャラクタープロンプト
    base_prompt = get_character_system_prompt(character_id)
    
    # 追加情報を組み立て
    additional_context = []
    
    # 必要な場合のみ天気情報を追加
    if ai_analysis.get('needs_weather') and weather_data:
        time_desc = weather_data.get('time_description', '現在')
        weather_text = f"{time_desc}の天気は{weather_data.get('weather', '不明')}"
        
        if weather_data.get('time_type') == 'daily' and weather_data.get('temp_min'):
            weather_text += f"、最低{weather_data.get('temp_min')}℃〜最高{weather_data.get('temp_max')}℃"
        else:
            weather_text += f"、{weather_data.get('temp', '不明')}℃"
        
        weather_text += "です。"
        additional_context.append(weather_text)
        
        print(f"AI判定による天気情報をプロンプトに追加: {weather_text}")
    
    # 必要な場合のみ近くの場所情報を追加（簡潔版）
    if ai_analysis.get('needs_location') and nearby_places:
        places_text = "近くの施設："
            
        for i, place in enumerate(nearby_places):
            if i > 0:
                places_text += "、"
            
            # 基本情報のみ
            place_info = f"【{place['name']}】({place['rating']}/5.0)"
            
            # 価格レベル表示
            if place.get('price_level'):
                price_symbols = '¥' * place['price_level']
                place_info += f"({price_symbols})"
            
            # 簡潔なレビュー（1件のみ、短縮版）
            if place.get('reviews') and len(place['reviews']) > 0:
                best_review = place['reviews'][0]
                review_text = best_review.get('text', '')
                if len(review_text) > 30:
                    review_text = review_text[:30] + "..."
                if review_text:
                    place_info += f" 「{review_text}」"
            
            places_text += place_info
        
        additional_context.append(places_text)
        
        print(f"AI判定による簡潔場所情報をプロンプトに追加: {len(nearby_places)}件の施設")
    
    # 拡張されたシステムプロンプトを構築
    if additional_context:
        enhanced_prompt = f"""{base_prompt}

現在の状況:
{chr(10).join(additional_context)}

この情報を参考に、親しみやすく簡潔に答えてください♪ 自己紹介は省略し、質問に関連する情報があれば自然に活用してくださいね✨"""
    else:
        enhanced_prompt = base_prompt
        print("AI判定: 追加情報なし - 基本プロンプトのみ使用")
    
    return enhanced_prompt

@voice_bp.route("/chat", methods=["POST", "OPTIONS"])
def voice_chat():
    if request.method == "OPTIONS":
        response = current_app.make_response('')
        response.headers['Access-Control-Allow-Origin'] = request.headers.get('Origin', '*')
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response

    # ユーザー認証
    user, error_response, error_code = get_authenticated_user()
    if error_response:
        return jsonify(error_response), error_code

    if not CHAT_OPENAI_API_KEY:
        return jsonify({"error": "CHAT_OPENAI_API環境変数が設定されていません"}), 500

    try:
        data = request.get_json()
        character_id = data.get('character_id')
        audio_data = data.get('audio_data')  # base64 encoded
        event_id = data.get('event_id')
        location_data = data.get('location')  # 位置情報

        if not all([character_id, audio_data, event_id]):
            return jsonify({"error": "必要なパラメータが不足しています"}), 400

        # WhisperとTTS用のOpenAIクライアント（CHAT_OPENAI_API使用）
        audio_client = openai.OpenAI(api_key=CHAT_OPENAI_API_KEY)

        # base64音声データをデコード
        audio_bytes = base64.b64decode(audio_data)
        
        # 一時ファイルに保存してWhisper APIで音声認識
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_audio:
            temp_audio.write(audio_bytes)
            temp_audio.flush()
            
            try:
                # Whisper APIで音声をテキストに変換（CHAT_OPENAI_API使用）
                with open(temp_audio.name, "rb") as audio_file:
                    transcript = audio_client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file,
                        language="ja"
                    )
                
                user_text = transcript.text
                print(f"音声認識結果: {user_text}")
                
                # AI解析によるユーザーの意図分析
                ai_analysis = ai_analyze_user_intent(user_text)
                print(f"AI意図解析結果: {json.dumps(ai_analysis, indent=2, ensure_ascii=False)}")
                
                # 必要に応じてAPIを呼び出し
                weather_data = None
                nearby_places = None
                
                # 天気情報が必要な場合のみ取得
                if ai_analysis.get('needs_weather') and location_data:
                    print("AI判定による詳細天気情報を取得中...")
                    time_spec = ai_generate_time_specification(ai_analysis.get('weather_analysis', {}))
                    weather_data = get_detailed_weather_info(event_id, location_data, time_spec)
                
                # 場所情報が必要な場合のみ取得
                if ai_analysis.get('needs_location') and location_data:
                    print("AI判定による拡張場所検索を実行中...")
                    nearby_places = ai_enhanced_nearby_places(
                        location_data['latitude'], 
                        location_data['longitude'],
                        ai_analysis.get('location_analysis', {})
                    )
                
                # AI解析に基づくインテリジェントプロンプトを作成
                system_prompt = create_ai_intelligent_prompt(
                    character_id, 
                    user_text, 
                    ai_analysis, 
                    weather_data, 
                    nearby_places
                )
                
                # ChatGPT応答生成用のOpenAIクライアント（OPENAI_API_KEY使用）
                openai_api_key = os.getenv("OPENAI_API_KEY")
                if not openai_api_key:
                    return jsonify({"error": "OPENAI_API_KEY環境変数が設定されていません"}), 500
                
                chat_client = openai.OpenAI(api_key=openai_api_key)
                
                # ChatGPT APIでレスポンスを生成（gpt-4.1-mini + OPENAI_API_KEY使用）
                chat_response = chat_client.chat.completions.create(
                    model="gpt-4.1-mini",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_text}
                    ],
                    max_tokens=250,  # より詳細な回答のため増量
                    temperature=0.8
                )
                
                response_text = chat_response.choices[0].message.content
                print(f"ChatGPT応答 (GPT-4.1-mini): {response_text}")
                
                # キャラクター専用の音声を取得
                character_voice = get_character_voice(character_id)
                print(f"使用する音声: {character_voice} (キャラクター: {character_id})")
                
                # TTS APIで音声を生成（CHAT_OPENAI_API使用）
                tts_response = audio_client.audio.speech.create(
                    model="tts-1",
                    voice=character_voice,  # キャラクターごとの音声を使用
                    input=response_text
                )
                
                # 音声データをbase64エンコード
                audio_content = tts_response.content
                audio_base64 = base64.b64encode(audio_content).decode('utf-8')
                
                return jsonify({
                    "response_text": response_text,
                    "audio_data": audio_base64,
                    "character_id": character_id,
                    "debug_info": {
                        "intent_analysis": ai_analysis,
                        "weather_used": weather_data is not None,
                        "location_used": nearby_places is not None,
                        "weather_data": weather_data,
                        "location_count": len(nearby_places) if nearby_places else 0
                    }
                })
                
            finally:
                # 一時ファイルを削除
                os.unlink(temp_audio.name)
                
    except openai.OpenAIError as e:
        print(f"OpenAI APIエラー: {e}")
        return jsonify({"error": f"OpenAI APIエラー: {str(e)}"}), 500
    except Exception as e:
        print(f"音声チャットエラー: {e}")
        return jsonify({"error": f"音声処理エラー: {str(e)}"}), 500

def ai_analyze_user_intent(user_text: str) -> dict:
    """生成AIを使ってユーザーの意図を分析"""
    try:
        # 意図解析には4.1-miniとOPENAI_API_KEYを使用
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            print("OPENAI_API_KEY環境変数が設定されていません")
            return fallback_analyze_user_intent(user_text)
            
        client = openai.OpenAI(api_key=openai_api_key)
        
        # 現在時刻を取得（日本時間）
        jst = pytz.timezone('Asia/Tokyo')
        now = datetime.now(jst)
        current_time_str = now.strftime("%Y年%m月%d日 %H時%M分")
        current_hour = now.hour
        current_weekday = ["月", "火", "水", "木", "金", "土", "日"][now.weekday()]
        
        analysis_prompt = f"""
あなたは音声チャットアシスタントの意図解析エンジンです。
ユーザーの発話を分析して、以下の情報をJSON形式で出力してください。

現在時刻: {current_time_str} ({current_weekday}曜日)
現在の時刻: {current_hour}時

ユーザーの発話: "{user_text}"

以下のJSON形式で回答してください：

{{
  "needs_weather": boolean,
  "needs_location": boolean,
  "weather_analysis": {{
    "time_type": "current|hourly|daily|time_of_day|none",
    "time_description": "時間の説明",
    "offset_hours": number|null,
    "offset_days": number|null,
    "target_hour": number|null,
    "reasoning": "判定理由"
  }},
  "location_analysis": {{
    "search_type": "general|restaurant|cafe|convenience|atm|transit|park|hospital|hotel|shopping|none",
    "search_keywords": ["検索キーワード1", "検索キーワード2"],
    "detailed_requirements": ["詳細要求1", "詳細要求2"],
    "reasoning": "判定理由"
  }},
  "overall_reasoning": "全体的な判定理由"
}}

判定ガイドライン：
1. 天気情報が必要かどうかを判定（天気、気温、雨、服装、傘など）
2. 場所情報が必要かどうかを判定（おすすめ、近く、カフェ、レストランなど）
3. 時間指定があれば解析（今、明日、3時間後、夕方など）
4. 場所検索の種類を特定（カフェ、レストラン、コンビニなど）
5. 詳細な検索要求を抽出（安い、個室、24時間営業など）

時間指定の例：
- "今"/"現在" → current
- "3時間後"/"2時間後" → hourly (offset_hours: 3)
- "明日"/"明後日" → daily (offset_days: 1)
- "夕方"/"朝"/"夜" → time_of_day (target_hour: 17/8/20)

場所検索の例：
- カフェ、コーヒー → cafe
- レストラン、食事、ランチ → restaurant
- コンビニ → convenience
- ATM、銀行 → atm
- 駅、電車 → transit
- 公園 → park
- 病院、薬局 → hospital
- ホテル、宿泊 → hotel
- ショッピング、買い物 → shopping
"""

        response = client.chat.completions.create(
            model="gpt-4.1-mini",  # 意図解析には4.1-miniを使用
            messages=[
                {"role": "system", "content": "あなたは優秀な自然言語解析AIです。ユーザーの発話を正確に分析してJSONで回答してください。"},
                {"role": "user", "content": analysis_prompt}
            ],
            max_tokens=500,
            temperature=0.1  # 安定した結果のため低めに設定
        )
        
        ai_response = response.choices[0].message.content
        print(f"AI解析応答 (GPT-4.1-mini): {ai_response}")
        
        # JSONパースを試行
        try:
            analysis_result = json.loads(ai_response)
            return analysis_result
        except json.JSONDecodeError:
            # JSONパースに失敗した場合は、修正を試みる
            try:
                # ```json と ``` を除去
                cleaned_response = ai_response.strip()
                if cleaned_response.startswith('```json'):
                    cleaned_response = cleaned_response[7:]
                if cleaned_response.endswith('```'):
                    cleaned_response = cleaned_response[:-3]
                
                analysis_result = json.loads(cleaned_response.strip())
                return analysis_result
            except json.JSONDecodeError as e:
                print(f"AI応答のJSONパースエラー: {e}")
                # フォールバック: 従来のキーワードベース解析
                return fallback_analyze_user_intent(user_text)
                
    except Exception as e:
        print(f"AI意図解析エラー: {str(e)}")
        # フォールバック: 従来のキーワードベース解析
        return fallback_analyze_user_intent(user_text)

def fallback_analyze_user_intent(user_text: str) -> dict:
    """AIが失敗した場合のフォールバック解析"""
    return analyze_user_intent(user_text)

def ai_generate_time_specification(weather_analysis: dict) -> dict:
    """AI解析結果から時間指定オブジェクトを生成"""
    if not weather_analysis or weather_analysis.get('time_type') == 'none':
        return None
    
    time_spec = {
        'type': weather_analysis.get('time_type'),
        'keyword': weather_analysis.get('time_description', ''),
    }
    
    if weather_analysis.get('offset_hours') is not None:
        time_spec['offset_hours'] = weather_analysis['offset_hours']
    
    if weather_analysis.get('offset_days') is not None:
        time_spec['offset_days'] = weather_analysis['offset_days']
    
    if weather_analysis.get('target_hour') is not None:
        time_spec['target_hour'] = weather_analysis['target_hour']
    
    return time_spec

def ai_enhanced_nearby_places(lat, lng, location_analysis: dict, radius=500):
    """AI解析結果に基づく拡張場所検索（詳細情報付き）"""
    try:
        from app.utils.openai_utils import get_nearby_places, get_place_details
        
        search_type = location_analysis.get('search_type', 'general')
        search_keywords = location_analysis.get('search_keywords', [])
        detailed_requirements = location_analysis.get('detailed_requirements', [])
        
        # Google Places APIの検索タイプマッピング
        google_types_mapping = {
            'restaurant': 'restaurant',
            'cafe': 'cafe',
            'convenience': 'convenience_store',
            'atm': 'atm',
            'transit': 'transit_station',
            'park': 'park',
            'hospital': 'hospital',
            'hotel': 'lodging',
            'shopping': 'shopping_mall',
            'general': None
        }
        
        google_search_type = google_types_mapping.get(search_type)
        
        # 基本検索を実行
        all_places = []
        if google_search_type:
            places = get_nearby_places(lat, lng, radius, google_search_type)
            if places:
                all_places.extend(places)
        else:
            # 一般検索：複数タイプを検索
            for place_type in ['restaurant', 'cafe', 'store']:
                places = get_nearby_places(lat, lng, radius, place_type)
                if places:
                    all_places.extend(places[:3])  # 各タイプから3件ずつ
        
        # 重複を除去
        unique_places = {}
        for place in all_places:
            place_id = place.get('place_id')
            if place_id and place_id not in unique_places:
                unique_places[place_id] = place
        
        # AI判定による詳細要求に基づくフィルタリング
        filtered_places = []
        for place in unique_places.values():
            should_include = True
            
            # 詳細要求による追加フィルタリング
            if detailed_requirements:
                place_name_lower = place.get('name', '').lower()
                place_types = [t.lower() for t in place.get('types', [])]
                
                # 価格関連の要求
                if '安い' in detailed_requirements:
                    price_level = place.get('price_level', 2)
                    if price_level > 2:  # 価格レベルが高い場合は除外
                        should_include = False
                elif '高級' in detailed_requirements:
                    price_level = place.get('price_level', 2)
                    if price_level < 3:  # 価格レベルが低い場合は除外
                        should_include = False
                
                # 24時間営業の要求
                if '24時間' in detailed_requirements:
                    # この判定は簡略化（実際はPlace Details APIが必要）
                    if 'convenience_store' not in place_types:
                        should_include = False
            
            if should_include:
                filtered_places.append(place)
        
        # 評価順にソート
        sorted_places = sorted(
            [p for p in filtered_places if p.get("rating", 0) > 0],
            key=lambda x: x.get("rating", 0),
            reverse=True
        )[:5]
        
        # 詳細情報を取得
        result = []
        for place in sorted_places:
            place_id = place.get('place_id')
            
            # 基本情報
            place_info = {
                "name": place.get("name", "不明"),
                "rating": place.get("rating", 0),
                "types": place.get("types", []),
                "vicinity": place.get("vicinity", ""),
                "price_level": place.get("price_level"),
                "ai_match_keywords": search_keywords,
                "ai_requirements": detailed_requirements
            }
            
            # 詳細情報を取得（get_place_detailsを使用）
            if place_id:
                try:
                    place_details = get_place_details(place_id)
                    if place_details:
                        # 詳細情報を追加
                        place_info.update({
                            "formatted_address": place_details.get("formatted_address", ""),
                            "website": place_details.get("website", ""),
                            "phone_number": place_details.get("formatted_phone_number", ""),
                            "opening_hours": place_details.get("opening_hours", {}).get("weekday_text", []),
                            "editorial_summary": place_details.get("editorial_summary", {}).get("overview", "")
                        })
                        
                        # レビュー情報（最新の2件）
                        reviews = place_details.get("reviews", [])
                        if reviews:
                            place_info["reviews"] = [{
                                "text": review.get("text", ""),
                                "rating": review.get("rating", 0),
                                "time": review.get("relative_time_description", ""),
                                "author": review.get("author_name", "")
                            } for review in reviews[:2]]
                        
                        print(f"詳細情報取得成功: {place_info['name']} - 住所: {place_info.get('formatted_address', 'なし')}")
                    else:
                        print(f"詳細情報取得失敗: {place_info['name']}")
                except Exception as detail_error:
                    print(f"詳細情報取得エラー: {place_info['name']} - {str(detail_error)}")
            
            result.append(place_info)
        
        print(f"AI拡張場所検索完了: {len(result)}件の詳細情報付き施設を取得")
        return result
        
    except Exception as e:
        print(f"AI拡張場所検索エラー: {str(e)}")
        return [] 