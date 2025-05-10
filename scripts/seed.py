import sys, os
import uuid
from datetime import datetime, timedelta
from sqlalchemy import text

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.models import db
from app.models.user import User
from app.models.event import Event, UserMemberGroup, UserHeartEvent, TagMaster, UserTagAssociation, EventTagAssociation, ThreadTagAssociation
from app.models.area import AreaList
from app.models.file import ImageList
from app.models.thread import Thread, ThreadMessage, UserHeartThread
from app.models.message import EventMessage
import boto3
from werkzeug.utils import secure_filename
from botocore.exceptions import ClientError

# MinIO設定
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "http://minio:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
MINIO_BUCKET = os.getenv("MINIO_BUCKET", "user-profile-images")
EVENT_BUCKET = "event-images"
THREAD_BUCKET = "thread-images"
TEST_IMAGE_PATH = os.path.join(os.path.dirname(__file__), "test.png")

s3 = boto3.client(
    "s3",
    endpoint_url=MINIO_ENDPOINT,
    aws_access_key_id=MINIO_ACCESS_KEY,
    aws_secret_access_key=MINIO_SECRET_KEY,
    region_name="us-east-1"
)

def create_buckets():
    """必要なバケットを作成"""
    for bucket in [MINIO_BUCKET, EVENT_BUCKET, THREAD_BUCKET]:
        try:
            s3.head_bucket(Bucket=bucket)
            print(f"📦 バケット '{bucket}' は既に存在します")
        except ClientError:
            print(f"📦 バケット '{bucket}' を作成します")
            s3.create_bucket(Bucket=bucket)

def upload_image(bucket, path, key):
    """画像をアップロード"""
    try:
        with open(path, "rb") as f:
            s3.upload_fileobj(f, bucket, key)
            print(f"🖼️ 画像アップロード成功: {key}")
        return f"http://localhost:9000/{bucket}/{key}"
    except FileNotFoundError:
        print(f"⚠️ {path} が見つかりません。")
        return None

app = create_app()

