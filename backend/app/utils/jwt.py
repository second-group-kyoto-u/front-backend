import jwt
import datetime
from datetime import datetime, timezone, timedelta
import os

JST = timezone(timedelta(hours=9))

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-jwt-secret")

def generate_token(user_id):
    payload = {
        'user_id': user_id,
        'exp': datetime.now(JST) + timedelta(days=7),  # 有効期限: 7日
        'iat': datetime.now(JST)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm='HS256')

def decode_token(token):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        return payload['user_id']
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

# verify_token関数を追加（decode_tokenのエイリアス）
def verify_token(token):
    """
    トークンを検証し、ユーザーIDを返す
    decode_token関数のエイリアス
    """
    return decode_token(token)
