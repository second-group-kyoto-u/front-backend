from app import create_app
from app.models import db
from app.models.user import User
import uuid

app = create_app()

with app.app_context():
    # テストユーザーの作成
    test_user = User(
        id=str(uuid.uuid4()),
        user_name="TestUser",
        email_address="test@example.com",
        profile_message="This is a test user",
        is_certificated=True
    )
    test_user.set_password("password123")
    
    # 既存のユーザーを確認
    existing_user = User.query.filter_by(email_address="test@example.com").first()
    if existing_user:
        print(f"ユーザーは既に存在します: {existing_user.email_address}")
    else:
        db.session.add(test_user)
        db.session.commit()
        print(f"ユーザーを作成しました: {test_user.email_address} / password123") 