# アプリケーション内でユーザーに関するデータ構造と処理をまとめる場所
from werkzeug.security import generate_password_hash, check_password_hash

# 仮のユーザーデータベース（実際はSQLやORMで管理）
users_db = {
    "test@example.com": {
        "id": 1,
        "email": "test@example.com",
        "password": generate_password_hash("password123"),
    }
}

def get_user_by_email(email: str):
    return users_db.get(email)

def verify_password(stored_password_hash, input_password):
    return check_password_hash(stored_password_hash, input_password)