## テーブルのリセット
with app.app_context():
    conn = db.engine.connect()
    
    # 外部キー制約を無効化
    conn.execute(text("SET FOREIGN_KEY_CHECKS=0"))

    # 明示的にメタデータをdrop
    db.metadata.drop_all(bind=conn)

    # 外部キー制約を再び有効化
    conn.execute(text("SET FOREIGN_KEY_CHECKS=1"))
    conn.close()
    db.create_all()

    

    # バケットを作成
    create_buckets()
    
    # エリアデータを作成
    areas = [
        {"id": str(uuid.uuid4()), "name": "東京"},
        {"id": str(uuid.uuid4()), "name": "大阪"},
        {"id": str(uuid.uuid4()), "name": "京都"},
        {"id": str(uuid.uuid4()), "name": "沖縄"},
        {"id": str(uuid.uuid4()), "name": "北海道"}
    ]
    
    for area in areas:
        area_obj = AreaList(area_id=area["id"], area_name=area["name"])
        db.session.add(area_obj)
    
    db.session.commit()
    print("✅ エリア情報を追加しました")
    
    # タグマスターを作成
    tags = [
        {"id": str(uuid.uuid4()), "name": "自然"},
        {"id": str(uuid.uuid4()), "name": "グルメ"},
        {"id": str(uuid.uuid4()), "name": "アウトドア"},
        {"id": str(uuid.uuid4()), "name": "スポーツ"},
        {"id": str(uuid.uuid4()), "name": "文化"},
        {"id": str(uuid.uuid4()), "name": "ショッピング"}
    ]
    
    tag_ids = {}
    for tag in tags:
        tag_obj = TagMaster(
            id=tag["id"],
            tag_name=tag["name"],
            is_active=True,
            created_at=datetime.utcnow()
        )
        db.session.add(tag_obj)
        tag_ids[tag["name"]] = tag["id"]
    
    db.session.commit()
    print("✅ タグマスターを追加しました")
    
    # ユーザーデータを作成
    users = [
        {
            "id": str(uuid.uuid4()),
            "email": "test@example.com",
            "name": "テストユーザー",
            "password": "123",
            "birthdate": datetime(1990, 1, 1),
            "profile": "旅行が好きです。よろしくお願いします。"
        },
        {
            "id": str(uuid.uuid4()),
            "email": "tanaka@example.com",
            "name": "田中太郎",
            "password": "123",
            "birthdate": datetime(1985, 5, 15),
            "profile": "写真撮影が趣味です。一緒に素敵な景色を見に行きましょう。"
        },
        {
            "id": str(uuid.uuid4()),
            "email": "yamada@example.com",
            "name": "山田花子",
            "password": "123",
            "birthdate": datetime(1992, 10, 20),
            "profile": "食べ歩きが大好きです。おいしいお店探しましょう！"
        }
    ]
    
    user_ids = {}
    for user_data in users:
        user = User(
            id=user_data["id"],
            email_address=user_data["email"],
            user_name=user_data["name"],
            birthdate=user_data["birthdate"],
            profile_message=user_data["profile"],
            is_certificated=True
        )
        user.set_password(user_data["password"])
        db.session.add(user)
        
        user_ids[user_data["email"]] = user_data["id"]
        
        # 画像をアップロード
        filename = f"user_{user_data['id']}_profile.jpg"
        image_url = upload_image(MINIO_BUCKET, TEST_IMAGE_PATH, filename)
        if image_url:
            user.user_image_url = image_url
    
    db.session.commit()
    print("✅ ユーザーを追加しました")
    
    # イベント画像をアップロード
    event_images = []
    for i in range(3):
        image_id = str(uuid.uuid4())
        filename = f"event_{image_id}.jpg"
        image_url = upload_image(EVENT_BUCKET, TEST_IMAGE_PATH, filename)
        if image_url:
            # テスト用に最初のユーザーをアップロード者として設定
            uploader_id = user_ids["test@example.com"]
            image = ImageList(id=image_id, image_url=image_url, uploaded_by=uploader_id)
            db.session.add(image)
            event_images.append(image_id)
    
    db.session.commit()
    print("✅ イベント画像をアップロードしました")
    
    # イベントデータを作成
    events = [
        {
            "id": str(uuid.uuid4()),
            "title": "富士山登山ツアー",
            "description": "富士山登山に一緒に行きませんか？初心者歓迎です。",
            "image_id": event_images[0] if event_images else None,
            "author_id": user_ids["test@example.com"],
            "area_id": areas[0]["id"],  # 東京
            "limit": 5,
            "current": 1,
            "published_at": datetime.utcnow() - timedelta(days=2)
        },
        {
            "id": str(uuid.uuid4()),
            "title": "大阪たこ焼きパーティー",
            "description": "大阪でたこ焼きパーティーしませんか？地元の美味しいお店を案内します。",
            "image_id": event_images[1] if len(event_images) > 1 else None,
            "author_id": user_ids["yamada@example.com"],
            "area_id": areas[1]["id"],  # 大阪
            "limit": 8,
            "current": 2,
            "published_at": datetime.utcnow() - timedelta(days=1)
        },
        {
            "id": str(uuid.uuid4()),
            "title": "京都紅葉撮影会",
            "description": "京都の紅葉を撮影しに行きます。カメラ好きの方、ぜひ一緒に！",
            "image_id": event_images[2] if len(event_images) > 2 else None,
            "author_id": user_ids["tanaka@example.com"],
            "area_id": areas[2]["id"],  # 京都
            "limit": 6,
            "current": 1,
            "published_at": datetime.utcnow()
        }
    ]
    
    event_ids = []
    for event_data in events:
        event = Event(
            id=event_data["id"],
            title=event_data["title"],
            description=event_data["description"],
            image_id=event_data["image_id"],
            author_user_id=event_data["author_id"],
            area_id=event_data["area_id"],
            limit_persons=event_data["limit"],
            current_persons=event_data["current"],
            published_at=event_data["published_at"],
            timestamp=event_data["published_at"]
        )
        db.session.add(event)
        event_ids.append(event_data["id"])
        
        # 作成者をイベントメンバーに追加
        member = UserMemberGroup(user_id=event_data["author_id"], event_id=event_data["id"])
        db.session.add(member)
    
    db.session.commit()
    print("✅ イベントを追加しました")
    
    # イベントのタグを設定
    event_tags = [
        {"event_id": event_ids[0], "tags": ["自然", "アウトドア"]},
        {"event_id": event_ids[1], "tags": ["グルメ"]},
        {"event_id": event_ids[2], "tags": ["文化", "自然"]}
    ]
    
    for event_tag in event_tags:
        for tag_name in event_tag["tags"]:
            tag_association = EventTagAssociation(
                id=str(uuid.uuid4()),
                tag_id=tag_ids[tag_name],
                event_id=event_tag["event_id"],
                created_at=datetime.utcnow()
            )
            db.session.add(tag_association)
    
    db.session.commit()
    print("✅ イベントのタグを設定しました")
    
    # イベントのいいねを設定
    hearts = [
        {"user_id": user_ids["tanaka@example.com"], "event_id": event_ids[0]},
        {"user_id": user_ids["yamada@example.com"], "event_id": event_ids[0]},
        {"user_id": user_ids["test@example.com"], "event_id": event_ids[1]}
    ]
    
    for heart in hearts:
        heart_obj = UserHeartEvent(user_id=heart["user_id"], event_id=heart["event_id"])
        db.session.add(heart_obj)
    
    db.session.commit()
    print("✅ イベントのいいねを設定しました")
    
    # スレッド画像をアップロード
    thread_images = []
    for i in range(2):
        image_id = str(uuid.uuid4())
        filename = f"thread_{image_id}.jpg"
        image_url = upload_image(THREAD_BUCKET, TEST_IMAGE_PATH, filename)
        if image_url:
            # テスト用に最初のユーザーをアップロード者として設定
            uploader_id = user_ids["test@example.com"]
            image = ImageList(id=image_id, image_url=image_url, uploaded_by=uploader_id)
            db.session.add(image)
            thread_images.append(image_id)
    
    db.session.commit()
    print("✅ スレッド画像をアップロードしました")
    
    # スレッドを作成
    threads = [
        {
            "id": str(uuid.uuid4()),
            "title": "京都のおすすめ観光スポット",
            "message": "京都のおすすめ観光スポットを教えてください！",
            "image_id": thread_images[0] if thread_images else None,
            "area_id": areas[2]["id"],  # 京都
            "author_id": user_ids["test@example.com"],
            "published_at": datetime.utcnow() - timedelta(days=1)
        },
        {
            "id": str(uuid.uuid4()),
            "title": "北海道旅行のアドバイス",
            "message": "北海道旅行で絶対に行くべき場所は？",
            "image_id": thread_images[1] if len(thread_images) > 1 else None,
            "area_id": areas[4]["id"],  # 北海道
            "author_id": user_ids["yamada@example.com"],
            "published_at": datetime.utcnow()
        }
    ]
    
    thread_ids = []
    for thread_data in threads:
        thread = Thread(
            id=thread_data["id"],
            title=thread_data["title"],
            message=thread_data["message"],
            image_id=thread_data["image_id"],
            area_id=thread_data["area_id"],
            author_id=thread_data["author_id"],
            published_at=thread_data["published_at"]
        )
        db.session.add(thread)
        thread_ids.append(thread_data["id"])
    
    db.session.commit()
    print("✅ スレッドを追加しました")

    # スレッドタグを設定
    thread_tags = [
        {"thread_id": thread_ids[0], "tags": ["文化", "自然"]},
        {"thread_id": thread_ids[1], "tags": ["自然", "アウトドア"]}
    ]
    
    for thread_tag in thread_tags:
        for tag_name in thread_tag["tags"]:
            tag_association = ThreadTagAssociation(
                id=str(uuid.uuid4()),
                tag_id=tag_ids[tag_name],
                thread_id=thread_tag["thread_id"],
                created_at=datetime.utcnow()
            )
            db.session.add(tag_association)
    
    db.session.commit()
    print("✅ スレッドのタグを設定しました")
    
    # スレッドのいいねを設定
    thread_hearts = [
        {"user_id": user_ids["tanaka@example.com"], "thread_id": thread_ids[0]},
        {"user_id": user_ids["test@example.com"], "thread_id": thread_ids[1]}
    ]
    
    for heart in thread_hearts:
        heart_obj = UserHeartThread(user_id=heart["user_id"], thread_id=heart["thread_id"])
        db.session.add(heart_obj)
    
    db.session.commit()
    print("✅ スレッドのいいねを設定しました")
    
    # スレッドメッセージを作成
    thread_messages = [
        {
            "id": str(uuid.uuid4()),
            "thread_id": thread_ids[0],
            "sender_user_id": user_ids["test@example.com"],
            "content": "京都のおすすめ観光スポットを教えてください！",
            "timestamp": datetime.utcnow() - timedelta(days=1),
            "message_type": "text"
        },
        {
            "id": str(uuid.uuid4()),
            "thread_id": thread_ids[0],
            "sender_user_id": user_ids["tanaka@example.com"],
            "content": "清水寺は必見です！夕方の景色が特に美しいです。",
            "timestamp": datetime.utcnow() - timedelta(hours=12),
            "message_type": "text"
        },
        {
            "id": str(uuid.uuid4()),
            "thread_id": thread_ids[1],
            "sender_user_id": user_ids["yamada@example.com"],
            "content": "北海道旅行で絶対に行くべき場所は？",
            "timestamp": datetime.utcnow(),
            "message_type": "text"
        }
    ]
    
    for message_data in thread_messages:
        thread_message = ThreadMessage(
            id=message_data["id"],
            thread_id=message_data["thread_id"],
            sender_user_id=message_data["sender_user_id"],
            content=message_data["content"],
            timestamp=message_data["timestamp"],
            message_type=message_data["message_type"]
        )
        db.session.add(thread_message)
    
    db.session.commit()
    print("✅ スレッドメッセージを追加しました")
    
    # イベントメッセージを作成
    event_messages = [
        {
            "id": str(uuid.uuid4()),
            "event_id": event_ids[0],
            "sender_user_id": user_ids["test@example.com"],
            "content": "富士山登山の集合場所は新宿駅南口です。8時に集合しましょう！",
            "timestamp": datetime.utcnow() - timedelta(hours=12),
            "message_type": "text"
        },
        {
            "id": str(uuid.uuid4()),
            "event_id": event_ids[1],
            "sender_user_id": user_ids["yamada@example.com"],
            "content": "たこ焼きパーティーは大阪駅前のたこ焼き屋「たこ金」で行います。",
            "timestamp": datetime.utcnow() - timedelta(hours=6),
            "message_type": "text"
        }
    ]
    
    for message_data in event_messages:
        event_message = EventMessage(
            id=message_data["id"],
            event_id=message_data["event_id"],
            sender_user_id=message_data["sender_user_id"],
            content=message_data["content"],
            timestamp=message_data["timestamp"],
            message_type=message_data["message_type"]
        )
        db.session.add(event_message)
    
    db.session.commit()
    print("✅ イベントメッセージを追加しました")
    
    print("\n✨ シードデータの投入が完了しました！")
    print("\n🔹 ログイン可能なユーザー:")
    for user_data in users:
        print(f"  📧 メールアドレス: {user_data['email']}  🔑 パスワード: {user_data['password']}")
