import jwt
import datetime
from datetime import timezone
import os

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-jwt-secret")

def generate_token(user_id):
    payload = {
        'user_id': user_id,
        'exp': datetime.datetime.now(timezone.utc) + datetime.timedelta(days=7),  # 有効期限: 7日
        'iat': datetime.datetime.now(timezone.utc)
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
