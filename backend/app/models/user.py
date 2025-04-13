# アプリケーション内でユーザーに関するデータ構造と処理をまとめる場所
from app.models import db 
from werkzeug.security import generate_password_hash, check_password_hash


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    profile_image_url = db.Column(db.String(512)) 

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# DBアクセス用ヘルパー関数
def get_user_by_email(email: str) -> User | None:
    return User.query.filter_by(email=email).first()
