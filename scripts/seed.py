import sys, os
import uuid
from datetime import datetime, timedelta, timezone
from sqlalchemy import text
import json

JST = timezone(timedelta(hours=9))

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.models import db
from app.models.user import User
from app.models.event import Event, UserMemberGroup, UserHeartEvent, TagMaster, UserTagAssociation, EventTagAssociation, ThreadTagAssociation
from app.models.area import AreaList
from app.models.file import ImageList
from app.models.thread import Thread, ThreadMessage, UserHeartThread
from app.models.message import EventMessage, FriendRelationship
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
TEST_IMAGE_PATH = os.path.join(os.path.dirname(__file__), "users", "test.png")

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
            # 既存のバケットも公開設定に更新
            s3.put_bucket_policy(
                Bucket=bucket, 
                Policy=json.dumps({
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Effect": "Allow",
                            "Principal": {"AWS": "*"},
                            "Action": ["s3:GetObject"],
                            "Resource": [f"arn:aws:s3:::{bucket}/*"]
                        }
                    ]
                })
            )
            print(f"🔓 バケット '{bucket}' を公開アクセス可能に設定しました")
        except ClientError:
            print(f"📦 バケット '{bucket}' を作成します")
            s3.create_bucket(Bucket=bucket)
            # 新規バケットを公開設定に
            s3.put_bucket_policy(
                Bucket=bucket, 
                Policy=json.dumps({
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Effect": "Allow",
                            "Principal": {"AWS": "*"},
                            "Action": ["s3:GetObject"],
                            "Resource": [f"arn:aws:s3:::{bucket}/*"]
                        }
                    ]
                })
            )
            print(f"🔓 バケット '{bucket}' を公開アクセス可能に設定しました")

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
            created_at=datetime.now(JST)
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
            "profile": "旅行が好きです。よろしくお願いします。",
            "image_path": TEST_IMAGE_PATH
        },
        {
            "id": str(uuid.uuid4()),
            "email": "tanaka@example.com",
            "name": "田中太郎",
            "password": "123",
            "birthdate": datetime(1985, 5, 15),
            "profile": "写真撮影が趣味です。一緒に素敵な景色を見に行きましょう。",
            "image_path": TEST_IMAGE_PATH
        },
        {
            "id": str(uuid.uuid4()),
            "email": "yamada@example.com",
            "name": "山田花子",
            "password": "123",
            "birthdate": datetime(1992, 10, 20),
            "profile": "食べ歩きが大好きです。おいしいお店探しましょう！",
            "image_path": TEST_IMAGE_PATH
        },
        # 動物画像を使ったユーザーを追加
        {
            "id": str(uuid.uuid4()),
            "email": "uma@example.com",
            "name": "馬太郎",
            "password": "123",
            "birthdate": datetime(1988, 3, 15),
            "profile": "乗馬が趣味です。自然の中で過ごすのが好きです。",
            "image_path": os.path.join(os.path.dirname(__file__), "users", "ウマ.png")
        },
        {
            "id": str(uuid.uuid4()),
            "email": "okojo@example.com",
            "name": "オコジョ健太",
            "password": "123",
            "birthdate": datetime(1995, 7, 25),
            "profile": "山登りが得意です。高山でも元気に動き回ります！",
            "image_path": os.path.join(os.path.dirname(__file__), "users", "オコジョ.png")
        },
        {
            "id": str(uuid.uuid4()),
            "email": "tonakai@example.com",
            "name": "トナカイ花子",
            "password": "123",
            "birthdate": datetime(1993, 12, 24),
            "profile": "寒い地域が大好きです。クリスマスシーズンが特に忙しいです。",
            "image_path": os.path.join(os.path.dirname(__file__), "users", "トナカイ.png")
        },
        {
            "id": str(uuid.uuid4()),
            "email": "niwatori@example.com",
            "name": "鶏次郎",
            "password": "123",
            "birthdate": datetime(1991, 4, 1),
            "profile": "早起きが得意です。朝の散歩ツアーを企画しています。",
            "image_path": os.path.join(os.path.dirname(__file__), "users", "ニワトリ.png")
        },
        {
            "id": str(uuid.uuid4()),
            "email": "hyrax@example.com",
            "name": "ハイラックス夏子",
            "password": "123",
            "birthdate": datetime(1989, 8, 10),
            "profile": "岩場での休憩が趣味です。日向ぼっこが大好き。",
            "image_path": os.path.join(os.path.dirname(__file__), "users", "ハイラックス.png")
        },
        {
            "id": str(uuid.uuid4()),
            "email": "hamster@example.com",
            "name": "ハムスター翔",
            "password": "123",
            "birthdate": datetime(1996, 2, 14),
            "profile": "小さな隠れ家が大好きです。種集めが趣味です。",
            "image_path": os.path.join(os.path.dirname(__file__), "users", "ハムスター.png")
        },
        {
            "id": str(uuid.uuid4()),
            "email": "rakuda@example.com",
            "name": "ラクダ正太",
            "password": "123",
            "birthdate": datetime(1987, 6, 30),
            "profile": "砂漠ツアーガイドをしています。暑さに強いです。",
            "image_path": os.path.join(os.path.dirname(__file__), "users", "ラクダ.png")
        },
        {
            "id": str(uuid.uuid4()),
            "email": "sheep@example.com",
            "name": "黒羊めぐみ",
            "password": "123",
            "birthdate": datetime(1994, 9, 5),
            "profile": "モフモフした毛が自慢です。編み物ワークショップを開催しています。",
            "image_path": os.path.join(os.path.dirname(__file__), "users", "黒い羊.png")
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
        filename = f"user_{user_data['id']}_profile.png"
        image_url = upload_image(MINIO_BUCKET, user_data["image_path"], filename)
        if image_url:
            user.user_image_url = image_url
    
    db.session.commit()
    print("✅ ユーザーを追加しました")
    
    # イベント画像をアップロード
    event_images = {}
    
    # いちご狩りの画像をアップロード
    ichigo_image_id = str(uuid.uuid4())
    ichigo_filename = f"event_{ichigo_image_id}.png"
    ichigo_image_path = os.path.join(os.path.dirname(__file__), "events", "いちご狩り.png")
    ichigo_image_url = upload_image(EVENT_BUCKET, ichigo_image_path, ichigo_filename)
    if ichigo_image_url:
        uploader_id = user_ids["test@example.com"]
        image = ImageList(id=ichigo_image_id, image_url=ichigo_image_url, uploaded_by=uploader_id)
        db.session.add(image)
        event_images["いちご狩り"] = {
            "id": ichigo_image_id,
            "url": ichigo_image_url
        }
    
    # たこ焼きパーティーの画像をアップロード
    takoyaki_image_id = str(uuid.uuid4())
    takoyaki_filename = f"event_{takoyaki_image_id}.webp"
    takoyaki_image_path = os.path.join(os.path.dirname(__file__), "events", "たこ焼き.webp")
    takoyaki_image_url = upload_image(EVENT_BUCKET, takoyaki_image_path, takoyaki_filename)
    if takoyaki_image_url:
        uploader_id = user_ids["yamada@example.com"]
        image = ImageList(id=takoyaki_image_id, image_url=takoyaki_image_url, uploaded_by=uploader_id)
        db.session.add(image)
        event_images["たこ焼き"] = {
            "id": takoyaki_image_id,
            "url": takoyaki_image_url
        }
    
    # 紅葉撮影会の画像をアップロード
    koyo_image_id = str(uuid.uuid4())
    koyo_filename = f"event_{koyo_image_id}.webp"
    koyo_image_path = os.path.join(os.path.dirname(__file__), "events", "紅葉撮影会.webp")
    koyo_image_url = upload_image(EVENT_BUCKET, koyo_image_path, koyo_filename)
    if koyo_image_url:
        uploader_id = user_ids["tanaka@example.com"]
        image = ImageList(id=koyo_image_id, image_url=koyo_image_url, uploaded_by=uploader_id)
        db.session.add(image)
        event_images["紅葉"] = {
            "id": koyo_image_id,
            "url": koyo_image_url
        }
    
    # 東京スカイツリーの画像をアップロード
    skytree_image_id = str(uuid.uuid4())
    skytree_filename = f"event_{skytree_image_id}.jpg"
    skytree_image_path = os.path.join(os.path.dirname(__file__), "events", "東京スカイツリー.jpg")
    skytree_image_url = upload_image(EVENT_BUCKET, skytree_image_path, skytree_filename)
    if skytree_image_url:
        uploader_id = user_ids["test@example.com"]
        image = ImageList(id=skytree_image_id, image_url=skytree_image_url, uploaded_by=uploader_id)
        db.session.add(image)
        event_images["東京スカイツリー"] = {
            "id": skytree_image_id,
            "url": skytree_image_url
        }
    
    # 乗馬体験の画像をアップロード
    horse_image_id = str(uuid.uuid4())
    horse_filename = f"event_{horse_image_id}.jpg"
    horse_image_path = os.path.join(os.path.dirname(__file__), "events", "乗馬体験.jpg")
    horse_image_url = upload_image(EVENT_BUCKET, horse_image_path, horse_filename)
    if horse_image_url:
        uploader_id = user_ids["uma@example.com"]
        image = ImageList(id=horse_image_id, image_url=horse_image_url, uploaded_by=uploader_id)
        db.session.add(image)
        event_images["乗馬体験"] = {
            "id": horse_image_id,
            "url": horse_image_url
        }
    
    # 山岳トレッキングの画像をアップロード
    trekking_image_id = str(uuid.uuid4())
    trekking_filename = f"event_{trekking_image_id}.jpg"
    trekking_image_path = os.path.join(os.path.dirname(__file__), "events", "山岳トレッキング.jpg")
    trekking_image_url = upload_image(EVENT_BUCKET, trekking_image_path, trekking_filename)
    if trekking_image_url:
        uploader_id = user_ids["okojo@example.com"]
        image = ImageList(id=trekking_image_id, image_url=trekking_image_url, uploaded_by=uploader_id)
        db.session.add(image)
        event_images["山岳トレッキング"] = {
            "id": trekking_image_id,
            "url": trekking_image_url
        }
    
    # 早朝サンライズヨガの画像をアップロード
    yoga_image_id = str(uuid.uuid4())
    yoga_filename = f"event_{yoga_image_id}.jpg"
    yoga_image_path = os.path.join(os.path.dirname(__file__), "events", "早朝サンライズヨガ.jpg")
    yoga_image_url = upload_image(EVENT_BUCKET, yoga_image_path, yoga_filename)
    if yoga_image_url:
        uploader_id = user_ids["niwatori@example.com"]
        image = ImageList(id=yoga_image_id, image_url=yoga_image_url, uploaded_by=uploader_id)
        db.session.add(image)
        event_images["早朝サンライズヨガ"] = {
            "id": yoga_image_id,
            "url": yoga_image_url
        }
    
    # 種集めウォーキングの画像をアップロード
    seedwalk_image_id = str(uuid.uuid4())
    seedwalk_filename = f"event_{seedwalk_image_id}.jpg"
    seedwalk_image_path = os.path.join(os.path.dirname(__file__), "events", "種集めウォーキング.jpg")
    seedwalk_image_url = upload_image(EVENT_BUCKET, seedwalk_image_path, seedwalk_filename)
    if seedwalk_image_url:
        uploader_id = user_ids["hamster@example.com"]
        image = ImageList(id=seedwalk_image_id, image_url=seedwalk_image_url, uploaded_by=uploader_id)
        db.session.add(image)
        event_images["種集めウォーキング"] = {
            "id": seedwalk_image_id,
            "url": seedwalk_image_url
        }
    
    # 砂漠ツアーガイドの画像をアップロード
    desert_image_id = str(uuid.uuid4())
    desert_filename = f"event_{desert_image_id}.jpg"
    desert_image_path = os.path.join(os.path.dirname(__file__), "events", "砂漠ツアーガイド.jpg")
    desert_image_url = upload_image(EVENT_BUCKET, desert_image_path, desert_filename)
    if desert_image_url:
        uploader_id = user_ids["rakuda@example.com"]
        image = ImageList(id=desert_image_id, image_url=desert_image_url, uploaded_by=uploader_id)
        db.session.add(image)
        event_images["砂漠ツアーガイド"] = {
            "id": desert_image_id,
            "url": desert_image_url
        }
    
    # 編み物ワークショップの画像をアップロード
    knitting_image_id = str(uuid.uuid4())
    knitting_filename = f"event_{knitting_image_id}.jpg"
    knitting_image_path = os.path.join(os.path.dirname(__file__), "events", "編み物ワークショップ.jpg")
    knitting_image_url = upload_image(EVENT_BUCKET, knitting_image_path, knitting_filename)
    if knitting_image_url:
        uploader_id = user_ids["sheep@example.com"]
        image = ImageList(id=knitting_image_id, image_url=knitting_image_url, uploaded_by=uploader_id)
        db.session.add(image)
        event_images["編み物ワークショップ"] = {
            "id": knitting_image_id,
            "url": knitting_image_url
        }
    
    # 寿司作り体験の画像をアップロード
    sushi_image_id = str(uuid.uuid4())
    sushi_filename = f"event_{sushi_image_id}.jpg"
    sushi_image_path = os.path.join(os.path.dirname(__file__), "events", "寿司作り体験.jpg")
    sushi_image_url = upload_image(EVENT_BUCKET, sushi_image_path, sushi_filename)
    if sushi_image_url:
        uploader_id = user_ids["yamada@example.com"]
        image = ImageList(id=sushi_image_id, image_url=sushi_image_url, uploaded_by=uploader_id)
        db.session.add(image)
        event_images["寿司作り体験"] = {
            "id": sushi_image_id,
            "url": sushi_image_url
        }
    
    # 鎌倉散策の画像をアップロード
    kamakura_image_id = str(uuid.uuid4())
    kamakura_filename = f"event_{kamakura_image_id}.jpg"
    kamakura_image_path = os.path.join(os.path.dirname(__file__), "events", "鎌倉散策.jpg")
    kamakura_image_url = upload_image(EVENT_BUCKET, kamakura_image_path, kamakura_filename)
    if kamakura_image_url:
        uploader_id = user_ids["tanaka@example.com"]
        image = ImageList(id=kamakura_image_id, image_url=kamakura_image_url, uploaded_by=uploader_id)
        db.session.add(image)
        event_images["鎌倉散策"] = {
            "id": kamakura_image_id,
            "url": kamakura_image_url
        }
    
    # クリスマスマーケットの画像をアップロード
    xmas_image_id = str(uuid.uuid4())
    xmas_filename = f"event_{xmas_image_id}.jpg"
    xmas_image_path = os.path.join(os.path.dirname(__file__), "events", "クリスマスマーケット.jpg")
    xmas_image_url = upload_image(EVENT_BUCKET, xmas_image_path, xmas_filename)
    if xmas_image_url:
        uploader_id = user_ids["tonakai@example.com"]
        image = ImageList(id=xmas_image_id, image_url=xmas_image_url, uploaded_by=uploader_id)
        db.session.add(image)
        event_images["クリスマスマーケット"] = {
            "id": xmas_image_id,
            "url": xmas_image_url
        }
    
    # 岩場でのんびりピクニックの画像をアップロード
    picnic_image_id = str(uuid.uuid4())
    picnic_filename = f"event_{picnic_image_id}.jpg"
    picnic_image_path = os.path.join(os.path.dirname(__file__), "events", "岩場でのんびりピクニック.jpg")
    picnic_image_url = upload_image(EVENT_BUCKET, picnic_image_path, picnic_filename)
    if picnic_image_url:
        uploader_id = user_ids["hyrax@example.com"]
        image = ImageList(id=picnic_image_id, image_url=picnic_image_url, uploaded_by=uploader_id)
        db.session.add(image)
        event_images["岩場でのんびりピクニック"] = {
            "id": picnic_image_id,
            "url": picnic_image_url
        }
    
    db.session.commit()
    print("✅ イベント画像をアップロードしました")
    
    # イベントデータを作成
    events = [
        # テストユーザーのイベント
        {
            "id": str(uuid.uuid4()),
            "title": "いちご狩りツアー",
            "description": "美味しいいちごを一緒に摘みに行きませんか？初心者歓迎です。",
            "image_id": event_images["いちご狩り"]["id"] if "いちご狩り" in event_images else None,
            "author_id": user_ids["test@example.com"],
            "area_id": areas[0]["id"],  # 東京
            "limit": 10,
            "current": 1,
            "published_at": datetime.now(JST) - timedelta(days=2),
            "tags": ["自然", "アウトドア"]
        },
        {
            "id": str(uuid.uuid4()),
            "title": "東京スカイツリー観光",
            "description": "東京スカイツリーを一緒に観光しませんか？東京の景色を楽しみましょう。",
            "image_id": event_images["東京スカイツリー"]["id"] if "東京スカイツリー" in event_images else None,
            "author_id": user_ids["test@example.com"],
            "area_id": areas[0]["id"],  # 東京
            "limit": 8,
            "current": 1,
            "published_at": datetime.now(JST) - timedelta(days=1),
            "tags": ["文化", "観光"]
        },
        
        # 田中さんのイベント
        {
            "id": str(uuid.uuid4()),
            "title": "京都紅葉撮影会",
            "description": "京都の紅葉を撮影しに行きます。カメラ好きの方、ぜひ一緒に！",
            "image_id": event_images["紅葉"]["id"] if "紅葉" in event_images else None,
            "author_id": user_ids["tanaka@example.com"],
            "area_id": areas[2]["id"],  # 京都
            "limit": 6,
            "current": 1,
            "published_at": datetime.now(JST),
            "tags": ["文化", "自然"]
        },
        {
            "id": str(uuid.uuid4()),
            "title": "鎌倉散策ツアー",
            "description": "鎌倉の歴史的な寺社を巡りながら散策します。写真撮影にもおすすめです。",
            "image_id": event_images["鎌倉散策"]["id"] if "鎌倉散策" in event_images else None,
            "author_id": user_ids["tanaka@example.com"],
            "area_id": areas[0]["id"],  # 東京（近郊）
            "limit": 8,
            "current": 1,
            "published_at": datetime.now(JST) - timedelta(days=3),
            "tags": ["文化", "歴史"]
        },
        
        # 山田さんのイベント
        {
            "id": str(uuid.uuid4()),
            "title": "大阪たこ焼きパーティー",
            "description": "大阪でたこ焼きパーティーしませんか？地元の美味しいお店を案内します。",
            "image_id": event_images["たこ焼き"]["id"] if "たこ焼き" in event_images else None,
            "author_id": user_ids["yamada@example.com"],
            "area_id": areas[1]["id"],  # 大阪
            "limit": 8,
            "current": 1,
            "published_at": datetime.now(JST) - timedelta(days=1),
            "tags": ["グルメ"]
        },
        {
            "id": str(uuid.uuid4()),
            "title": "寿司作り体験教室",
            "description": "自分で寿司を作ってみませんか？初心者向けの体験教室です。",
            "image_id": event_images["寿司作り体験"]["id"] if "寿司作り体験" in event_images else None,
            "author_id": user_ids["yamada@example.com"],
            "area_id": areas[0]["id"],  # 東京
            "limit": 6,
            "current": 1,
            "published_at": datetime.now(JST) - timedelta(days=4),
            "tags": ["グルメ", "文化"]
        },
        
        # 動物ユーザーのイベント
        {
            "id": str(uuid.uuid4()),
            "title": "乗馬体験ツアー",
            "description": "初心者でも安心して楽しめる乗馬体験です。大自然の中で馬と触れ合いましょう。",
            "image_id": event_images["乗馬体験"]["id"] if "乗馬体験" in event_images else None,
            "author_id": user_ids["uma@example.com"],
            "area_id": areas[4]["id"],  # 北海道
            "limit": 5,
            "current": 1,
            "published_at": datetime.now(JST) - timedelta(days=5),
            "tags": ["アウトドア", "スポーツ"]
        },
        {
            "id": str(uuid.uuid4()),
            "title": "山岳トレッキング",
            "description": "高山を一緒に登りませんか？美しい景色と爽快な空気を楽しめます。",
            "image_id": event_images["山岳トレッキング"]["id"] if "山岳トレッキング" in event_images else None,
            "author_id": user_ids["okojo@example.com"],
            "area_id": areas[4]["id"],  # 北海道
            "limit": 6,
            "current": 1,
            "published_at": datetime.now(JST) - timedelta(days=2),
            "tags": ["アウトドア", "スポーツ", "自然"]
        },
        {
            "id": str(uuid.uuid4()),
            "title": "クリスマスマーケット訪問",
            "description": "冬の季節限定！クリスマスマーケットを一緒に楽しみましょう。",
            "image_id": event_images["クリスマスマーケット"]["id"] if "クリスマスマーケット" in event_images else None,
            "author_id": user_ids["tonakai@example.com"],
            "area_id": areas[4]["id"],  # 北海道
            "limit": 10,
            "current": 1,
            "published_at": datetime.now(JST) - timedelta(days=1),
            "tags": ["文化", "ショッピング"]
        },
        {
            "id": str(uuid.uuid4()),
            "title": "早朝サンライズヨガ",
            "description": "早朝の爽やかな空気の中でヨガを楽しみましょう。初心者歓迎です。",
            "image_id": event_images["早朝サンライズヨガ"]["id"] if "早朝サンライズヨガ" in event_images else None,
            "author_id": user_ids["niwatori@example.com"],
            "area_id": areas[0]["id"],  # 東京
            "limit": 8,
            "current": 1,
            "published_at": datetime.now(JST) - timedelta(days=3),
            "tags": ["スポーツ", "自然"]
        },
        {
            "id": str(uuid.uuid4()),
            "title": "岩場でのんびりピクニック",
            "description": "自然の岩場でピクニックを楽しみます。のんびり日向ぼっこもできます。",
            "image_id": event_images["岩場でのんびりピクニック"]["id"] if "岩場でのんびりピクニック" in event_images else None,
            "author_id": user_ids["hyrax@example.com"],
            "area_id": areas[3]["id"],  # 沖縄
            "limit": 5,
            "current": 1,
            "published_at": datetime.now(JST) - timedelta(days=2),
            "tags": ["自然", "アウトドア"]
        },
        {
            "id": str(uuid.uuid4()),
            "title": "種集めウォーキング",
            "description": "自然の中で様々な植物の種を集めるウォーキングイベントです。",
            "image_id": event_images["種集めウォーキング"]["id"] if "種集めウォーキング" in event_images else None,
            "author_id": user_ids["hamster@example.com"],
            "area_id": areas[0]["id"],  # 東京
            "limit": 6,
            "current": 1,
            "published_at": datetime.now(JST) - timedelta(days=5),
            "tags": ["自然", "アウトドア"]
        },
        {
            "id": str(uuid.uuid4()),
            "title": "砂漠ツアーガイド",
            "description": "砂漠の魅力を体験するガイドツアーです。ラクダに乗る体験も含まれます。",
            "image_id": event_images["砂漠ツアーガイド"]["id"] if "砂漠ツアーガイド" in event_images else None,
            "author_id": user_ids["rakuda@example.com"],
            "area_id": areas[3]["id"],  # 沖縄（砂浜を砂漠に見立てて）
            "limit": 7,
            "current": 1,
            "published_at": datetime.now(JST) - timedelta(days=4),
            "tags": ["アウトドア", "文化"]
        },
        {
            "id": str(uuid.uuid4()),
            "title": "編み物ワークショップ",
            "description": "暖かな毛糸で編み物を楽しむワークショップです。初心者も大歓迎！",
            "image_id": event_images["編み物ワークショップ"]["id"] if "編み物ワークショップ" in event_images else None,
            "author_id": user_ids["sheep@example.com"],
            "area_id": areas[4]["id"],  # 北海道
            "limit": 10,
            "current": 1,
            "published_at": datetime.now(JST) - timedelta(days=3),
            "tags": ["文化", "ショッピング"]
        }
    ]
    
    event_ids = []
    for event_data in events:
        tags = event_data.pop("tags", [])  # tagsキーを取り出して削除
        
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
            timestamp=event_data["published_at"],
            status='pending'
        )
        db.session.add(event)
        event_ids.append(event_data["id"])
        
        # 作成者をイベントメンバーに追加
        member = UserMemberGroup(
            user_id=event_data["author_id"], 
            event_id=event_data["id"],
            joined_at=datetime.now(JST) - timedelta(days=1)
        )
        db.session.add(member)
        
        # イベントとタグの関連付け
        for tag_name in tags:
            if tag_name in tag_ids:
                tag_association = EventTagAssociation(
                    id=str(uuid.uuid4()),
                    tag_id=tag_ids[tag_name],
                    event_id=event_data["id"],
                    created_at=datetime.now(JST)
                )
                db.session.add(tag_association)
    
    db.session.commit()
    print("✅ イベントを追加しました")

    # 参加メンバーを追加
    # イベント1に動物ユーザーを何人か参加させる
    event1_members = [
        "uma@example.com", 
        "okojo@example.com", 
        "tonakai@example.com", 
        "niwatori@example.com"
    ]
    for i, email in enumerate(event1_members):
        member = UserMemberGroup(
            user_id=user_ids[email], 
            event_id=event_ids[0],
            joined_at=datetime.now(JST) - timedelta(days=1, hours=i)
        )
        db.session.add(member)
        
        # システムメッセージを追加
        user_name = next((u["name"] for u in users if u["email"] == email), "ユーザー")
        system_message = EventMessage(
            id=str(uuid.uuid4()),
            event_id=event_ids[0],
            sender_user_id=None,  # システムメッセージ
            content=f"{user_name}さんがイベントに参加しました",
            timestamp=datetime.now(JST) - timedelta(days=1, hours=i),
            message_type='system'
        )
        db.session.add(system_message)
    
    # イベント2に別の動物ユーザーを参加させる
    event2_members = ["hyrax@example.com", "hamster@example.com", "sheep@example.com"]
    for i, email in enumerate(event2_members):
        member = UserMemberGroup(
            user_id=user_ids[email], 
            event_id=event_ids[1],
            joined_at=datetime.now(JST) - timedelta(hours=i+2)
        )
        db.session.add(member)
        
        # システムメッセージを追加
        user_name = next((u["name"] for u in users if u["email"] == email), "ユーザー")
        system_message = EventMessage(
            id=str(uuid.uuid4()),
            event_id=event_ids[1],
            sender_user_id=None,  # システムメッセージ
            content=f"{user_name}さんがイベントに参加しました",
            timestamp=datetime.now(JST) - timedelta(hours=i+2),
            message_type='system'
        )
        db.session.add(system_message)
    
    # イベント3に残りの動物ユーザーを参加させる
    event3_members = ["rakuda@example.com", "hamster@example.com"]
    for i, email in enumerate(event3_members):
        member = UserMemberGroup(
            user_id=user_ids[email], 
            event_id=event_ids[2],
            joined_at=datetime.now(JST) - timedelta(hours=i+1)
        )
        db.session.add(member)
        
        # システムメッセージを追加
        user_name = next((u["name"] for u in users if u["email"] == email), "ユーザー")
        system_message = EventMessage(
            id=str(uuid.uuid4()),
            event_id=event_ids[2],
            sender_user_id=None,  # システムメッセージ
            content=f"{user_name}さんがイベントに参加しました",
            timestamp=datetime.now(JST) - timedelta(hours=i+1),
            message_type='system'
        )
        db.session.add(system_message)
    
    # イベントの参加者数を更新
    for i, event_id in enumerate(event_ids):
        event = Event.query.get(event_id)
        if i == 0:  # 最初のイベント
            event.current_persons = 1 + len(event1_members)
        elif i == 1:  # 2番目のイベント
            event.current_persons = 1 + len(event2_members)
        elif i == 2:  # 3番目のイベント
            event.current_persons = 1 + len(event3_members)
    
    db.session.commit()
    print("✅ イベント参加メンバーを追加しました")
    
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
            "published_at": datetime.now(JST) - timedelta(days=1)
        },
        {
            "id": str(uuid.uuid4()),
            "title": "北海道旅行のアドバイス",
            "message": "北海道旅行で絶対に行くべき場所は？",
            "image_id": thread_images[1] if len(thread_images) > 1 else None,
            "area_id": areas[4]["id"],  # 北海道
            "author_id": user_ids["yamada@example.com"],
            "published_at": datetime.now(JST)
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
                created_at=datetime.now(JST)
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
            "timestamp": datetime.now(JST) - timedelta(days=1),
            "message_type": "text"
        },
        {
            "id": str(uuid.uuid4()),
            "thread_id": thread_ids[0],
            "sender_user_id": user_ids["tanaka@example.com"],
            "content": "清水寺は必見です！夕方の景色が特に美しいです。",
            "timestamp": datetime.now(JST) - timedelta(hours=12),
            "message_type": "text"
        },
        {
            "id": str(uuid.uuid4()),
            "thread_id": thread_ids[1],
            "sender_user_id": user_ids["yamada@example.com"],
            "content": "北海道旅行で絶対に行くべき場所は？",
            "timestamp": datetime.now(JST),
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
            "content": "いちご狩りの集合場所は東京駅南口です。10時に集合しましょう！",
            "timestamp": datetime.now(JST) - timedelta(hours=12),
            "message_type": "text"
        },
        {
            "id": str(uuid.uuid4()),
            "event_id": event_ids[1],
            "sender_user_id": user_ids["yamada@example.com"],
            "content": "たこ焼きパーティーは大阪駅前のたこ焼き屋「たこ金」で行います。",
            "timestamp": datetime.now(JST) - timedelta(hours=6),
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
    
    # フレンド関係（フォロー/フォロワー）を作成
    # 一部のユーザー間でフォロー関係を設定
    friend_relationships = [
        # test@example.comユーザーの関係
        {"user_id": user_ids["test@example.com"], "friend_id": user_ids["tanaka@example.com"], "status": "accepted"},
        {"user_id": user_ids["test@example.com"], "friend_id": user_ids["yamada@example.com"], "status": "accepted"},
        {"user_id": user_ids["test@example.com"], "friend_id": user_ids["uma@example.com"], "status": "pending"},
        
        # tanaka@example.comユーザーの関係
        {"user_id": user_ids["tanaka@example.com"], "friend_id": user_ids["test@example.com"], "status": "accepted"},
        {"user_id": user_ids["tanaka@example.com"], "friend_id": user_ids["okojo@example.com"], "status": "accepted"},
        {"user_id": user_ids["tanaka@example.com"], "friend_id": user_ids["tonakai@example.com"], "status": "accepted"},
        
        # yamada@example.comユーザーの関係
        {"user_id": user_ids["yamada@example.com"], "friend_id": user_ids["test@example.com"], "status": "accepted"},
        {"user_id": user_ids["yamada@example.com"], "friend_id": user_ids["tanaka@example.com"], "status": "pending"},
        {"user_id": user_ids["yamada@example.com"], "friend_id": user_ids["niwatori@example.com"], "status": "accepted"},
        
        # 動物ユーザー同士の関係
        {"user_id": user_ids["uma@example.com"], "friend_id": user_ids["okojo@example.com"], "status": "accepted"},
        {"user_id": user_ids["okojo@example.com"], "friend_id": user_ids["uma@example.com"], "status": "accepted"},
        {"user_id": user_ids["tonakai@example.com"], "friend_id": user_ids["niwatori@example.com"], "status": "accepted"},
        {"user_id": user_ids["niwatori@example.com"], "friend_id": user_ids["tonakai@example.com"], "status": "accepted"},
        {"user_id": user_ids["hyrax@example.com"], "friend_id": user_ids["hamster@example.com"], "status": "accepted"},
        {"user_id": user_ids["hamster@example.com"], "friend_id": user_ids["hyrax@example.com"], "status": "accepted"},
        {"user_id": user_ids["rakuda@example.com"], "friend_id": user_ids["sheep@example.com"], "status": "accepted"},
        {"user_id": user_ids["sheep@example.com"], "friend_id": user_ids["rakuda@example.com"], "status": "accepted"}
    ]
    
    for relationship in friend_relationships:
        friend_rel = FriendRelationship(
            id=str(uuid.uuid4()),
            user_id=relationship["user_id"],
            friend_id=relationship["friend_id"],
            status=relationship["status"],
            created_at=datetime.now(JST),
            updated_at=datetime.now(JST)
        )
        db.session.add(friend_rel)
    
    db.session.commit()
    print("✅ ユーザーのフォロー関係を追加しました")
    
    print("\n✨ シードデータの投入が完了しました！")
    print("\n🔹 ログイン可能なユーザー:")
    for user_data in users:
        print(f"  📧 メールアドレス: {user_data['email']}  🔑 パスワード: {user_data['password']}")
