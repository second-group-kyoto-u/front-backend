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
            
        response = requests.get(url, params=params, timeout=30)
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
            
        response = requests.get(url, params=params, timeout=30)
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