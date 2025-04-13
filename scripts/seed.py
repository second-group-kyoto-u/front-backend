import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.models.user import db, User
import boto3
from werkzeug.utils import secure_filename
from botocore.exceptions import ClientError

# MinIO設定
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "http://minio:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
MINIO_BUCKET = os.getenv("MINIO_BUCKET", "user-profile-images")
TEST_IMAGE_PATH = os.path.join(os.path.dirname(__file__), "test.png")

s3 = boto3.client(
    "s3",
    endpoint_url=MINIO_ENDPOINT,
    aws_access_key_id=MINIO_ACCESS_KEY,
    aws_secret_access_key=MINIO_SECRET_KEY,
    region_name="us-east-1"
)

app = create_app()

with app.app_context():
    db.drop_all()
    db.create_all()

    try:
        s3.head_bucket(Bucket=MINIO_BUCKET)
        print(f"📦 バケット '{MINIO_BUCKET}' は既に存在します")
    except ClientError:
        print(f"📦 バケット '{MINIO_BUCKET}' を作成します")
        s3.create_bucket(Bucket=MINIO_BUCKET)

    if not User.query.filter_by(email="test@example.com").first():
        user = User(email="test@example.com")
        user.set_password("123")
        db.session.add(user)
        db.session.commit()
        print("✅ ユーザー追加完了: test@example.com / 123")

        user_id = user.id
        filename = f"user_{user_id}_profile.jpg"
        try:
            with open(TEST_IMAGE_PATH, "rb") as f:
                s3.upload_fileobj(f, MINIO_BUCKET, filename)
                print(f"🖼️ 画像アップロード成功: {filename}")
            image_url = f"http://localhost:9000/{MINIO_BUCKET}/{filename}"
            user.profile_image_url = image_url
            db.session.commit()
            print(f"🔗 プロフィール画像URL登録済み: {image_url}")
        except FileNotFoundError:
            print("⚠️ test.png が見つかりません。scripts ディレクトリに配置してください。")
