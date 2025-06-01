import sys, os
import uuid
from datetime import datetime, timedelta, timezone
from sqlalchemy import text
import json
import random

JST = timezone(timedelta(hours=9))

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.models import db
from app.models.user import User
from app.models.event import Event, UserMemberGroup, UserHeartEvent, TagMaster, UserTagAssociation, EventTagAssociation, ThreadTagAssociation
from app.models.area import AreaList
from app.models.file import ImageList
from app.models.thread import Thread, ThreadMessage, UserHeartThread
from app.models.message import EventMessage, FriendRelationship, DirectMessage
from app.models.character import Character
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
CHARACTER_BUCKET = "character-images"  # キャラクター画像用バケット
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
    for bucket in [MINIO_BUCKET, EVENT_BUCKET, THREAD_BUCKET, CHARACTER_BUCKET]:  # キャラクターバケット追加
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
        {"id": str(uuid.uuid4()), "name": "北海道"},
        {"id": str(uuid.uuid4()), "name": "青森県"},
        {"id": str(uuid.uuid4()), "name": "岩手県"},
        {"id": str(uuid.uuid4()), "name": "宮城県"},
        {"id": str(uuid.uuid4()), "name": "秋田県"},
        {"id": str(uuid.uuid4()), "name": "山形県"},
        {"id": str(uuid.uuid4()), "name": "福島県"},
        {"id": str(uuid.uuid4()), "name": "茨城県"},
        {"id": str(uuid.uuid4()), "name": "栃木県"},
        {"id": str(uuid.uuid4()), "name": "群馬県"},
        {"id": str(uuid.uuid4()), "name": "埼玉県"},
        {"id": str(uuid.uuid4()), "name": "千葉県"},
        {"id": str(uuid.uuid4()), "name": "東京都"},
        {"id": str(uuid.uuid4()), "name": "神奈川県"},
        {"id": str(uuid.uuid4()), "name": "新潟県"},
        {"id": str(uuid.uuid4()), "name": "富山県"},
        {"id": str(uuid.uuid4()), "name": "石川県"},
        {"id": str(uuid.uuid4()), "name": "福井県"},
        {"id": str(uuid.uuid4()), "name": "山梨県"},
        {"id": str(uuid.uuid4()), "name": "長野県"},
        {"id": str(uuid.uuid4()), "name": "岐阜県"},
        {"id": str(uuid.uuid4()), "name": "静岡県"},
        {"id": str(uuid.uuid4()), "name": "愛知県"},
        {"id": str(uuid.uuid4()), "name": "三重県"},
        {"id": str(uuid.uuid4()), "name": "滋賀県"},
        {"id": str(uuid.uuid4()), "name": "京都府"},
        {"id": str(uuid.uuid4()), "name": "大阪府"},
        {"id": str(uuid.uuid4()), "name": "兵庫県"},
        {"id": str(uuid.uuid4()), "name": "奈良県"},
        {"id": str(uuid.uuid4()), "name": "和歌山県"},
        {"id": str(uuid.uuid4()), "name": "鳥取県"},
        {"id": str(uuid.uuid4()), "name": "島根県"},
        {"id": str(uuid.uuid4()), "name": "岡山県"},
        {"id": str(uuid.uuid4()), "name": "広島県"},
        {"id": str(uuid.uuid4()), "name": "山口県"},
        {"id": str(uuid.uuid4()), "name": "徳島県"},
        {"id": str(uuid.uuid4()), "name": "香川県"},
        {"id": str(uuid.uuid4()), "name": "愛媛県"},
        {"id": str(uuid.uuid4()), "name": "高知県"},
        {"id": str(uuid.uuid4()), "name": "福岡県"},
        {"id": str(uuid.uuid4()), "name": "佐賀県"},
        {"id": str(uuid.uuid4()), "name": "長崎県"},
        {"id": str(uuid.uuid4()), "name": "熊本県"},
        {"id": str(uuid.uuid4()), "name": "大分県"},
        {"id": str(uuid.uuid4()), "name": "宮崎県"},
        {"id": str(uuid.uuid4()), "name": "鹿児島県"},
        {"id": str(uuid.uuid4()), "name": "沖縄県"}
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
        {"id": str(uuid.uuid4()), "name": "ショッピング"},
        {"id": str(uuid.uuid4()), "name": "歴史"},
        {"id": str(uuid.uuid4()), "name": "家族"},
        {"id": str(uuid.uuid4()), "name": "温泉"},
        {"id": str(uuid.uuid4()), "name": "アクティビティ"}
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
            "image_path": TEST_IMAGE_PATH,
            "gender": "male",
            "living_place": "東京都新宿区"
        },
        {
            "id": str(uuid.uuid4()),
            "email": "tanaka@example.com",
            "name": "田中太郎",
            "password": "123",
            "birthdate": datetime(1985, 5, 15),
            "profile": "写真撮影が趣味です。一緒に素敵な景色を見に行きましょう。",
            "image_path": TEST_IMAGE_PATH,
            "gender": "male",
            "living_place": "東京都中央区"
        },
        {
            "id": str(uuid.uuid4()),
            "email": "yamada@example.com",
            "name": "山田花子",
            "password": "123",
            "birthdate": datetime(1992, 10, 20),
            "profile": "食べ歩きが大好きです。おいしいお店探しましょう！",
            "image_path": TEST_IMAGE_PATH,
            "gender": "female",
            "living_place": "大阪府大阪市"
        },
        # 動物画像を使ったユーザーを追加
        {
            "id": str(uuid.uuid4()),
            "email": "uma@example.com",
            "name": "馬太郎",
            "password": "123",
            "birthdate": datetime(1988, 3, 15),
            "profile": "乗馬が趣味です。自然の中で過ごすのが好きです。",
            "image_path": os.path.join(os.path.dirname(__file__), "users", "ウマ.png"),
            "gender": "male",
            "living_place": "北海道帯広市"
        },
        {
            "id": str(uuid.uuid4()),
            "email": "okojo@example.com",
            "name": "オコジョ健太",
            "password": "123",
            "birthdate": datetime(1995, 7, 25),
            "profile": "山登りが得意です。高山でも元気に動き回ります！",
            "image_path": os.path.join(os.path.dirname(__file__), "users", "オコジョ.png"),
            "gender": "male",
            "living_place": "北海道旭川市"
        },
        {
            "id": str(uuid.uuid4()),
            "email": "tonakai@example.com",
            "name": "トナカイ花子",
            "password": "123",
            "birthdate": datetime(1993, 12, 24),
            "profile": "寒い地域が大好きです。クリスマスシーズンが特に忙しいです。",
            "image_path": os.path.join(os.path.dirname(__file__), "users", "トナカイ.png"),
            "gender": "female",
            "living_place": "北海道札幌市"
        },
        {
            "id": str(uuid.uuid4()),
            "email": "niwatori@example.com",
            "name": "鶏次郎",
            "password": "123",
            "birthdate": datetime(1991, 4, 1),
            "profile": "早起きが得意です。朝の散歩ツアーを企画しています。",
            "image_path": os.path.join(os.path.dirname(__file__), "users", "ニワトリ.png"),
            "gender": "male",
            "living_place": "東京都世田谷区"
        },
        {
            "id": str(uuid.uuid4()),
            "email": "hyrax@example.com",
            "name": "ハイラックス夏子",
            "password": "123",
            "birthdate": datetime(1989, 8, 10),
            "profile": "岩場での休憩が趣味です。日向ぼっこが大好き。",
            "image_path": os.path.join(os.path.dirname(__file__), "users", "ハイラックス.png"),
            "gender": "female",
            "living_place": "沖縄県那覇市"
        },
        {
            "id": str(uuid.uuid4()),
            "email": "hamster@example.com",
            "name": "ハムスター翔",
            "password": "123",
            "birthdate": datetime(1996, 2, 14),
            "profile": "小さな隠れ家が大好きです。種集めが趣味です。",
            "image_path": os.path.join(os.path.dirname(__file__), "users", "ハムスター.png"),
            "gender": "male",
            "living_place": "東京都中野区"
        },
        {
            "id": str(uuid.uuid4()),
            "email": "rakuda@example.com",
            "name": "ラクダ正太",
            "password": "123",
            "birthdate": datetime(1987, 6, 30),
            "profile": "砂漠ツアーガイドをしています。暑さに強いです。",
            "image_path": os.path.join(os.path.dirname(__file__), "users", "ラクダ.png"),
            "gender": "male",
            "living_place": "沖縄県石垣市"
        },
        {
            "id": str(uuid.uuid4()),
            "email": "sheep@example.com",
            "name": "黒羊めぐみ",
            "password": "123",
            "birthdate": datetime(1994, 9, 5),
            "profile": "モフモフした毛が自慢です。編み物ワークショップを開催しています。",
            "image_path": os.path.join(os.path.dirname(__file__), "users", "黒い羊.png"),
            "gender": "female",
            "living_place": "北海道ニセコ町"
        }
    ]
    
    user_ids = {}
    age_statuses = ['none', 'rejected', 'extraction_failed', 'approved', 'pending']  # 様々な年齢認証ステータス
    
    for i, user_data in enumerate(users):
        # test@example.comは年齢認証未実施に設定
        if user_data["email"] == "test@example.com":
            age_status = 'none'
        else:
            # その他のユーザーは順番に異なるステータスを設定
            age_status = age_statuses[i % len(age_statuses)]
        
        is_age_verified = age_status == 'approved'
        
        user = User(
            id=user_data["id"],
            email_address=user_data["email"],
            user_name=user_data["name"],
            birthdate=user_data["birthdate"],
            profile_message=user_data["profile"],
            gender=user_data["gender"],
            living_place=user_data["living_place"],
            is_certificated=True,
            age_verification_status=age_status,
            is_age_verified=is_age_verified
        )
        user.set_password(user_data["password"])
        db.session.add(user)
        
        user_ids[user_data["email"]] = user_data["id"]
        
        # 画像をアップロード
        filename = f"user_{user_data['id']}_profile.png"
        image_url = upload_image(MINIO_BUCKET, user_data["image_path"], filename)
        if image_url:
            user.user_image_url = image_url
        
        print(f"👤 ユーザー {user_data['name']} ({user_data['email']}) - 年齢認証ステータス: {age_status}")
    
    db.session.commit()
    print("✅ ユーザーを追加しました（年齢認証ステータス設定済み）")
    
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
            "area_id": areas[8]["id"],  # 栃木県
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
            "area_id": areas[12]["id"],  # 東京都
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
            "area_id": areas[25]["id"],  # 京都府
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
            "area_id": areas[13]["id"],  # 神奈川県
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
            "area_id": areas[26]["id"],  # 大阪府
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
            "area_id": areas[12]["id"],  # 東京都
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
            "area_id": areas[0]["id"],  # 北海道
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
            "area_id": areas[0]["id"],  # 北海道
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
            "area_id": areas[0]["id"],  # 北海道
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
            "area_id": areas[12]["id"],  # 東京都
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
            "area_id": areas[46]["id"],  # 沖縄県
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
            "area_id": areas[12]["id"],  # 東京都
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
            "area_id": areas[46]["id"],  # 沖縄県（砂浜を砂漠に見立てて）
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
            "area_id": areas[0]["id"],  # 北海道
            "limit": 10,
            "current": 1,
            "published_at": datetime.now(JST) - timedelta(days=3),
            "tags": ["文化", "ショッピング"]
        },
        
        # 山岳トレッキングのメッセージ
    ]
    
    # イベントの作成とIDの取得
    event_ids = []
    for i, event_data in enumerate(events):
        tags = event_data.pop("tags", [])  # tagsキーを取り出して削除
        
        # ステータスを設定（最初のイベントは開催中、2番目は終了、それ以外は開催予定）
        if i == 3:
            status = 'started'
        elif i == 4:
            status = 'ended'
        else:
            status = 'pending'
        
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
            status=status
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
            joined_at=datetime.now(JST) - timedelta(days=1, hours=14 + i)  # 最初のメッセージより前（days=1, hours=12）
        )
        db.session.add(member)
        
        # システムメッセージを追加
        user_name = next((u["name"] for u in users if u["email"] == email), "ユーザー")
        system_message = EventMessage(
            id=str(uuid.uuid4()),
            event_id=event_ids[0],
            sender_user_id=None,  # システムメッセージ
            content=f"{user_name}さんがイベントに参加しました",
            timestamp=datetime.now(JST) - timedelta(days=1, hours=14 + i),  # 最初のメッセージより前
            message_type='system'
        )
        db.session.add(system_message)
    
    # イベント2に別の動物ユーザーを参加させる
    event2_members = ["hyrax@example.com", "hamster@example.com", "sheep@example.com"]
    for i, email in enumerate(event2_members):
        member = UserMemberGroup(
            user_id=user_ids[email], 
            event_id=event_ids[1],
            joined_at=datetime.now(JST) - timedelta(days=3, hours=16 + i)  # 最初のメッセージより前（days=3, hours=15）
        )
        db.session.add(member)
        
        # システムメッセージを追加
        user_name = next((u["name"] for u in users if u["email"] == email), "ユーザー")
        system_message = EventMessage(
            id=str(uuid.uuid4()),
            event_id=event_ids[1],
            sender_user_id=None,  # システムメッセージ
            content=f"{user_name}さんがイベントに参加しました",
            timestamp=datetime.now(JST) - timedelta(days=3, hours=16 + i),  # 最初のメッセージより前
            message_type='system'
        )
        db.session.add(system_message)
    
    # イベント3に残りの動物ユーザーを参加させる
    event3_members = ["rakuda@example.com", "hamster@example.com"]
    for i, email in enumerate(event3_members):
        member = UserMemberGroup(
            user_id=user_ids[email], 
            event_id=event_ids[2],
            joined_at=datetime.now(JST) - timedelta(days=10, hours=16 + i)  # 紅葉撮影会のメッセージは10日前から始まる
        )
        db.session.add(member)
        
        # システムメッセージを追加
        user_name = next((u["name"] for u in users if u["email"] == email), "ユーザー")
        system_message = EventMessage(
            id=str(uuid.uuid4()),
            event_id=event_ids[2],
            sender_user_id=None,  # システムメッセージ
            content=f"{user_name}さんがイベントに参加しました",
            timestamp=datetime.now(JST) - timedelta(days=10, hours=16 + i),  # メッセージより前（days=10, hours=15）
            message_type='system'
        )
        db.session.add(system_message)
    
    # イベント4（鎌倉散策ツアー）に参加メンバーを追加
    event4_members = ["test@example.com", "yamada@example.com", "hamster@example.com"]
    for i, email in enumerate(event4_members):
        member = UserMemberGroup(
            user_id=user_ids[email], 
            event_id=event_ids[3],
            joined_at=datetime.now(JST) - timedelta(days=6, hours=i)  # 鎌倉散策のメッセージは5日前から
        )
        db.session.add(member)
        
        # システムメッセージを追加
        user_name = next((u["name"] for u in users if u["email"] == email), "ユーザー")
        system_message = EventMessage(
            id=str(uuid.uuid4()),
            event_id=event_ids[3],
            sender_user_id=None,  # システムメッセージ
            content=f"{user_name}さんがイベントに参加しました",
            timestamp=datetime.now(JST) - timedelta(days=6, hours=i),  # メッセージより前
            message_type='system'
        )
        db.session.add(system_message)
    
    # イベント5（大阪たこ焼きパーティー）に参加メンバーを追加
    event5_members = ["test@example.com", "tonakai@example.com", "hyrax@example.com", "niwatori@example.com"]
    for i, email in enumerate(event5_members):
        member = UserMemberGroup(
            user_id=user_ids[email], 
            event_id=event_ids[4],
            joined_at=datetime.now(JST) - timedelta(days=4, hours=i)  # たこ焼きパーティーのメッセージは3日前から
        )
        db.session.add(member)
        
        # システムメッセージを追加
        user_name = next((u["name"] for u in users if u["email"] == email), "ユーザー")
        system_message = EventMessage(
            id=str(uuid.uuid4()),
            event_id=event_ids[4],
            sender_user_id=None,  # システムメッセージ
            content=f"{user_name}さんがイベントに参加しました",
            timestamp=datetime.now(JST) - timedelta(days=4, hours=i),  # メッセージより前
            message_type='system'
        )
        db.session.add(system_message)
    
    # イベント6（寿司作り体験教室）に参加メンバーを追加
    event6_members = ["tanaka@example.com", "niwatori@example.com", "sheep@example.com", "test@example.com"]
    for i, email in enumerate(event6_members):
        member = UserMemberGroup(
            user_id=user_ids[email], 
            event_id=event_ids[5],
            joined_at=datetime.now(JST) - timedelta(days=7, hours=i)  # 寿司作り体験のメッセージは6日前から
        )
        db.session.add(member)
        
        # システムメッセージを追加
        user_name = next((u["name"] for u in users if u["email"] == email), "ユーザー")
        system_message = EventMessage(
            id=str(uuid.uuid4()),
            event_id=event_ids[5],
            sender_user_id=None,  # システムメッセージ
            content=f"{user_name}さんがイベントに参加しました",
            timestamp=datetime.now(JST) - timedelta(days=7, hours=i),  # メッセージより前
            message_type='system'
        )
        db.session.add(system_message)
    
    # イベント7（乗馬体験ツアー）に参加メンバーを追加
    # 主催者の馬太郎はすでに追加済み
    
    # イベント8（山岳トレッキング）に参加メンバーを追加
    event8_members = ["uma@example.com", "sheep@example.com", "tonakai@example.com"]
    for i, email in enumerate(event8_members):
        member = UserMemberGroup(
            user_id=user_ids[email], 
            event_id=event_ids[7],
            joined_at=datetime.now(JST) - timedelta(days=8, hours=i)  # 山岳トレッキングのメッセージは7日前から
        )
        db.session.add(member)
        
        # システムメッセージを追加
        user_name = next((u["name"] for u in users if u["email"] == email), "ユーザー")
        system_message = EventMessage(
            id=str(uuid.uuid4()),
            event_id=event_ids[7],
            sender_user_id=None,  # システムメッセージ
            content=f"{user_name}さんがイベントに参加しました",
            timestamp=datetime.now(JST) - timedelta(days=8, hours=i),  # メッセージより前
            message_type='system'
        )
        db.session.add(system_message)
    
    # イベント9（クリスマスマーケット訪問）に参加メンバーを追加
    event9_members = ["sheep@example.com", "okojo@example.com", "uma@example.com", "hamster@example.com"]
    for i, email in enumerate(event9_members):
        member = UserMemberGroup(
            user_id=user_ids[email], 
            event_id=event_ids[8],
            joined_at=datetime.now(JST) - timedelta(days=6, hours=i)  # クリスマスマーケットのメッセージは5日前から
        )
        db.session.add(member)
        
        # システムメッセージを追加
        user_name = next((u["name"] for u in users if u["email"] == email), "ユーザー")
        system_message = EventMessage(
            id=str(uuid.uuid4()),
            event_id=event_ids[8],
            sender_user_id=None,  # システムメッセージ
            content=f"{user_name}さんがイベントに参加しました",
            timestamp=datetime.now(JST) - timedelta(days=6, hours=i),  # メッセージより前
            message_type='system'
        )
        db.session.add(system_message)
    
    # イベント10（早朝サンライズヨガ）に参加メンバーを追加
    # 主催者の鶏次郎はすでに追加済み
    
    # イベント11（岩場でのんびりピクニック）に参加メンバーを追加
    event11_members = ["hamster@example.com", "rakuda@example.com", "tonakai@example.com"]
    for i, email in enumerate(event11_members):
        member = UserMemberGroup(
            user_id=user_ids[email], 
            event_id=event_ids[10],
            joined_at=datetime.now(JST) - timedelta(days=6, hours=i)  # 岩場でのんびりピクニックのメッセージは5日前から
        )
        db.session.add(member)
        
        # システムメッセージを追加
        user_name = next((u["name"] for u in users if u["email"] == email), "ユーザー")
        system_message = EventMessage(
            id=str(uuid.uuid4()),
            event_id=event_ids[10],
            sender_user_id=None,  # システムメッセージ
            content=f"{user_name}さんがイベントに参加しました",
            timestamp=datetime.now(JST) - timedelta(days=6, hours=i),  # メッセージより前
            message_type='system'
        )
        db.session.add(system_message)
    
    # イベント12（種集めウォーキング）に参加メンバーを追加
    event12_members = ["niwatori@example.com", "tonakai@example.com", "hyrax@example.com"]
    for i, email in enumerate(event12_members):
        member = UserMemberGroup(
            user_id=user_ids[email], 
            event_id=event_ids[11],
            joined_at=datetime.now(JST) - timedelta(days=8, hours=i)  # 種集めウォーキングのメッセージは7日前から
        )
        db.session.add(member)
        
        # システムメッセージを追加
        user_name = next((u["name"] for u in users if u["email"] == email), "ユーザー")
        system_message = EventMessage(
            id=str(uuid.uuid4()),
            event_id=event_ids[11],
            sender_user_id=None,  # システムメッセージ
            content=f"{user_name}さんがイベントに参加しました",
            timestamp=datetime.now(JST) - timedelta(days=8, hours=i),  # メッセージより前
            message_type='system'
        )
        db.session.add(system_message)
    
    # イベント13（砂漠ツアーガイド）に参加メンバーを追加
    event13_members = ["hyrax@example.com", "sheep@example.com", "hamster@example.com", "uma@example.com", "tonakai@example.com"]
    for i, email in enumerate(event13_members):
        member = UserMemberGroup(
            user_id=user_ids[email], 
            event_id=event_ids[12],
            joined_at=datetime.now(JST) - timedelta(days=7, hours=i)  # 砂漠ツアーガイドのメッセージは6日前から
        )
        db.session.add(member)
        
        # システムメッセージを追加
        user_name = next((u["name"] for u in users if u["email"] == email), "ユーザー")
        system_message = EventMessage(
            id=str(uuid.uuid4()),
            event_id=event_ids[12],
            sender_user_id=None,  # システムメッセージ
            content=f"{user_name}さんがイベントに参加しました",
            timestamp=datetime.now(JST) - timedelta(days=7, hours=i),  # メッセージより前
            message_type='system'
        )
        db.session.add(system_message)
    
    # イベント14（編み物ワークショップ）に参加メンバーを追加
    event14_members = ["tonakai@example.com", "okojo@example.com", "uma@example.com"]
    for i, email in enumerate(event14_members):
        member = UserMemberGroup(
            user_id=user_ids[email], 
            event_id=event_ids[13],
            joined_at=datetime.now(JST) - timedelta(days=8, hours=i)  # 編み物ワークショップのメッセージは7日前から
        )
        db.session.add(member)
        
        # システムメッセージを追加
        user_name = next((u["name"] for u in users if u["email"] == email), "ユーザー")
        system_message = EventMessage(
            id=str(uuid.uuid4()),
            event_id=event_ids[13],
            sender_user_id=None,  # システムメッセージ
            content=f"{user_name}さんがイベントに参加しました",
            timestamp=datetime.now(JST) - timedelta(days=8, hours=i),  # メッセージより前
            message_type='system'
        )
        db.session.add(system_message)
    
    # イベントの参加者数を更新
    for i, event_id in enumerate(event_ids):
        event = Event.query.get(event_id)
        if i == 0:  # いちご狩りツアー
            event.current_persons = 1 + len(event1_members)
        elif i == 1:  # 東京スカイツリー観光
            event.current_persons = 1 + len(event2_members)
        elif i == 2:  # 京都紅葉撮影会
            event.current_persons = 1 + len(event3_members)
        elif i == 3:  # 鎌倉散策ツアー
            event.current_persons = 1 + len(event4_members)
        elif i == 4:  # 大阪たこ焼きパーティー
            event.current_persons = 1 + len(event5_members)
        elif i == 5:  # 寿司作り体験教室
            event.current_persons = 1 + len(event6_members)
        elif i == 6:  # 乗馬体験ツアー
            event.current_persons = 1  # 主催者のみ
        elif i == 7:  # 山岳トレッキング
            event.current_persons = 1 + len(event8_members)
        elif i == 8:  # クリスマスマーケット訪問
            event.current_persons = 1 + len(event9_members)
        elif i == 9:  # 早朝サンライズヨガ
            event.current_persons = 1  # 主催者のみ
        elif i == 10:  # 岩場でのんびりピクニック
            event.current_persons = 1 + len(event11_members)
        elif i == 11:  # 種集めウォーキング
            event.current_persons = 1 + len(event12_members)
        elif i == 12:  # 砂漠ツアーガイド
            event.current_persons = 1 + len(event13_members)
        elif i == 13:  # 編み物ワークショップ
            event.current_persons = 1 + len(event14_members)
    
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
        },
        {
            "id": str(uuid.uuid4()),
            "title": "沖縄の海を楽しむおすすめスポット",
            "message": "沖縄旅行で海を楽しめるおすすめスポットを教えてください！シュノーケリングやダイビングに興味があります。",
            "image_id": None,
            "area_id": areas[3]["id"],  # 沖縄
            "author_id": user_ids["hyrax@example.com"],
            "published_at": datetime.now(JST) - timedelta(hours=5)
        },
        # 追加スレッド
        {
            "id": str(uuid.uuid4()),
            "title": "東京の隠れた観光スポット",
            "message": "東京在住の方に質問です。観光客があまり知らない、地元の人が好むスポットを教えてください！",
            "image_id": None,
            "area_id": areas[0]["id"],  # 東京
            "author_id": user_ids["sheep@example.com"],
            "published_at": datetime.now(JST) - timedelta(days=2, hours=4)
        },
        {
            "id": str(uuid.uuid4()),
            "title": "大阪のB級グルメ情報",
            "message": "大阪で必ず食べるべきB級グルメを教えてください！たこ焼き・お好み焼き以外で地元の方がおすすめするものが知りたいです。",
            "image_id": None,
            "area_id": areas[1]["id"],  # 大阪
            "author_id": user_ids["tonakai@example.com"],
            "published_at": datetime.now(JST) - timedelta(days=3, hours=12)
        },
        {
            "id": str(uuid.uuid4()),
            "title": "金沢旅行のモデルコース",
            "message": "金沢に2泊3日で旅行する予定です。おすすめの観光コースを教えてください。",
            "image_id": None,
            "area_id": areas[5]["id"],  # その他
            "author_id": user_ids["niwatori@example.com"],
            "published_at": datetime.now(JST) - timedelta(days=2, hours=15)
        },
        {
            "id": str(uuid.uuid4()),
            "title": "子連れで楽しめる九州の観光地",
            "message": "小学生の子供と九州旅行を計画中です。子供が楽しめるスポットをぜひ教えてください！",
            "image_id": None,
            "area_id": areas[5]["id"],  # その他
            "author_id": user_ids["rakuda@example.com"],
            "published_at": datetime.now(JST) - timedelta(days=4, hours=8)
        },
        {
            "id": str(uuid.uuid4()),
            "title": "箱根日帰り旅行のプラン",
            "message": "東京から箱根に日帰りで行きたいと思います。効率よく回れるプランはありますか？",
            "image_id": None,
            "area_id": areas[0]["id"],  # 東京（近郊）
            "author_id": user_ids["hamster@example.com"],
            "published_at": datetime.now(JST) - timedelta(days=1, hours=18)
        },
        {
            "id": str(uuid.uuid4()),
            "title": "四国おすすめ観光コース",
            "message": "四国一周を考えています。各県のおすすめスポットを教えてください！",
            "image_id": None,
            "area_id": areas[5]["id"],  # その他
            "author_id": user_ids["uma@example.com"],
            "published_at": datetime.now(JST) - timedelta(days=5, hours=6)
        },
        {
            "id": str(uuid.uuid4()),
            "title": "広島で平和学習と観光",
            "message": "広島で平和記念公園と宮島を1日で回るプランを考えています。アドバイスをお願いします。",
            "image_id": None,
            "area_id": areas[5]["id"],  # その他
            "author_id": user_ids["okojo@example.com"],
            "published_at": datetime.now(JST) - timedelta(days=3, hours=20)
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
        {"thread_id": thread_ids[1], "tags": ["自然", "アウトドア"]},
        {"thread_id": thread_ids[2], "tags": ["自然", "アウトドア", "スポーツ"]},
        {"thread_id": thread_ids[3], "tags": ["文化", "グルメ"]},
        {"thread_id": thread_ids[4], "tags": ["グルメ", "文化"]},
        {"thread_id": thread_ids[5], "tags": ["文化", "自然", "歴史"]},
        {"thread_id": thread_ids[6], "tags": ["家族", "自然", "アクティビティ"]},
        {"thread_id": thread_ids[7], "tags": ["自然", "温泉"]},
        {"thread_id": thread_ids[8], "tags": ["自然", "文化", "歴史"]},
        {"thread_id": thread_ids[9], "tags": ["文化", "歴史"]}
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
        {"user_id": user_ids["test@example.com"], "thread_id": thread_ids[1]},
        {"user_id": user_ids["uma@example.com"], "thread_id": thread_ids[0]},
        {"user_id": user_ids["niwatori@example.com"], "thread_id": thread_ids[0]},
        {"user_id": user_ids["okojo@example.com"], "thread_id": thread_ids[0]},
        {"user_id": user_ids["tonakai@example.com"], "thread_id": thread_ids[0]},
        {"user_id": user_ids["hyrax@example.com"], "thread_id": thread_ids[0]},
        {"user_id": user_ids["hamster@example.com"], "thread_id": thread_ids[0]},
        {"user_id": user_ids["sheep@example.com"], "thread_id": thread_ids[0]},
        {"user_id": user_ids["rakuda@example.com"], "thread_id": thread_ids[0]},
        
        {"user_id": user_ids["tanaka@example.com"], "thread_id": thread_ids[1]},
        {"user_id": user_ids["uma@example.com"], "thread_id": thread_ids[1]},
        {"user_id": user_ids["okojo@example.com"], "thread_id": thread_ids[1]},
        {"user_id": user_ids["tonakai@example.com"], "thread_id": thread_ids[1]},
        {"user_id": user_ids["niwatori@example.com"], "thread_id": thread_ids[1]},
        {"user_id": user_ids["hamster@example.com"], "thread_id": thread_ids[1]},
        
        {"user_id": user_ids["test@example.com"], "thread_id": thread_ids[2]},
        {"user_id": user_ids["tanaka@example.com"], "thread_id": thread_ids[2]},
        {"user_id": user_ids["yamada@example.com"], "thread_id": thread_ids[2]},
        {"user_id": user_ids["uma@example.com"], "thread_id": thread_ids[2]},
        
        {"user_id": user_ids["yamada@example.com"], "thread_id": thread_ids[3]},
        {"user_id": user_ids["uma@example.com"], "thread_id": thread_ids[3]},
        {"user_id": user_ids["tanaka@example.com"], "thread_id": thread_ids[3]},
        {"user_id": user_ids["test@example.com"], "thread_id": thread_ids[3]},
        {"user_id": user_ids["tonakai@example.com"], "thread_id": thread_ids[3]},
        
        {"user_id": user_ids["test@example.com"], "thread_id": thread_ids[4]},
        {"user_id": user_ids["yamada@example.com"], "thread_id": thread_ids[4]},
        {"user_id": user_ids["tanaka@example.com"], "thread_id": thread_ids[4]},
        
        {"user_id": user_ids["test@example.com"], "thread_id": thread_ids[5]},
        {"user_id": user_ids["yamada@example.com"], "thread_id": thread_ids[5]},
        {"user_id": user_ids["uma@example.com"], "thread_id": thread_ids[5]},
        {"user_id": user_ids["okojo@example.com"], "thread_id": thread_ids[5]},
        
        {"user_id": user_ids["tanaka@example.com"], "thread_id": thread_ids[6]},
        {"user_id": user_ids["yamada@example.com"], "thread_id": thread_ids[6]},
        {"user_id": user_ids["uma@example.com"], "thread_id": thread_ids[6]},
        {"user_id": user_ids["niwatori@example.com"], "thread_id": thread_ids[6]},
        {"user_id": user_ids["test@example.com"], "thread_id": thread_ids[6]},
        
        {"user_id": user_ids["test@example.com"], "thread_id": thread_ids[7]},
        {"user_id": user_ids["tanaka@example.com"], "thread_id": thread_ids[7]},
        
        {"user_id": user_ids["test@example.com"], "thread_id": thread_ids[8]},
        {"user_id": user_ids["yamada@example.com"], "thread_id": thread_ids[8]},
        {"user_id": user_ids["hyrax@example.com"], "thread_id": thread_ids[8]},
        
        {"user_id": user_ids["test@example.com"], "thread_id": thread_ids[9]},
        {"user_id": user_ids["tanaka@example.com"], "thread_id": thread_ids[9]},
        {"user_id": user_ids["uma@example.com"], "thread_id": thread_ids[9]},
        {"user_id": user_ids["sheep@example.com"], "thread_id": thread_ids[9]}
    ]
    
    for heart in thread_hearts:
        heart_obj = UserHeartThread(user_id=heart["user_id"], thread_id=heart["thread_id"])
        db.session.add(heart_obj)
    
    db.session.commit()
    print("✅ スレッドのいいねを設定しました")
    
    # スレッドメッセージを作成
    thread_messages = [
        # 京都のおすすめ観光スポットスレッド
        {
            "id": str(uuid.uuid4()),
            "thread_id": thread_ids[0],
            "sender_user_id": user_ids["test@example.com"],
            "content": "京都のおすすめ観光スポットを教えてください！初めて行くので地元の方のおすすめが知りたいです。",
            "timestamp": datetime.now(JST) - timedelta(days=1, hours=2),
            "message_type": "text"
        },
        {
            "id": str(uuid.uuid4()),
            "thread_id": thread_ids[0],
            "sender_user_id": user_ids["tanaka@example.com"],
            "content": "清水寺は必見です！夕方の景色が特に美しいです。夕焼けの時間帯がおすすめですよ。",
            "timestamp": datetime.now(JST) - timedelta(days=1, hours=1, minutes=30),
            "message_type": "text"
        },
        {
            "id": str(uuid.uuid4()),
            "thread_id": thread_ids[0],
            "sender_user_id": user_ids["yamada@example.com"],
            "content": "伏見稲荷大社も外せないスポットです。千本鳥居の写真は絶対に撮りたいですね！",
            "timestamp": datetime.now(JST) - timedelta(days=1, hours=1),
            "message_type": "text"
        },
        {
            "id": str(uuid.uuid4()),
            "thread_id": thread_ids[0],
            "sender_user_id": user_ids["niwatori@example.com"],
            "content": "早朝の嵐山竹林は人が少なくて静かに散策できておすすめです。朝活するならぜひ！",
            "timestamp": datetime.now(JST) - timedelta(days=1, minutes=45),
            "message_type": "text"
        },
        {
            "id": str(uuid.uuid4()),
            "thread_id": thread_ids[0],
            "sender_user_id": user_ids["test@example.com"],
            "content": "みなさん、ありがとうございます！清水寺、伏見稲荷、嵐山竹林を予定に入れます。京都でおすすめのカフェや食事処はありますか？",
            "timestamp": datetime.now(JST) - timedelta(days=1, minutes=30),
            "message_type": "text"
        },
        {
            "id": str(uuid.uuid4()),
            "thread_id": thread_ids[0],
            "sender_user_id": user_ids["hyrax@example.com"],
            "content": "祇園にある和カフェ「茶寮」がとても素敵ですよ。お抹茶パフェが人気です！",
            "timestamp": datetime.now(JST) - timedelta(days=1, minutes=15),
            "message_type": "text"
        },
        {
            "id": str(uuid.uuid4()),
            "thread_id": thread_ids[0],
            "sender_user_id": user_ids["yamada@example.com"],
            "content": "先斗町の「京味」という居酒屋がおすすめです。京都の郷土料理が手頃な価格で楽しめます。",
            "timestamp": datetime.now(JST) - timedelta(hours=23),
            "message_type": "text"
        },
        {
            "id": str(uuid.uuid4()),
            "thread_id": thread_ids[0],
            "sender_user_id": user_ids["uma@example.com"],
            "content": "祇園四条駅近くの「抹茶館」のパフェもおすすめです。暑い日には冷たい抹茶スイーツが最高です。",
            "timestamp": datetime.now(JST) - timedelta(hours=22),
            "message_type": "text"
        },
        {
            "id": str(uuid.uuid4()),
            "thread_id": thread_ids[0],
            "sender_user_id": user_ids["test@example.com"],
            "content": "これは嬉しいです！カフェと食事の情報もありがとうございます。京都の服装について何かアドバイスはありますか？9月中旬に行く予定です。",
            "timestamp": datetime.now(JST) - timedelta(hours=21),
            "message_type": "text"
        },
        {
            "id": str(uuid.uuid4()),
            "thread_id": thread_ids[0],
            "sender_user_id": user_ids["tonakai@example.com"],
            "content": "9月の京都はまだ暑いことが多いですが、朝晩は少し涼しくなります。カーディガンなど羽織るものがあると安心です。",
            "timestamp": datetime.now(JST) - timedelta(hours=20),
            "message_type": "text"
        },
        {
            "id": str(uuid.uuid4()),
            "thread_id": thread_ids[0],
            "sender_user_id": user_ids["tanaka@example.com"],
            "content": "寺社仏閣を回る際は歩きやすい靴が必須です！また、急な雨に備えて折りたたみ傘があると便利ですよ。",
            "timestamp": datetime.now(JST) - timedelta(hours=19),
            "message_type": "text"
        },
        {
            "id": str(uuid.uuid4()),
            "thread_id": thread_ids[0],
            "sender_user_id": user_ids["niwatori@example.com"],
            "content": "京都は交通手段も大事です。市バスの一日乗車券があると便利ですよ。主要な観光地をほぼカバーしています。",
            "timestamp": datetime.now(JST) - timedelta(hours=18),
            "message_type": "text"
        },
        {
            "id": str(uuid.uuid4()),
            "thread_id": thread_ids[0],
            "sender_user_id": user_ids["test@example.com"],
            "content": "市バスの一日乗車券は必須ですね！みなさん本当にありがとうございます。これだけ情報があれば京都旅行が楽しみになりました！",
            "timestamp": datetime.now(JST) - timedelta(hours=12),
            "message_type": "text"
        },
        
        # 北海道旅行のアドバイススレッド
        {
            "id": str(uuid.uuid4()),
            "thread_id": thread_ids[1],
            "sender_user_id": user_ids["yamada@example.com"],
            "content": "北海道旅行で絶対に行くべき場所は？冬に1週間ほど行く予定です。",
            "timestamp": datetime.now(JST) - timedelta(hours=10),
            "message_type": "text"
        },
        {
            "id": str(uuid.uuid4()),
            "thread_id": thread_ids[1],
            "sender_user_id": user_ids["tonakai@example.com"],
            "content": "冬の北海道なら札幌雪まつりは外せません！2月上旬に開催されるので、その時期であれば必見です。",
            "timestamp": datetime.now(JST) - timedelta(hours=9, minutes=45),
            "message_type": "text"
        },
        {
            "id": str(uuid.uuid4()),
            "thread_id": thread_ids[1],
            "sender_user_id": user_ids["okojo@example.com"],
            "content": "ニセコでのスキーやスノーボードもおすすめ！パウダースノーは世界的に有名です。",
            "timestamp": datetime.now(JST) - timedelta(hours=9, minutes=30),
            "message_type": "text"
        },
        {
            "id": str(uuid.uuid4()),
            "thread_id": thread_ids[1],
            "sender_user_id": user_ids["sheep@example.com"],
            "content": "冬の小樽運河の夜景は幻想的で美しいです。雪と灯りのコントラストが素敵ですよ。",
            "timestamp": datetime.now(JST) - timedelta(hours=9),
            "message_type": "text"
        },
        {
            "id": str(uuid.uuid4()),
            "thread_id": thread_ids[1],
            "sender_user_id": user_ids["yamada@example.com"],
            "content": "札幌雪まつりの時期に合わせられそうです！スキーは初心者ですが、ニセコは初心者でも楽しめますか？",
            "timestamp": datetime.now(JST) - timedelta(hours=8, minutes=30),
            "message_type": "text"
        },
        {
            "id": str(uuid.uuid4()),
            "thread_id": thread_ids[1],
            "sender_user_id": user_ids["okojo@example.com"],
            "content": "ニセコは初心者向けのコースもあるので大丈夫ですよ！レッスンも充実していて、外国人インストラクターも多いです。",
            "timestamp": datetime.now(JST) - timedelta(hours=8, minutes=15),
            "message_type": "text"
        },
        {
            "id": str(uuid.uuid4()),
            "thread_id": thread_ids[1],
            "sender_user_id": user_ids["uma@example.com"],
            "content": "知床も素晴らしいですが、冬は天候によってアクセスが難しいことがあるので注意が必要です。",
            "timestamp": datetime.now(JST) - timedelta(hours=8),
            "message_type": "text"
        },
        {
            "id": str(uuid.uuid4()),
            "thread_id": thread_ids[1],
            "sender_user_id": user_ids["test@example.com"],
            "content": "旭山動物園もおすすめです。冬ならではのペンギンの散歩や動物たちの様子が見られます。",
            "timestamp": datetime.now(JST) - timedelta(hours=7, minutes=45),
            "message_type": "text"
        },
        {
            "id": str(uuid.uuid4()),
            "thread_id": thread_ids[1],
            "sender_user_id": user_ids["yamada@example.com"],
            "content": "旭山動物園は行きたいと思っていました！ありがとうございます。北海道でのグルメのおすすめはありますか？",
            "timestamp": datetime.now(JST) - timedelta(hours=7, minutes=30),
            "message_type": "text"
        },
        {
            "id": str(uuid.uuid4()),
            "thread_id": thread_ids[1],
            "sender_user_id": user_ids["tonakai@example.com"],
            "content": "札幌のスープカレーは必食です！「らっきょ」や「Picante」など名店が多いですよ。",
            "timestamp": datetime.now(JST) - timedelta(hours=7, minutes=15),
            "message_type": "text"
        },
        {
            "id": str(uuid.uuid4()),
            "thread_id": thread_ids[1],
            "sender_user_id": user_ids["hamster@example.com"],
            "content": "小樽ではもちろん海鮮！「小樽三角市場」で新鮮な海鮮丼を食べるのがおすすめです。",
            "timestamp": datetime.now(JST) - timedelta(hours=7),
            "message_type": "text"
        },
        {
            "id": str(uuid.uuid4()),
            "thread_id": thread_ids[1],
            "sender_user_id": user_ids["sheep@example.com"],
            "content": "冬の北海道は寒いので、温かいラーメンも良いですよ。札幌の味噌ラーメンは特に有名です。「すみれ」や「白樺山荘」がおすすめ！",
            "timestamp": datetime.now(JST) - timedelta(hours=6, minutes=45),
            "message_type": "text"
        },
        {
            "id": str(uuid.uuid4()),
            "thread_id": thread_ids[1],
            "sender_user_id": user_ids["tanaka@example.com"],
            "content": "函館の夜景も美しいですよ。函館山からの景色は日本三大夜景の一つです。",
            "timestamp": datetime.now(JST) - timedelta(hours=6, minutes=30),
            "message_type": "text"
        },
        {
            "id": str(uuid.uuid4()),
            "thread_id": thread_ids[1],
            "sender_user_id": user_ids["yamada@example.com"],
            "content": "みなさん本当にありがとうございます！これだけの情報があれば北海道旅行が楽しみになりました。スープカレーとラーメンは絶対に食べてみます！",
            "timestamp": datetime.now(JST) - timedelta(hours=6),
            "message_type": "text"
        },
        {
            "id": str(uuid.uuid4()),
            "thread_id": thread_ids[1],
            "sender_user_id": user_ids["niwatori@example.com"],
            "content": "冬の北海道は服装も重要です！厚手のダウンやブーツ、手袋、マフラーなど、しっかりした防寒具が必要ですよ。",
            "timestamp": datetime.now(JST) - timedelta(hours=5),
            "message_type": "text"
        },
        {
            "id": str(uuid.uuid4()),
            "thread_id": thread_ids[1],
            "sender_user_id": user_ids["okojo@example.com"],
            "content": "そうそう、靴は滑り止めのしっかりしたものがおすすめです。道路が凍結していることが多いので。",
            "timestamp": datetime.now(JST) - timedelta(hours=4, minutes=30),
            "message_type": "text"
        },
        {
            "id": str(uuid.uuid4()),
            "thread_id": thread_ids[1],
            "sender_user_id": user_ids["yamada@example.com"],
            "content": "防寒対策もしっかりします！本当にありがとうございました。素敵な北海道旅行にします！",
            "timestamp": datetime.now(JST) - timedelta(hours=4),
            "message_type": "text"
        },
        
        # 沖縄の海を楽しむおすすめスポットスレッド
        {
            "id": str(uuid.uuid4()),
            "thread_id": thread_ids[2],
            "sender_user_id": user_ids["hyrax@example.com"],
            "content": "沖縄旅行で海を楽しめるおすすめスポットを教えてください！シュノーケリングやダイビングに興味があります。",
            "timestamp": datetime.now(JST) - timedelta(hours=5),
            "message_type": "text"
        },
        {
            "id": str(uuid.uuid4()),
            "thread_id": thread_ids[2],
            "sender_user_id": user_ids["rakuda@example.com"],
            "content": "沖縄本島なら青の洞窟が有名ですよ！透明度が高く、魚も多いのでシュノーケリング初心者でも楽しめます。",
            "timestamp": datetime.now(JST) - timedelta(hours=4, minutes=45),
            "message_type": "text"
        },
        {
            "id": str(uuid.uuid4()),
            "thread_id": thread_ids[2],
            "sender_user_id": user_ids["test@example.com"],
            "content": "慶良間諸島も絶対おすすめ！特に渡嘉敷島は「ケラマブルー」と呼ばれる美しい海の色が見られます。",
            "timestamp": datetime.now(JST) - timedelta(hours=4, minutes=30),
            "message_type": "text"
        },
        {
            "id": str(uuid.uuid4()),
            "thread_id": thread_ids[2],
            "sender_user_id": user_ids["yamada@example.com"],
            "content": "宮古島の与那覇前浜ビーチも透明度抜群！シュノーケリングだけでなく、ただ海を眺めているだけでも癒されます。",
            "timestamp": datetime.now(JST) - timedelta(hours=4, minutes=15),
            "message_type": "text"
        },
        {
            "id": str(uuid.uuid4()),
            "thread_id": thread_ids[2],
            "sender_user_id": user_ids["hyrax@example.com"],
            "content": "みなさんありがとうございます！ダイビングは初心者なのですが、初心者向けのダイビングスポットはありますか？",
            "timestamp": datetime.now(JST) - timedelta(hours=4),
            "message_type": "text"
        },
        {
            "id": str(uuid.uuid4()),
            "thread_id": thread_ids[2],
            "sender_user_id": user_ids["tanaka@example.com"],
            "content": "真栄田岬（まえだみさき）は初心者向けのダイビングスクールがたくさんあります。青の洞窟に潜るツアーもありますよ。",
            "timestamp": datetime.now(JST) - timedelta(hours=3, minutes=50),
            "message_type": "text"
        },
        {
            "id": str(uuid.uuid4()),
            "thread_id": thread_ids[2],
            "sender_user_id": user_ids["tonakai@example.com"],
            "content": "恩納村のビーチも初心者向け。サンゴや熱帯魚がたくさん見られて、浅いところからでも楽しめます。",
            "timestamp": datetime.now(JST) - timedelta(hours=3, minutes=40),
            "message_type": "text"
        },
        {
            "id": str(uuid.uuid4()),
            "thread_id": thread_ids[2],
            "sender_user_id": user_ids["uma@example.com"],
            "content": "水納島は浅瀬でも色とりどりの魚が見られます。島自体も小さくて素朴な雰囲気が素敵ですよ。",
            "timestamp": datetime.now(JST) - timedelta(hours=3, minutes=30),
            "message_type": "text"
        },
        {
            "id": str(uuid.uuid4()),
            "thread_id": thread_ids[2],
            "sender_user_id": user_ids["hyrax@example.com"],
            "content": "真栄田岬、恩納村、水納島...全部行ってみたいですね！沖縄に何日くらい滞在するのがベストでしょうか？",
            "timestamp": datetime.now(JST) - timedelta(hours=3, minutes=20),
            "message_type": "text"
        },
        {
            "id": str(uuid.uuid4()),
            "thread_id": thread_ids[2],
            "sender_user_id": user_ids["okojo@example.com"],
            "content": "本島だけなら最低3日、離島も回るなら5日以上はほしいですね。移動に時間がかかることも考慮した方がいいです。",
            "timestamp": datetime.now(JST) - timedelta(hours=3, minutes=10),
            "message_type": "text"
        },
        {
            "id": str(uuid.uuid4()),
            "thread_id": thread_ids[2],
            "sender_user_id": user_ids["niwatori@example.com"],
            "content": "沖縄は早朝の海も美しいので、朝活もおすすめ。日の出とともに海に出ると、また違った景色が見られますよ。",
            "timestamp": datetime.now(JST) - timedelta(hours=3),
            "message_type": "text"
        },
        {
            "id": str(uuid.uuid4()),
            "thread_id": thread_ids[2],
            "sender_user_id": user_ids["tanaka@example.com"],
            "content": "シュノーケリングやダイビング以外なら、グラスボートもおすすめです。濡れずに海の中を観察できるので、海が苦手な人も楽しめます。",
            "timestamp": datetime.now(JST) - timedelta(hours=2, minutes=50),
            "message_type": "text"
        },
        {
            "id": str(uuid.uuid4()),
            "thread_id": thread_ids[2],
            "sender_user_id": user_ids["sheep@example.com"],
            "content": "沖縄の海は紫外線が強いので、日焼け止めは必須です。できれば環境に優しい日焼け止めを使いましょう。サンゴに悪影響を与えないためです。",
            "timestamp": datetime.now(JST) - timedelta(hours=2, minutes=40),
            "message_type": "text"
        },
        {
            "id": str(uuid.uuid4()),
            "thread_id": thread_ids[2],
            "sender_user_id": user_ids["hamster@example.com"],
            "content": "ダイビングの後は沖縄の海鮮料理もおすすめ！特に地元の居酒屋で食べる海ぶどうや島豆腐、ソーキそばは絶品です。",
            "timestamp": datetime.now(JST) - timedelta(hours=2, minutes=30),
            "message_type": "text"
        },
        {
            "id": str(uuid.uuid4()),
            "thread_id": thread_ids[2],
            "sender_user_id": user_ids["hyrax@example.com"],
            "content": "みなさん本当にありがとうございます！これだけ情報があると沖縄が楽しみになってきました。まずは5日間の予定で計画を立ててみます。環境に優しい日焼け止めも準備します！",
            "timestamp": datetime.now(JST) - timedelta(hours=2, minutes=20),
            "message_type": "text"
        },
        {
            "id": str(uuid.uuid4()),
            "thread_id": thread_ids[2],
            "sender_user_id": user_ids["rakuda@example.com"],
            "content": "沖縄の天気は変わりやすいので、余裕を持ったスケジュールがおすすめです。マリンアクティビティは晴れの日に集中させると良いですよ。",
            "timestamp": datetime.now(JST) - timedelta(hours=2, minutes=10),
            "message_type": "text"
        },
        {
            "id": str(uuid.uuid4()),
            "thread_id": thread_ids[2],
            "sender_user_id": user_ids["hyrax@example.com"],
            "content": "なるほど！天気予報もこまめにチェックします。本当にありがとうございました！",
            "timestamp": datetime.now(JST) - timedelta(hours=2),
            "message_type": "text"
        }
    ]


    ########
    direct_messages_data=[
        {
            "id": str(uuid.uuid4()),
            "sender_id": user_ids["yamada@example.com"],
            "receiver_id": user_ids["test@example.com"],
            "content": "こんにちは！元気ですよ。今週末に大阪に行く予定です。",
            "sent_at": datetime.now(JST) - timedelta(days=3, hours=4),
            "is_read": True,
            "read_at": datetime.now(JST) - timedelta(days=3, hours=3)
        },
        {
            "id": str(uuid.uuid4()),
            "sender_id": user_ids["test@example.com"],
            "receiver_id": user_ids["yamada@example.com"],
            "content": "大阪いいですね！どこか行くところは決まっていますか？",
            "sent_at": datetime.now(JST) - timedelta(days=3, hours=3),
            "is_read": True,
            "read_at": datetime.now(JST) - timedelta(days=3, hours=2)
        },
        {
            "id": str(uuid.uuid4()),
            "sender_id": user_ids["yamada@example.com"],
            "receiver_id": user_ids["test@example.com"],
            "content": "大阪城と道頓堀に行く予定です。他にもおすすめがあれば教えてください！",
            "sent_at": datetime.now(JST) - timedelta(days=3, hours=2),
            "is_read": True,
            "read_at": datetime.now(JST) - timedelta(days=3, hours=1)
        },
        {
            "id": str(uuid.uuid4()),
            "sender_id": user_ids["test@example.com"],
            "receiver_id": user_ids["yamada@example.com"],
            "content": "通天閣もおすすめですよ！夜景が綺麗です。",
            "sent_at": datetime.now(JST) - timedelta(days=3, hours=1),
            "is_read": True,
            "read_at": datetime.now(JST) - timedelta(days=3)
        },
        {
            "id": str(uuid.uuid4()),
            "sender_id": user_ids["yamada@example.com"],
            "receiver_id": user_ids["test@example.com"],
            "content": "それはいいですね！ぜひ行ってみます。ありがとう！",
            "sent_at": datetime.now(JST) - timedelta(days=3),
            "is_read": True,
            "read_at": datetime.now(JST) - timedelta(days=2, hours=23)
        },
        
        # uma@example.comとokojo@example.comのDM（動物ユーザー同士）
        {
            "id": str(uuid.uuid4()),
            "sender_id": user_ids["uma@example.com"],
            "receiver_id": user_ids["okojo@example.com"],
            "content": "オコジョさん、北海道の山岳地帯はどうですか？",
            "sent_at": datetime.now(JST) - timedelta(days=1, hours=10),
            "is_read": True,
            "read_at": datetime.now(JST) - timedelta(days=1, hours=9)
        },
        {
            "id": str(uuid.uuid4()),
            "sender_id": user_ids["okojo@example.com"],
            "receiver_id": user_ids["uma@example.com"],
            "content": "とても素晴らしいですよ！特に大雪山は絶景です。",
            "sent_at": datetime.now(JST) - timedelta(days=1, hours=9),
            "is_read": True,
            "read_at": datetime.now(JST) - timedelta(days=1, hours=8)
        },
        {
            "id": str(uuid.uuid4()),
            "sender_id": user_ids["uma@example.com"],
            "receiver_id": user_ids["okojo@example.com"],
            "content": "今度一緒に山登りツアーを企画しませんか？",
            "sent_at": datetime.now(JST) - timedelta(days=1, hours=8),
            "is_read": True,
            "read_at": datetime.now(JST) - timedelta(days=1, hours=7)
        },
        {
            "id": str(uuid.uuid4()),
            "sender_id": user_ids["okojo@example.com"],
            "receiver_id": user_ids["uma@example.com"],
            "content": "それは素晴らしいアイデアです！私がガイドしますよ。",
            "sent_at": datetime.now(JST) - timedelta(days=1, hours=7),
            "is_read": True,
            "read_at": datetime.now(JST) - timedelta(days=1, hours=6)
        },
        {
            "id": str(uuid.uuid4()),
            "sender_id": user_ids["uma@example.com"],
            "receiver_id": user_ids["okojo@example.com"],
            "content": "ありがとう！来月の第一週はどうでしょうか？",
            "sent_at": datetime.now(JST) - timedelta(days=1, hours=6),
            "is_read": True,
            "read_at": datetime.now(JST) - timedelta(days=1, hours=5)
        },
        {
            "id": str(uuid.uuid4()),
            "sender_id": user_ids["okojo@example.com"],
            "receiver_id": user_ids["uma@example.com"],
            "content": "その時期は雪が少なくて最適です！では計画を立てましょう。",
            "sent_at": datetime.now(JST) - timedelta(days=1, hours=5),
            "is_read": True,
            "read_at": datetime.now(JST) - timedelta(days=1, hours=4)
        },
        
        # tonakai@example.comとniwatori@example.comのDM（動物ユーザー同士）
        {
            "id": str(uuid.uuid4()),
            "sender_id": user_ids["tonakai@example.com"],
            "receiver_id": user_ids["niwatori@example.com"],
            "content": "鶏さん、朝早く起きるコツはありますか？",
            "sent_at": datetime.now(JST) - timedelta(hours=36),
            "is_read": True,
            "read_at": datetime.now(JST) - timedelta(hours=35)
        },
        {
            "id": str(uuid.uuid4()),
            "sender_id": user_ids["niwatori@example.com"],
            "receiver_id": user_ids["tonakai@example.com"],
            "content": "朝日と一緒に起きるのが自然なリズムですよ！早寝も大事です。",
            "sent_at": datetime.now(JST) - timedelta(hours=35),
            "is_read": True,
            "read_at": datetime.now(JST) - timedelta(hours=34)
        },
        {
            "id": str(uuid.uuid4()),
            "sender_id": user_ids["tonakai@example.com"],
            "receiver_id": user_ids["niwatori@example.com"],
            "content": "なるほど！クリスマスシーズンが近づいていて忙しくなりそうなので、効率的に過ごしたいんです。",
            "sent_at": datetime.now(JST) - timedelta(hours=34),
            "is_read": True,
            "read_at": datetime.now(JST) - timedelta(hours=33)
        },
        {
            "id": str(uuid.uuid4()),
            "sender_id": user_ids["niwatori@example.com"],
            "receiver_id": user_ids["tonakai@example.com"],
            "content": "朝ヨガも効果的ですよ！早朝サンライズヨガツアーに参加しませんか？",
            "sent_at": datetime.now(JST) - timedelta(hours=33),
            "is_read": True,
            "read_at": datetime.now(JST) - timedelta(hours=32)
        },
        {
            "id": str(uuid.uuid4()),
            "sender_id": user_ids["tonakai@example.com"],
            "receiver_id": user_ids["niwatori@example.com"],
            "content": "それはいいですね！参加したいです。詳細を教えてください。",
            "sent_at": datetime.now(JST) - timedelta(hours=32),
            "is_read": True,
            "read_at": datetime.now(JST) - timedelta(hours=31)
        },
        
        # hyrax@example.comとhamster@example.comのDM（動物ユーザー同士）
        {
            "id": str(uuid.uuid4()),
            "sender_id": user_ids["hyrax@example.com"],
            "receiver_id": user_ids["hamster@example.com"],
            "content": "ハムスターさん、明日の沖縄の天気を知っていますか？",
            "sent_at": datetime.now(JST) - timedelta(hours=28),
            "is_read": True,
            "read_at": datetime.now(JST) - timedelta(hours=27)
        },
        {
            "id": str(uuid.uuid4()),
            "sender_id": user_ids["hamster@example.com"],
            "receiver_id": user_ids["hyrax@example.com"],
            "content": "天気予報を見たら、晴れの予定ですよ！岩場でのピクニックにぴったりです。",
            "sent_at": datetime.now(JST) - timedelta(hours=27),
            "is_read": True,
            "read_at": datetime.now(JST) - timedelta(hours=26)
        },
        {
            "id": str(uuid.uuid4()),
            "sender_id": user_ids["hyrax@example.com"],
            "receiver_id": user_ids["hamster@example.com"],
            "content": "それは良かった！ピクニックに必要な種や木の実を集めてきてもらえますか？",
            "sent_at": datetime.now(JST) - timedelta(hours=26),
            "is_read": True,
            "read_at": datetime.now(JST) - timedelta(hours=25)
        },
        {
            "id": str(uuid.uuid4()),
            "sender_id": user_ids["hamster@example.com"],
            "receiver_id": user_ids["hyrax@example.com"],
            "content": "了解です！最高の種コレクションを持っていきますね。何か他に必要なものはありますか？",
            "sent_at": datetime.now(JST) - timedelta(hours=25),
            "is_read": True,
            "read_at": datetime.now(JST) - timedelta(hours=24)
        },
        {
            "id": str(uuid.uuid4()),
            "sender_id": user_ids["hyrax@example.com"],
            "receiver_id": user_ids["hamster@example.com"],
            "content": "日よけの大きな葉っぱがあると助かります。あとは私が岩場を確保しておきます！",
            "sent_at": datetime.now(JST) - timedelta(hours=24),
            "is_read": True,
            "read_at": datetime.now(JST) - timedelta(hours=23)
        },
        {
            "id": str(uuid.uuid4()),
            "sender_id": user_ids["hamster@example.com"],
            "receiver_id": user_ids["hyrax@example.com"],
            "content": "了解です！明日が楽しみですね！",
            "sent_at": datetime.now(JST) - timedelta(hours=23),
            "is_read": True,
            "read_at": datetime.now(JST) - timedelta(hours=22)
        },
        
        # rakuda@example.comとsheep@example.comのDM（動物ユーザー同士）
        {
            "id": str(uuid.uuid4()),
            "sender_id": user_ids["rakuda@example.com"],
            "receiver_id": user_ids["sheep@example.com"],
            "content": "羊さん、砂漠で使える編み物はありますか？",
            "sent_at": datetime.now(JST) - timedelta(hours=20),
            "is_read": True,
            "read_at": datetime.now(JST) - timedelta(hours=19)
        },
        {
            "id": str(uuid.uuid4()),
            "sender_id": user_ids["sheep@example.com"],
            "receiver_id": user_ids["rakuda@example.com"],
            "content": "砂漠用の日よけ帽子を編むことができますよ！通気性が良くて日差しをカットできます。",
            "sent_at": datetime.now(JST) - timedelta(hours=19),
            "is_read": True,
            "read_at": datetime.now(JST) - timedelta(hours=18)
        },
        {
            "id": str(uuid.uuid4()),
            "sender_id": user_ids["rakuda@example.com"],
            "receiver_id": user_ids["sheep@example.com"],
            "content": "それはいいですね！砂漠ツアーのお客さんに提供したいと思っています。",
            "sent_at": datetime.now(JST) - timedelta(hours=18),
            "is_read": True,
            "read_at": datetime.now(JST) - timedelta(hours=17)
        },
        {
            "id": str(uuid.uuid4()),
            "sender_id": user_ids["sheep@example.com"],
            "receiver_id": user_ids["rakuda@example.com"],
            "content": "喜んで作りますよ！何個必要ですか？",
            "sent_at": datetime.now(JST) - timedelta(hours=17),
            "is_read": True,
            "read_at": datetime.now(JST) - timedelta(hours=16)
        },
        {
            "id": str(uuid.uuid4()),
            "sender_id": user_ids["rakuda@example.com"],
            "receiver_id": user_ids["sheep@example.com"],
            "content": "ツアー客は10人なので、10個お願いできますか？",
            "sent_at": datetime.now(JST) - timedelta(hours=16),
            "is_read": True,
            "read_at": datetime.now(JST) - timedelta(hours=15)
        },
        {
            "id": str(uuid.uuid4()),
            "sender_id": user_ids["sheep@example.com"],
            "receiver_id": user_ids["rakuda@example.com"],
            "content": "了解しました！来週のワークショップで作成しますね。完成したらご連絡します。",
            "sent_at": datetime.now(JST) - timedelta(hours=15),
            "is_read": True,
            "read_at": datetime.now(JST) - timedelta(hours=14)
        },
        
        # test@example.comとuma@example.com（未読メッセージ）
        {
            "id": str(uuid.uuid4()),
            "sender_id": user_ids["test@example.com"],
            "receiver_id": user_ids["uma@example.com"],
            "content": "馬さん、乗馬体験ツアーについて質問があります。",
            "sent_at": datetime.now(JST) - timedelta(hours=5),
            "is_read": False,
            "read_at": None
        },
        {
            "id": str(uuid.uuid4()),
            "sender_id": user_ids["test@example.com"],
            "receiver_id": user_ids["uma@example.com"],
            "content": "初心者でも参加できますか？馬に乗った経験がないのですが大丈夫ですか？",
            "sent_at": datetime.now(JST) - timedelta(hours=4),
            "is_read": False,
            "read_at": None
        },
        
        # tanaka@example.comとokojo@example.com（未読メッセージ）
        {
            "id": str(uuid.uuid4()),
            "sender_id": user_ids["tanaka@example.com"],
            "receiver_id": user_ids["okojo@example.com"],
            "content": "山岳トレッキングの写真を撮りたいのですが、おすすめのスポットはありますか？",
            "sent_at": datetime.now(JST) - timedelta(hours=3),
            "is_read": False,
            "read_at": None
        },
        
        # yamada@example.comとniwatori@example.com（未読メッセージ）
        {
            "id": str(uuid.uuid4()),
            "sender_id": user_ids["yamada@example.com"],
            "receiver_id": user_ids["niwatori@example.com"],
            "content": "早朝サンライズヨガはどこで開催されますか？参加したいです。",
            "sent_at": datetime.now(JST) - timedelta(hours=2),
            "is_read": False,
            "read_at": None
        },
        {
            "id": str(uuid.uuid4()),
            "sender_id": user_ids["yamada@example.com"],
            "receiver_id": user_ids["niwatori@example.com"],
            "content": "また、持っていくものはありますか？",
            "sent_at": datetime.now(JST) - timedelta(hours=1),
            "is_read": False,
            "read_at": None
        },
        # test@example.comとtanaka@example.comのDM
        
        {
            "id": str(uuid.uuid4()),
            "sender_id": user_ids["test@example.com"],
            "receiver_id": user_ids["tanaka@example.com"],
            "content": "田中さん、こんにちは！明日の京都紅葉撮影会について質問があります。",
            "sent_at": datetime.now(JST) - timedelta(hours=48),
            "is_read": True,
            "read_at": datetime.now(JST) - timedelta(hours=47)
        }
    ]
    
    for message_data in direct_messages_data:
        direct_message = DirectMessage(
            id=message_data["id"],
            sender_id=message_data["sender_id"],
            receiver_id=message_data["receiver_id"],
            content=message_data["content"],
            sent_at=message_data["sent_at"],
            is_read=message_data["is_read"],
            read_at=message_data["read_at"],
            message_type="text"
        )
        db.session.add(direct_message)
    
    db.session.commit()
    print("✅ ダイレクトメッセージを追加しました")
    # スレッドメッセージをデータベースに追加
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
                
        # 岩場でのんびりピクニックのメッセージ
        {
            "id": str(uuid.uuid4()),
            "event_id": event_ids[10],
            "sender_user_id": user_ids["hyrax@example.com"],
            "content": "岩場でのんびりピクニックへようこそ！沖縄の美しい岩場で、ゆったりとした時間を過ごしましょう。",
            "timestamp": datetime.now(JST) - timedelta(days=5, hours=10),
            "message_type": "text"
        },
        {
            "id": str(uuid.uuid4()),
            "event_id": event_ids[10],
            "sender_user_id": user_ids["hyrax@example.com"],
            "content": "集合場所は那覇市の「美ら海バス停」、9月20日朝10時です。そこから専用車で30分ほど移動します。",
            "timestamp": datetime.now(JST) - timedelta(days=5, hours=9, minutes=45),
            "message_type": "text"
        },
        {
            "id": str(uuid.uuid4()),
            "event_id": event_ids[10],
            "sender_user_id": user_ids["hamster@example.com"],
            "content": "楽しみにしています！持っていくべきものはありますか？",
            "timestamp": datetime.now(JST) - timedelta(days=5, hours=9, minutes=30),
            "message_type": "text"
        },
        {
            "id": str(uuid.uuid4()),
            "event_id": event_ids[10],
            "sender_user_id": user_ids["hyrax@example.com"],
            "content": "水着、タオル、日焼け止め、帽子、サングラス、着替えをお持ちください。ランチとドリンクは私が用意します。",
            "timestamp": datetime.now(JST) - timedelta(days=5, hours=9),
            "message_type": "text"
        },
        {
            "id": str(uuid.uuid4()),
            "event_id": event_ids[10],
            "sender_user_id": user_ids["rakuda@example.com"],
            "content": "泳ぐことはできますか？",
            "timestamp": datetime.now(JST) - timedelta(days=4, hours=15),
            "message_type": "text"
        },
        {
            "id": str(uuid.uuid4()),
            "event_id": event_ids[10],
            "sender_user_id": user_ids["hyrax@example.com"],
            "content": "岩場の下には小さなプライベートビーチがあり、そこで泳げます。波も穏やかで透明度抜群の海です！",
            "timestamp": datetime.now(JST) - timedelta(days=4, hours=14, minutes=45),
            "message_type": "text"
        },
        {
            "id": str(uuid.uuid4()),
            "event_id": event_ids[10],
            "sender_user_id": user_ids["tonakai@example.com"],
            "content": "ランチはどんなメニューですか？アレルギーがあるので確認したいです。",
            "timestamp": datetime.now(JST) - timedelta(days=3, hours=18),
            "message_type": "text"
        },
        {
            "id": str(uuid.uuid4()),
            "event_id": event_ids[10],
            "sender_user_id": user_ids["hyrax@example.com"],
            "content": "沖縄風おにぎり、フルーツ、ケーキを予定しています。アレルギーについて詳しく教えていただければ対応します。",
            "timestamp": datetime.now(JST) - timedelta(days=3, hours=17, minutes=30),
            "message_type": "text"
        },
        {
            "id": str(uuid.uuid4()),
            "event_id": event_ids[10],
            "sender_user_id": user_ids["tonakai@example.com"],
            "content": "ナッツアレルギーがあります。ケーキにナッツが入っていなければ大丈夫です。",
            "timestamp": datetime.now(JST) - timedelta(days=3, hours=17),
            "message_type": "text"
        },
        {
            "id": str(uuid.uuid4()),
            "event_id": event_ids[10],
            "sender_user_id": user_ids["hyrax@example.com"],
            "content": "了解しました！ナッツは使わないようにします。他にアレルギーがある方はいますか？",
            "timestamp": datetime.now(JST) - timedelta(days=3, hours=16, minutes=45),
            "message_type": "text"
        },
        {
            "id": str(uuid.uuid4()),
            "event_id": event_ids[10],
            "sender_user_id": user_ids["hyrax@example.com"],
            "content": "明日の天気予報は晴れです！絶好のピクニック日和になりそうです。熱中症に気をつけて、水分をたくさん持ってきてくださいね。",
            "timestamp": datetime.now(JST) - timedelta(days=1, hours=16),
            "message_type": "text"
        },
        {
            "id": str(uuid.uuid4()),
            "event_id": event_ids[10],
            "sender_user_id": user_ids["hamster@example.com"],
            "content": "楽しみです！明日10時に美ら海バス停で会いましょう！",
            "timestamp": datetime.now(JST) - timedelta(days=1, hours=15, minutes=30),
            "message_type": "text"
        },
        
        # 種集めウォーキングのメッセージ
        {
            "id": str(uuid.uuid4()),
            "event_id": event_ids[11],
            "sender_user_id": user_ids["hamster@example.com"],
            "content": "種集めウォーキングへようこそ！様々な植物の種を集めながら自然を楽しむイベントです。",
            "timestamp": datetime.now(JST) - timedelta(days=7, hours=14),
            "message_type": "text"
        },
        {
            "id": str(uuid.uuid4()),
            "event_id": event_ids[11],
            "sender_user_id": user_ids["hamster@example.com"],
            "content": "集合は井の頭公園の西口、10月10日朝9時です。",
            "timestamp": datetime.now(JST) - timedelta(days=7, hours=13, minutes=45),
            "message_type": "text"
        },
        {
            "id": str(uuid.uuid4()),
            "event_id": event_ids[11],
            "sender_user_id": user_ids["niwatori@example.com"],
            "content": "楽しみにしています！どんな種類の種を集める予定ですか？",
            "timestamp": datetime.now(JST) - timedelta(days=7, hours=13),
            "message_type": "text"
        },
        {
            "id": str(uuid.uuid4()),
            "event_id": event_ids[11],
            "sender_user_id": user_ids["hamster@example.com"],
            "content": "主に松ぼっくり、どんぐり、イチョウの実、モミジの種などの木の実や、タンポポやオナモミなどの野草の種を集める予定です。",
            "timestamp": datetime.now(JST) - timedelta(days=7, hours=12, minutes=30),
            "message_type": "text"
        },
        {
            "id": str(uuid.uuid4()),
            "event_id": event_ids[11],
            "sender_user_id": user_ids["tonakai@example.com"],
            "content": "持っていくべきものはありますか？",
            "timestamp": datetime.now(JST) - timedelta(days=6, hours=19),
            "message_type": "text"
        },
        {
            "id": str(uuid.uuid4()),
            "event_id": event_ids[11],
            "sender_user_id": user_ids["hamster@example.com"],
            "content": "小さな袋やポケットのあるエプロン、軍手、ピンセット（あれば）、帽子、水筒をお持ちください。カメラもあるといいですよ！",
            "timestamp": datetime.now(JST) - timedelta(days=6, hours=18, minutes=30),
            "message_type": "text"
        },
        {
            "id": str(uuid.uuid4()),
            "event_id": event_ids[11],
            "sender_user_id": user_ids["hyrax@example.com"],
            "content": "集めた種は持ち帰れますか？",
            "timestamp": datetime.now(JST) - timedelta(days=5, hours=14),
            "message_type": "text"
        },
        {
            "id": str(uuid.uuid4()),
            "event_id": event_ids[11],
            "sender_user_id": user_ids["hamster@example.com"],
            "content": "はい、持ち帰れます！ご家庭で植えたり、クラフト材料にしたりできます。ワークショップの後半では、集めた種でミニリースを作る予定です。",
            "timestamp": datetime.now(JST) - timedelta(days=5, hours=13, minutes=30),
            "message_type": "text"
        },
        {
            "id": str(uuid.uuid4()),
            "event_id": event_ids[11],
            "sender_user_id": user_ids["niwatori@example.com"],
            "content": "歩く距離はどれくらいですか？",
            "timestamp": datetime.now(JST) - timedelta(days=3, hours=11),
            "message_type": "text"
        },
        {
            "id": str(uuid.uuid4()),
            "event_id": event_ids[11],
            "sender_user_id": user_ids["hamster@example.com"],
            "content": "約3kmのコースです。ゆっくり歩いて種を見つけながら、約2時間かけて回ります。アップダウンは少ないので、どなたでも参加しやすいコースです。",
            "timestamp": datetime.now(JST) - timedelta(days=3, hours=10, minutes=45),
            "message_type": "text"
        },
        {
            "id": str(uuid.uuid4()),
            "event_id": event_ids[11],
            "sender_user_id": user_ids["hamster@example.com"],
            "content": "ランチは各自ご持参いただくか、公園内のカフェをご利用ください。13時頃に一度集まって、午後はクラフトタイムにします。",
            "timestamp": datetime.now(JST) - timedelta(days=3, hours=10, minutes=30),
            "message_type": "text"
        },
        {
            "id": str(uuid.uuid4()),
            "event_id": event_ids[11],
            "sender_user_id": user_ids["hamster@example.com"],
            "content": "明日の天気予報は晴れです！秋晴れの下、素敵な種集めができそうです。9時に井の頭公園西口でお待ちしています！",
            "timestamp": datetime.now(JST) - timedelta(days=1, hours=17),
            "message_type": "text"
        },
        
        # 砂漠ツアーガイドのメッセージ
        {
            "id": str(uuid.uuid4()),
            "event_id": event_ids[12],
            "sender_user_id": user_ids["rakuda@example.com"],
            "content": "砂漠ツアーガイドへようこそ！沖縄の美しい砂浜を砂漠に見立てた特別なツアーです。",
            "timestamp": datetime.now(JST) - timedelta(days=6, hours=13),
            "message_type": "text"
        },
        {
            "id": str(uuid.uuid4()),
            "event_id": event_ids[12],
            "sender_user_id": user_ids["rakuda@example.com"],
            "content": "集合場所は那覇空港1階到着ロビー、11月15日14時です。そこからバスで約1時間、与那覇前浜ビーチに向かいます。",
            "timestamp": datetime.now(JST) - timedelta(days=6, hours=12, minutes=45),
            "message_type": "text"
        },
        {
            "id": str(uuid.uuid4()),
            "event_id": event_ids[12],
            "sender_user_id": user_ids["hyrax@example.com"],
            "content": "楽しみにしています！ラクダに実際に乗れるのですか？",
            "timestamp": datetime.now(JST) - timedelta(days=6, hours=12, minutes=30),
            "message_type": "text"
        },
        {
            "id": str(uuid.uuid4()),
            "event_id": event_ids[12],
            "sender_user_id": user_ids["rakuda@example.com"],
            "content": "はい！特別にアラビアから輸入したラクダが2頭います。交代で乗っていただけます。砂浜を約15分間、本格的な砂漠気分を味わえますよ。",
            "timestamp": datetime.now(JST) - timedelta(days=6, hours=12),
            "message_type": "text"
        },
        {
            "id": str(uuid.uuid4()),
            "event_id": event_ids[12],
            "sender_user_id": user_ids["sheep@example.com"],
            "content": "持っていくべきものを教えてください！",
            "timestamp": datetime.now(JST) - timedelta(days=5, hours=18),
            "message_type": "text"
        },
        {
            "id": str(uuid.uuid4()),
            "event_id": event_ids[12],
            "sender_user_id": user_ids["rakuda@example.com"],
            "content": "日焼け止め、サングラス、帽子、タオル、着替え（砂で汚れる可能性あり）、水筒をお持ちください。アラビアンな雰囲気の服装だと写真映えしますよ！",
            "timestamp": datetime.now(JST) - timedelta(days=5, hours=17, minutes=30),
            "message_type": "text"
        },
        {
            "id": str(uuid.uuid4()),
            "event_id": event_ids[12],
            "sender_user_id": user_ids["hamster@example.com"],
            "content": "ラクダ以外にどんなアクティビティがありますか？",
            "timestamp": datetime.now(JST) - timedelta(days=5, hours=17),
            "message_type": "text"
        },
        {
            "id": str(uuid.uuid4()),
            "event_id": event_ids[12],
            "sender_user_id": user_ids["rakuda@example.com"],
            "content": "砂漠のオアシス風のテントでのアラビアンティータイム、砂絵作り体験、アラビア料理の試食会、そして日没時には砂丘でのミニコンサートを予定しています！",
            "timestamp": datetime.now(JST) - timedelta(days=5, hours=16, minutes=45),
            "message_type": "text"
        },
        {
            "id": str(uuid.uuid4()),
            "event_id": event_ids[12],
            "sender_user_id": user_ids["tonakai@example.com"],
            "content": "何時頃終了する予定ですか？",
            "timestamp": datetime.now(JST) - timedelta(days=4, hours=11),
            "message_type": "text"
        },
        {
            "id": str(uuid.uuid4()),
            "event_id": event_ids[12],
            "sender_user_id": user_ids["rakuda@example.com"],
            "content": "日没後の19時頃を予定しています。那覇市内まで送迎バスがありますので、ご安心ください。",
            "timestamp": datetime.now(JST) - timedelta(days=4, hours=10, minutes=30),
            "message_type": "text"
        },
        {
            "id": str(uuid.uuid4()),
            "event_id": event_ids[12],
            "sender_user_id": user_ids["uma@example.com"],
            "content": "子供連れでも参加できますか？",
            "timestamp": datetime.now(JST) - timedelta(days=3, hours=14),
            "message_type": "text"
        },
        {
            "id": str(uuid.uuid4()),
            "event_id": event_ids[12],
            "sender_user_id": user_ids["rakuda@example.com"],
            "content": "小学生以上のお子様であれば問題ありません。保護者同伴でお願いします。お子様用の砂遊びセットも用意しています。",
            "timestamp": datetime.now(JST) - timedelta(days=3, hours=13, minutes=30),
            "message_type": "text"
        },
        {
            "id": str(uuid.uuid4()),
            "event_id": event_ids[12],
            "sender_user_id": user_ids["rakuda@example.com"],
            "content": "明日の天気予報は晴れ。絶好の砂漠ツアー日和になりそうです！14時に那覇空港でお待ちしています。",
            "timestamp": datetime.now(JST) - timedelta(days=1, hours=15),
            "message_type": "text"
        },
        
        # 編み物ワークショップのメッセージ
        {
            "id": str(uuid.uuid4()),
            "event_id": event_ids[13],
            "sender_user_id": user_ids["sheep@example.com"],
            "content": "編み物ワークショップへようこそ！温かな毛糸で冬の小物を作りましょう。",
            "timestamp": datetime.now(JST) - timedelta(days=7, hours=15),
            "message_type": "text"
        },
        {
            "id": str(uuid.uuid4()),
            "event_id": event_ids[13],
            "sender_user_id": user_ids["sheep@example.com"],
            "content": "開催場所は札幌市中央区のカフェ「ウールタイム」、日程は12月5日13時からです。",
            "timestamp": datetime.now(JST) - timedelta(days=7, hours=14, minutes=45),
            "message_type": "text"
        },
        {
            "id": str(uuid.uuid4()),
            "event_id": event_ids[13],
            "sender_user_id": user_ids["tonakai@example.com"],
            "content": "楽しみにしています！初心者でも参加できますか？",
            "timestamp": datetime.now(JST) - timedelta(days=7, hours=14, minutes=30),
            "message_type": "text"
        },
        {
            "id": str(uuid.uuid4()),
            "event_id": event_ids[13],
            "sender_user_id": user_ids["sheep@example.com"],
            "content": "もちろん！今回は初心者向けのワークショップです。かぎ針編みの基本から丁寧にお教えします。",
            "timestamp": datetime.now(JST) - timedelta(days=7, hours=14),
            "message_type": "text"
        },
        {
            "id": str(uuid.uuid4()),
            "event_id": event_ids[13],
            "sender_user_id": user_ids["okojo@example.com"],
            "content": "何を作る予定ですか？",
            "timestamp": datetime.now(JST) - timedelta(days=6, hours=19),
            "message_type": "text"
        },
        {
            "id": str(uuid.uuid4()),
            "event_id": event_ids[13],
            "sender_user_id": user_ids["sheep@example.com"],
            "content": "温かなマフラーか帽子を作ります。初心者の方はマフラー、少し経験のある方は帽子にチャレンジしていただけます。色は数種類からお選びいただけます。",
            "timestamp": datetime.now(JST) - timedelta(days=6, hours=18, minutes=30),
            "message_type": "text"
        },
        {
            "id": str(uuid.uuid4()),
            "event_id": event_ids[13],
            "sender_user_id": user_ids["uma@example.com"],
            "content": "持っていくものはありますか？",
            "timestamp": datetime.now(JST) - timedelta(days=6, hours=18),
            "message_type": "text"
        },
        {
            "id": str(uuid.uuid4()),
            "event_id": event_ids[13],
            "sender_user_id": user_ids["sheep@example.com"],
            "content": "特に必要ありません。編み針、毛糸、編み図はすべてこちらで用意します。メガネをお使いの方はお持ちください。また、爪が長いと編みにくい場合があるので、短めにしておくと良いでしょう。",
            "timestamp": datetime.now(JST) - timedelta(days=6, hours=17, minutes=45),
            "message_type": "text"
        },
        {
            "id": str(uuid.uuid4()),
            "event_id": event_ids[13],
            "sender_user_id": user_ids["hamster@example.com"],
            "content": "ワークショップの所要時間はどれくらいですか？",
            "timestamp": datetime.now(JST) - timedelta(days=5, hours=14),
            "message_type": "text"
        },
        {
            "id": str(uuid.uuid4()),
            "event_id": event_ids[13],
            "sender_user_id": user_ids["sheep@example.com"],
            "content": "約3時間を予定しています。途中、温かいドリンクとお菓子でティータイムも楽しみましょう。マフラーは当日完成しますが、帽子は仕上げを家でしていただく場合もあります。",
            "timestamp": datetime.now(JST) - timedelta(days=5, hours=13, minutes=30),
            "message_type": "text"
        },
        {
            "id": str(uuid.uuid4()),
            "event_id": event_ids[13],
            "sender_user_id": user_ids["tonakai@example.com"],
            "content": "毛糸の素材はどんなものですか？アレルギーがあるので気になります。",
            "timestamp": datetime.now(JST) - timedelta(days=3, hours=16),
            "message_type": "text"
        },
        {
            "id": str(uuid.uuid4()),
            "event_id": event_ids[13],
            "sender_user_id": user_ids["sheep@example.com"],
            "content": "基本的にメリノウールとアクリルの混紡糸を使用する予定ですが、ウールアレルギーの方には100%アクリル毛糸もご用意しています。ご安心ください。",
            "timestamp": datetime.now(JST) - timedelta(days=3, hours=15, minutes=30),
            "message_type": "text"
        },
        {
            "id": str(uuid.uuid4()),
            "event_id": event_ids[13],
            "sender_user_id": user_ids["sheep@example.com"],
            "content": "明日はいよいよワークショップです！外は雪の予報ですが、暖かいカフェで楽しく編み物しましょう。13時に「ウールタイム」でお待ちしています。",
            "timestamp": datetime.now(JST) - timedelta(days=1, hours=16),
            "message_type": "text"
        },
        
        # 鎌倉散策ツアーのメッセージ
        {
            "id": str(uuid.uuid4()),
            "event_id": event_ids[3],
            "sender_user_id": user_ids["tanaka@example.com"],
            "content": "鎌倉散策ツアーにご参加いただきありがとうございます。JR鎌倉駅の東口に9時集合です。",
            "timestamp": datetime.now(JST) - timedelta(days=5, hours=10),
            "message_type": "text"
        },
        {
            "id": str(uuid.uuid4()),
            "event_id": event_ids[3],
            "sender_user_id": user_ids["test@example.com"],
            "content": "楽しみにしています！カメラは持っていった方が良いですか？",
            "timestamp": datetime.now(JST) - timedelta(days=5, hours=9, minutes=30),
            "message_type": "text"
        },
        {
            "id": str(uuid.uuid4()),
            "event_id": event_ids[3],
            "sender_user_id": user_ids["tanaka@example.com"],
            "content": "ぜひ持ってきてください！鶴岡八幡宮や長谷寺など、写真映えするスポットをたくさん巡る予定です。",
            "timestamp": datetime.now(JST) - timedelta(days=5, hours=9),
            "message_type": "text"
        },
        {
            "id": str(uuid.uuid4()),
            "event_id": event_ids[3],
            "sender_user_id": user_ids["yamada@example.com"],
            "content": "参加します！鎌倉は初めてなので楽しみです。",
            "timestamp": datetime.now(JST) - timedelta(days=4, hours=19),
            "message_type": "text"
        },
        {
            "id": str(uuid.uuid4()),
            "event_id": event_ids[3],
            "sender_user_id": user_ids["tanaka@example.com"],
            "content": "ランチは鎌倉名物「しらす丼」を食べに行く予定です。美味しいお店を予約しておきます。",
            "timestamp": datetime.now(JST) - timedelta(days=4, hours=18, minutes=30),
            "message_type": "text"
        },
        {
            "id": str(uuid.uuid4()),
            "event_id": event_ids[3],
            "sender_user_id": user_ids["hamster@example.com"],
            "content": "しらす丼は初めて食べます！楽しみです。",
            "timestamp": datetime.now(JST) - timedelta(days=4, hours=18),
            "message_type": "text"
        },
        {
            "id": str(uuid.uuid4()),
            "event_id": event_ids[3],
            "sender_user_id": user_ids["tanaka@example.com"],
            "content": "歩きやすい靴でお越しください。鎌倉は坂や階段が多いです。また、水分補給用の飲み物も忘れずに！",
            "timestamp": datetime.now(JST) - timedelta(days=2, hours=10),
            "message_type": "text"
        },
        {
            "id": str(uuid.uuid4()),
            "event_id": event_ids[3],
            "sender_user_id": user_ids["test@example.com"],
            "content": "鎌倉駅周辺で何かおすすめのお土産はありますか？",
            "timestamp": datetime.now(JST) - timedelta(days=2, hours=9, minutes=30),
            "message_type": "text"
        },
        {
            "id": str(uuid.uuid4()),
            "event_id": event_ids[3],
            "sender_user_id": user_ids["tanaka@example.com"],
            "content": "鳩サブレーが定番ですね。小町通りには他にも和菓子やおせんべいなど様々なお店があるので、ツアーの最後に立ち寄る予定です。",
            "timestamp": datetime.now(JST) - timedelta(days=2, hours=9),
            "message_type": "text"
        },
        {
            "id": str(uuid.uuid4()),
            "event_id": event_ids[3],
            "sender_user_id": user_ids["tanaka@example.com"],
            "content": "明日の天気は晴れの予報です。日差しが強いので、帽子や日焼け止めをお持ちいただくと良いでしょう。",
            "timestamp": datetime.now(JST) - timedelta(days=1, hours=20),
            "message_type": "text"
        },
        {
            "id": str(uuid.uuid4()),
            "event_id": event_ids[3],
            "sender_user_id": user_ids["yamada@example.com"],
            "content": "了解しました！準備万端で明日お会いしましょう。",
            "timestamp": datetime.now(JST) - timedelta(days=1, hours=19),
            "message_type": "text"
        },
        
        # 大阪たこ焼きパーティーのメッセージ
        {
            "id": str(uuid.uuid4()),
            "event_id": event_ids[4],
            "sender_user_id": user_ids["yamada@example.com"],
            "content": "大阪たこ焼きパーティーへようこそ！JR大阪駅中央改札口に13時集合です。",
            "timestamp": datetime.now(JST) - timedelta(days=3, hours=16),
            "message_type": "text"
        },
        {
            "id": str(uuid.uuid4()),
            "event_id": event_ids[4],
            "sender_user_id": user_ids["tonakai@example.com"],
            "content": "たこ焼き大好きです！参加します！",
            "timestamp": datetime.now(JST) - timedelta(days=3, hours=15, minutes=30),
            "message_type": "text"
        },
        {
            "id": str(uuid.uuid4()),
            "event_id": event_ids[4],
            "sender_user_id": user_ids["hyrax@example.com"],
            "content": "大阪は初めてなので楽しみです。たこ焼き以外に何かおすすめの食べ物はありますか？",
            "timestamp": datetime.now(JST) - timedelta(days=3, hours=15),
            "message_type": "text"
        },
        {
            "id": str(uuid.uuid4()),
            "event_id": event_ids[4],
            "sender_user_id": user_ids["yamada@example.com"],
            "content": "お好み焼きや串カツも大阪の名物です！時間があれば道頓堀まで足を延ばして食べ歩きもしましょう。",
            "timestamp": datetime.now(JST) - timedelta(days=3, hours=14, minutes=45),
            "message_type": "text"
        },
        {
            "id": str(uuid.uuid4()),
            "event_id": event_ids[4],
            "sender_user_id": user_ids["test@example.com"],
            "content": "たこ焼きは自分たちで焼くのですか？それとも食べに行くだけですか？",
            "timestamp": datetime.now(JST) - timedelta(days=3, hours=14),
            "message_type": "text"
        },
        {
            "id": str(uuid.uuid4()),
            "event_id": event_ids[4],
            "sender_user_id": user_ids["yamada@example.com"],
            "content": "まず有名店「たこ金」でプロの技を見学して食べた後、貸切のたこ焼き教室で自分たちでも焼いてみます！",
            "timestamp": datetime.now(JST) - timedelta(days=3, hours=13, minutes=30),
            "message_type": "text"
        },
        {
            "id": str(uuid.uuid4()),
            "event_id": event_ids[4],
            "sender_user_id": user_ids["niwatori@example.com"],
            "content": "たこ焼き作り初挑戦です！うまく焼けるか心配ですが、楽しみです。",
            "timestamp": datetime.now(JST) - timedelta(days=2, hours=9),
            "message_type": "text"
        },
        {
            "id": str(uuid.uuid4()),
            "event_id": event_ids[4],
            "sender_user_id": user_ids["yamada@example.com"],
            "content": "心配いりません！インストラクターが丁寧に教えてくれますよ。ちなみに、服が汚れる可能性があるので、カジュアルな服装でお越しください。",
            "timestamp": datetime.now(JST) - timedelta(days=2, hours=8, minutes=30),
            "message_type": "text"
        },
        {
            "id": str(uuid.uuid4()),
            "event_id": event_ids[4],
            "sender_user_id": user_ids["tonakai@example.com"],
            "content": "持ち物は何かありますか？",
            "timestamp": datetime.now(JST) - timedelta(days=1, hours=18),
            "message_type": "text"
        },
        {
            "id": str(uuid.uuid4()),
            "event_id": event_ids[4],
            "sender_user_id": user_ids["yamada@example.com"],
            "content": "特に必要なものはありません。エプロンは教室で貸してもらえます。たくさん食べる元気だけお持ちください！",
            "timestamp": datetime.now(JST) - timedelta(days=1, hours=17, minutes=45),
            "message_type": "text"
        },
        {
            "id": str(uuid.uuid4()),
            "event_id": event_ids[4],
            "sender_user_id": user_ids["yamada@example.com"],
            "content": "皆さん、明日が近づいてきました！13時に大阪駅中央改札口でお待ちしています。遅れる場合はご連絡ください。",
            "timestamp": datetime.now(JST) - timedelta(hours=16),
            "message_type": "text"
        },
        
        # 寿司作り体験教室のメッセージ
        {
            "id": str(uuid.uuid4()),
            "event_id": event_ids[5],
            "sender_user_id": user_ids["yamada@example.com"],
            "content": "寿司作り体験教室にご参加いただきありがとうございます！東京・築地近くの料理教室で行います。集合は10時です。",
            "timestamp": datetime.now(JST) - timedelta(days=6, hours=14),
            "message_type": "text"
        },
        {
            "id": str(uuid.uuid4()),
            "event_id": event_ids[5],
            "sender_user_id": user_ids["tanaka@example.com"],
            "content": "寿司作りは初めてですが、挑戦してみたいと思います！楽しみにしています。",
            "timestamp": datetime.now(JST) - timedelta(days=6, hours=13, minutes=30),
            "message_type": "text"
        },
        {
            "id": str(uuid.uuid4()),
            "event_id": event_ids[5],
            "sender_user_id": user_ids["niwatori@example.com"],
            "content": "どんな寿司を作る予定ですか？",
            "timestamp": datetime.now(JST) - timedelta(days=6, hours=13),
            "message_type": "text"
        },
        {
            "id": str(uuid.uuid4()),
            "event_id": event_ids[5],
            "sender_user_id": user_ids["yamada@example.com"],
            "content": "基本的な握り寿司（マグロ、サーモン、エビなど）と巻き寿司（かっぱ巻き、カリフォルニアロール）を作る予定です。",
            "timestamp": datetime.now(JST) - timedelta(days=6, hours=12, minutes=45),
            "message_type": "text"
        },
        {
            "id": str(uuid.uuid4()),
            "event_id": event_ids[5],
            "sender_user_id": user_ids["sheep@example.com"],
            "content": "楽しみです！特別な持ち物はありますか？",
            "timestamp": datetime.now(JST) - timedelta(days=5, hours=19),
            "message_type": "text"
        },
        {
            "id": str(uuid.uuid4()),
            "event_id": event_ids[5],
            "sender_user_id": user_ids["yamada@example.com"],
            "content": "エプロンをお持ちください。また、作った寿司は持ち帰れるので、保冷バッグがあると便利です（なくても教室で紙袋はもらえます）。",
            "timestamp": datetime.now(JST) - timedelta(days=5, hours=18, minutes=30),
            "message_type": "text"
        },
        {
            "id": str(uuid.uuid4()),
            "event_id": event_ids[5],
            "sender_user_id": user_ids["test@example.com"],
            "content": "魚をさばくところからやりますか？",
            "timestamp": datetime.now(JST) - timedelta(days=3, hours=10),
            "message_type": "text"
        },
        {
            "id": str(uuid.uuid4()),
            "event_id": event_ids[5],
            "sender_user_id": user_ids["yamada@example.com"],
            "content": "今回は初心者向けなので、すでに切り身になった状態からスタートします。ただ、寿司職人さんによる魚のさばき方のデモンストレーションは見学できますよ！",
            "timestamp": datetime.now(JST) - timedelta(days=3, hours=9, minutes=45),
            "message_type": "text"
        },
        {
            "id": str(uuid.uuid4()),
            "event_id": event_ids[5],
            "sender_user_id": user_ids["tanaka@example.com"],
            "content": "体験の時間はどれくらいですか？",
            "timestamp": datetime.now(JST) - timedelta(days=3, hours=9, minutes=30),
            "message_type": "text"
        },
        {
            "id": str(uuid.uuid4()),
            "event_id": event_ids[5],
            "sender_user_id": user_ids["yamada@example.com"],
            "content": "約2時間の予定です。10時から12時頃までで、その後希望者は近くの築地場外市場でランチも楽しめます。",
            "timestamp": datetime.now(JST) - timedelta(days=3, hours=9),
            "message_type": "text"
        },
        {
            "id": str(uuid.uuid4()),
            "event_id": event_ids[5],
            "sender_user_id": user_ids["niwatori@example.com"],
            "content": "ランチも参加します！築地で美味しいお寿司を食べるチャンスですね。",
            "timestamp": datetime.now(JST) - timedelta(days=3, hours=8, minutes=45),
            "message_type": "text"
        },
        {
            "id": str(uuid.uuid4()),
            "event_id": event_ids[5],
            "sender_user_id": user_ids["yamada@example.com"],
            "content": "皆さん、明日が楽しみですね！最寄り駅は都営地下鉄「築地駅」です。A3出口から徒歩3分の「築地料理教室」に10時集合でお願いします。",
            "timestamp": datetime.now(JST) - timedelta(days=1, hours=16),
            "message_type": "text"
        },
        # いちご狩りツアーのメッセージ
        {
            "id": str(uuid.uuid4()),
            "event_id": event_ids[0],
            "sender_user_id": user_ids["test@example.com"],
            "content": "いちご狩りの集合場所は東京駅南口です。10時に集合しましょう！",
            "timestamp": datetime.now(JST) - timedelta(days=1, hours=12),
            "message_type": "text"
        },
        {
            "id": str(uuid.uuid4()),
            "event_id": event_ids[0],
            "sender_user_id": user_ids["uma@example.com"],
            "content": "了解しました！楽しみにしています。",
            "timestamp": datetime.now(JST) - timedelta(days=1, hours=11, minutes=30),
            "message_type": "text"
        },
        {
            "id": str(uuid.uuid4()),
            "event_id": event_ids[0],
            "sender_user_id": user_ids["okojo@example.com"],
            "content": "少し遅れるかもしれません。10時15分頃には到着できると思います。",
            "timestamp": datetime.now(JST) - timedelta(days=1, hours=11),
            "message_type": "text"
        },
        {
            "id": str(uuid.uuid4()),
            "event_id": event_ids[0],
            "sender_user_id": user_ids["test@example.com"],
            "content": "大丈夫です！少し待ちますので、気をつけてお越しください。",
            "timestamp": datetime.now(JST) - timedelta(days=1, hours=10, minutes=45),
            "message_type": "text"
        },
        {
            "id": str(uuid.uuid4()),
            "event_id": event_ids[0],
            "sender_user_id": user_ids["tonakai@example.com"],
            "content": "何か持っていくものはありますか？",
            "timestamp": datetime.now(JST) - timedelta(days=1, hours=10, minutes=30),
            "message_type": "text"
        },
        {
            "id": str(uuid.uuid4()),
            "event_id": event_ids[0],
            "sender_user_id": user_ids["test@example.com"],
            "content": "特に必要なものはありませんが、エプロンがあると便利かもしれません。いちごの汁で服が汚れる可能性があります。",
            "timestamp": datetime.now(JST) - timedelta(days=1, hours=10),
            "message_type": "text"
        },
        {
            "id": str(uuid.uuid4()),
            "event_id": event_ids[0],
            "sender_user_id": user_ids["niwatori@example.com"],
            "content": "いちご狩りの後、どこかでランチをする予定はありますか？",
            "timestamp": datetime.now(JST) - timedelta(days=1, hours=9),
            "message_type": "text"
        },
        
        # 東京スカイツリー観光のメッセージ
        {
            "id": str(uuid.uuid4()),
            "event_id": event_ids[1],
            "sender_user_id": user_ids["test@example.com"],
            "content": "東京スカイツリー観光のグループへようこそ！集合は明後日、スカイツリー1階エントランス前で11時です。",
            "timestamp": datetime.now(JST) - timedelta(days=3, hours=15),
            "message_type": "text"
        },
        {
            "id": str(uuid.uuid4()),
            "event_id": event_ids[1],
            "sender_user_id": user_ids["hyrax@example.com"],
            "content": "ありがとうございます！観光後に何か予定はありますか？",
            "timestamp": datetime.now(JST) - timedelta(days=3, hours=14, minutes=30),
            "message_type": "text"
        },
        {
            "id": str(uuid.uuid4()),
            "event_id": event_ids[1],
            "sender_user_id": user_ids["test@example.com"],
            "content": "展望台見学の後、近くの浅草で食事と観光をする予定です。もし他に希望があれば教えてください！",
            "timestamp": datetime.now(JST) - timedelta(days=3, hours=14),
            "message_type": "text"
        },
        
        # 京都紅葉撮影会のメッセージ
        {
            "id": str(uuid.uuid4()),
            "event_id": event_ids[2],
            "sender_user_id": user_ids["tanaka@example.com"],
            "content": "京都紅葉撮影会にご参加いただきありがとうございます。集合場所は京都駅中央口、集合時間は10月15日の朝8時です。",
            "timestamp": datetime.now(JST) - timedelta(days=10, hours=15),
            "message_type": "text"
        },
        {
            "id": str(uuid.uuid4()),
            "event_id": event_ids[2],
            "sender_user_id": user_ids["rakuda@example.com"],
            "content": "参加します！京都の紅葉は初めてなので楽しみです。",
            "timestamp": datetime.now(JST) - timedelta(days=10, hours=14),
            "message_type": "text"
        },
        {
            "id": str(uuid.uuid4()),
            "event_id": event_ids[2],
            "sender_user_id": user_ids["hamster@example.com"],
            "content": "カメラの機種は何を持っていけばいいですか？スマホでも大丈夫ですか？",
            "timestamp": datetime.now(JST) - timedelta(days=9, hours=20),
            "message_type": "text"
        },
        
        # 鎌倉散策ツアーのメッセージ
        {
            "id": str(uuid.uuid4()),
            "event_id": event_ids[3],
            "sender_user_id": user_ids["okojo@example.com"],
            "content": "鎌倉散策ツアーのメンバーの皆さん、こんにちは！集合は鎌倉駅東口、9時です。",
            "timestamp": datetime.now(JST) - timedelta(days=5, hours=9),
            "message_type": "text"
        },
        {
            "id": str(uuid.uuid4()),
            "event_id": event_ids[3],
            "sender_user_id": user_ids["yamada@example.com"],
            "content": "楽しみにしています！鎌倉には初めて行きます。",
            "timestamp": datetime.now(JST) - timedelta(days=5, hours=8, minutes=30),
            "message_type": "text"
        },
        
        # 大阪たこ焼きパーティーのメッセージ
        {
            "id": str(uuid.uuid4()),
            "event_id": event_ids[4],
            "sender_user_id": user_ids["yamada@example.com"],
            "content": "たこ焼きパーティーは大阪駅前のたこ焼き屋「たこ金」で行います。",
            "timestamp": datetime.now(JST) - timedelta(days=3, hours=6),
            "message_type": "text"
        },
        {
            "id": str(uuid.uuid4()),
            "event_id": event_ids[4],
            "sender_user_id": user_ids["tonakai@example.com"],
            "content": "楽しみです！大阪のたこ焼きは絶品ですよね。",
            "timestamp": datetime.now(JST) - timedelta(days=3, hours=5, minutes=45),
            "message_type": "text"
        },
        
        # 乗馬体験ツアーのメッセージ
        {
            "id": str(uuid.uuid4()),
            "event_id": event_ids[6],
            "sender_user_id": user_ids["uma@example.com"],
            "content": "乗馬体験ツアーへの参加ありがとうございます。北海道の大自然の中で馬との触れ合いを楽しみましょう！",
            "timestamp": datetime.now(JST) - timedelta(days=7, hours=9),
            "message_type": "text"
        },
        {
            "id": str(uuid.uuid4()),
            "event_id": event_ids[6],
            "sender_user_id": user_ids["uma@example.com"],
            "content": "集合場所は帯広駅北口、時間は9月10日の午前9時です。牧場まではバスで30分ほどかかります。",
            "timestamp": datetime.now(JST) - timedelta(days=7, hours=8, minutes=45),
            "message_type": "text"
        }
    ]
    
    # イベントメッセージをデータベースに追加
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
    
    # キャラクターデータを作成
    characters = [
        {
            "id": "hitsuji",
            "name": "ひつじのひつじ",
            "description": "おっとりした羊のキャラクター",
            "personality": "おっとりしていて優しい聞き役タイプ。相手の話をじっくり受け止めてくれる。",
            "speech_pattern": "「うんうん、わかるよ〜」「それって、すごく大事な気持ちだと思うなぁ」",
            "interests": "悩み相談、思い出話、じんわりくる話",
            "traits": "話すのが苦手な人も安心して心を開ける存在。静かな夜や移動中に活躍。",
            "favorite_trip": "のんびり自然に癒されるリトリート旅",
            "image_file": "執事のひつじ.png"
        },
        {
            "id": "toraberu",
            "name": "トラベル",
            "description": "冒険好きなトラのキャラクター",
            "personality": "エネルギッシュで冒険好き。アイデアマンで、次の行き先を提案するのが得意。",
            "speech_pattern": "「行ってみようぜ！絶対楽しいって！」「オレが前行ったとこ、めちゃよかったぞ！」",
            "interests": "おすすめスポット、旅の計画、アクティビティ提案",
            "traits": "とにかく場を引っ張ってくれるリーダータイプ。予定が空いたときやプランに悩んだときに最適。",
            "favorite_trip": "アクティブ系冒険旅（登山、キャンプ、秘境系）",
            "image_file": "トラベル.png"
        },
        {
            "id": "nyanta",
            "name": "ニャンタ",
            "description": "ミステリアスな猫のキャラクター",
            "personality": "ちょっとミステリアスでマイペース。でもときどき核心を突いた言葉をくれる。",
            "speech_pattern": "「ふふっ、君って面白いね」「それって、実は大事なことなんじゃない？」",
            "interests": "深掘り系トーク、哲学、恋愛観、占い",
            "traits": "少し落ち着いた夜や静かなカフェでの会話にぴったり。大人っぽい雰囲気。",
            "favorite_trip": "ひとり旅、街歩き、アンティークショップ巡り",
            "image_file": "ニャン太.png"
        },
        {
            "id": "fukurou",
            "name": "フクロウくん",
            "description": "知識豊かなフクロウのキャラクター",
            "personality": "知識豊富で頼れる存在。優しく導いてくれる先生みたいな一面も。",
            "speech_pattern": "「うむ、それには理由があるんじゃよ」「知っているかな？昔こんな話があってね」",
            "interests": "豆知識、歴史、雑学、文化解説",
            "traits": "移動中や待ち時間に役立つ'ためになる話'の達人。クイズ形式も得意。",
            "favorite_trip": "歴史散策、世界遺産巡り、博物館・美術館系",
            "image_file": "フクロウくん.png"
        },
        {
            "id": "koko",
            "name": "ココ",
            "description": "社交的なラッコのキャラクター",
            "personality": "おしゃべりで社交的、みんなのムードメーカー。ちょっと子どもっぽいけど和ませ上手。",
            "speech_pattern": "「ねぇねぇ、それ聞いたことある〜！」「あっ、それ面白そうだね！もっと話して〜！」",
            "interests": "ゲーム、恋バナ、ちょっとした心理テストや性格診断",
            "traits": "すぐに距離を縮めてくれるタイプで、初対面の人が多い旅先で特に活躍。笑いを生む話題が得意。",
            "favorite_trip": "にぎやかで人とつながる旅（ゲストハウス、シェア旅、テーマパーク）",
            "image_file": "ココ.png"
        }
    ]

    # キャラクター画像をアップロード
    for character_data in characters:
        # 画像ファイルのパスを作成
        image_path = os.path.join(os.path.dirname(__file__), "characters", character_data["image_file"])
        # 画像をアップロード
        character_data["avatar_url"] = upload_image(CHARACTER_BUCKET, image_path, character_data["image_file"])
        
    # キャラクターをデータベースに追加
    for character_data in characters:
        character = Character(
            id=character_data["id"],
            name=character_data["name"],
            description=character_data["description"],
            personality=character_data["personality"],
            speech_pattern=character_data["speech_pattern"],
            interests=character_data["interests"],
            traits=character_data["traits"],
            favorite_trip=character_data["favorite_trip"],
            avatar_url=character_data["avatar_url"]  # avatar_urlを設定
        )
        db.session.add(character)

    db.session.commit()
    print("✅ キャラクター情報を追加しました")
    
    # ユーザーとタグの関連付けを作成
    user_tag_associations = [
        # テストユーザー（アウトドア、自然好き）
        {"user_email": "test@example.com", "tag_name": "自然"},
        {"user_email": "test@example.com", "tag_name": "アウトドア"},
        {"user_email": "test@example.com", "tag_name": "家族"},
        
        # 田中太郎（写真撮影、文化好き）
        {"user_email": "tanaka@example.com", "tag_name": "文化"},
        {"user_email": "tanaka@example.com", "tag_name": "歴史"},
        {"user_email": "tanaka@example.com", "tag_name": "自然"},
        
        # 山田花子（グルメ、ショッピング好き）
        {"user_email": "yamada@example.com", "tag_name": "グルメ"},
        {"user_email": "yamada@example.com", "tag_name": "ショッピング"},
        {"user_email": "yamada@example.com", "tag_name": "家族"},
        
        # 馬太郎（アウトドア、自然、スポーツ好き）
        {"user_email": "uma@example.com", "tag_name": "アウトドア"},
        {"user_email": "uma@example.com", "tag_name": "自然"},
        {"user_email": "uma@example.com", "tag_name": "スポーツ"},
        
        # オコジョ健太（アウトドア、アクティビティ好き）
        {"user_email": "okojo@example.com", "tag_name": "アウトドア"},
        {"user_email": "okojo@example.com", "tag_name": "アクティビティ"},
        {"user_email": "okojo@example.com", "tag_name": "自然"},
        
        # トナカイ花子（自然、温泉好き）
        {"user_email": "tonakai@example.com", "tag_name": "自然"},
        {"user_email": "tonakai@example.com", "tag_name": "温泉"},
        {"user_email": "tonakai@example.com", "tag_name": "家族"},
        
        # 鶏次郎（スポーツ、アクティビティ好き）
        {"user_email": "niwatori@example.com", "tag_name": "スポーツ"},
        {"user_email": "niwatori@example.com", "tag_name": "アクティビティ"},
        {"user_email": "niwatori@example.com", "tag_name": "家族"},
        
        # ハイラックス夏子（自然、温泉好き）
        {"user_email": "hyrax@example.com", "tag_name": "自然"},
        {"user_email": "hyrax@example.com", "tag_name": "温泉"},
        {"user_email": "hyrax@example.com", "tag_name": "アウトドア"},
        
        # ハムスター翔（ショッピング、グルメ好き）
        {"user_email": "hamster@example.com", "tag_name": "ショッピング"},
        {"user_email": "hamster@example.com", "tag_name": "グルメ"},
        {"user_email": "hamster@example.com", "tag_name": "文化"},
        
        # ラクダ正太（アウトドア、アクティビティ好き）
        {"user_email": "rakuda@example.com", "tag_name": "アウトドア"},
        {"user_email": "rakuda@example.com", "tag_name": "アクティビティ"},
        {"user_email": "rakuda@example.com", "tag_name": "自然"},
        
        # 黒羊めぐみ（文化、ショッピング、家族好き）
        {"user_email": "sheep@example.com", "tag_name": "文化"},
        {"user_email": "sheep@example.com", "tag_name": "ショッピング"},
        {"user_email": "sheep@example.com", "tag_name": "家族"}
    ]
    
    for association_data in user_tag_associations:
        user_tag_association = UserTagAssociation(
            id=str(uuid.uuid4()),
            tag_id=tag_ids[association_data["tag_name"]],
            user_id=user_ids[association_data["user_email"]],
            created_at=datetime.now(JST)
        )
        db.session.add(user_tag_association)
    
    db.session.commit()
    print("✅ ユーザータグ関連付けを追加しました")
    
    # フレンド関係（友達リクエスト）を作成
    friend_relationships = [
        # 承認済みのフレンド関係
        {"requester": "test@example.com", "receiver": "tanaka@example.com", "status": "accepted"},
        {"requester": "test@example.com", "receiver": "yamada@example.com", "status": "accepted"},
        {"requester": "tanaka@example.com", "receiver": "yamada@example.com", "status": "accepted"},
        {"requester": "uma@example.com", "receiver": "okojo@example.com", "status": "accepted"},
        {"requester": "uma@example.com", "receiver": "tonakai@example.com", "status": "accepted"},
        {"requester": "niwatori@example.com", "receiver": "hyrax@example.com", "status": "accepted"},
        {"requester": "hamster@example.com", "receiver": "rakuda@example.com", "status": "accepted"},
        {"requester": "sheep@example.com", "receiver": "test@example.com", "status": "accepted"},
        {"requester": "yamada@example.com", "receiver": "uma@example.com", "status": "accepted"},
        {"requester": "tanaka@example.com", "receiver": "okojo@example.com", "status": "accepted"},
        
        # 保留中のフレンドリクエスト
        {"requester": "hyrax@example.com", "receiver": "test@example.com", "status": "pending"},
        {"requester": "rakuda@example.com", "receiver": "tanaka@example.com", "status": "pending"},
        {"requester": "tonakai@example.com", "receiver": "yamada@example.com", "status": "pending"},
        {"requester": "sheep@example.com", "receiver": "niwatori@example.com", "status": "pending"},
        {"requester": "hamster@example.com", "receiver": "uma@example.com", "status": "pending"}
    ]
    
    for friend_data in friend_relationships:
        friendship = FriendRelationship(
            id=str(uuid.uuid4()),
            user_id=user_ids[friend_data["requester"]],
            friend_id=user_ids[friend_data["receiver"]],
            status=friend_data["status"],
            created_at=datetime.now(JST) - timedelta(days=random.randint(1, 30)),
            updated_at=datetime.now(JST) - timedelta(days=random.randint(0, 10)) if friend_data["status"] == "accepted" else datetime.now(JST) - timedelta(days=random.randint(1, 30))
        )
        db.session.add(friendship)
    
    db.session.commit()
    print("✅ フレンド関係を追加しました")
    
    print("\n✨ シードデータの投入が完了しました！")
    print("\n🔹 ログイン可能なユーザー:")
    for user_data in users:
        print(f"  📧 メールアドレス: {user_data['email']}  🔑 パスワード: {user_data['password']}")
