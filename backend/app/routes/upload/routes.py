from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
import os
import uuid
from app.models import db
from app.models.file import ImageList
from app.routes.protected.routes import get_authenticated_user
from datetime import datetime, timezone, timedelta
from app.utils.storage import upload_file
from app.utils.age_certification import age_certify
import tempfile
from PIL import Image
import io

JST = timezone(timedelta(hours=9))

upload_bp = Blueprint("upload", __name__)

@upload_bp.route("/image", methods=["POST"])
def upload_image():
    # ユーザー認証
    user, error_response, error_code = get_authenticated_user()
    if error_response:
        return jsonify(error_response), error_code
    
    if 'file' not in request.files:
        return jsonify({"error": "ファイルが添付されていません"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "ファイル名が空です"}), 400
    
    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
    extension = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
    if extension not in allowed_extensions:
        return jsonify({"error": "許可されていないファイル形式です"}), 400

    filename = f"thread-messages/{uuid.uuid4()}.{extension}"
    content_type = file.content_type if hasattr(file, 'content_type') else None

    file_url = upload_file(file, filename, content_type)

    if not file_url:
        return jsonify({"error": "ファイルのアップロードに失敗しました"}), 500

    image = ImageList(
        id=str(uuid.uuid4()),
        image_url=file_url,
        uploaded_by=user.id,
        upload_date=datetime.now(JST)
    )
    
    db.session.add(image)
    db.session.commit()

    return jsonify({
        "message": "画像をアップロードしました",
        "image": {
            "id": image.id,
            "url": file_url
        }
    })


@upload_bp.route("/event-image", methods=["POST", "OPTIONS"])
def upload_event_image():
    if request.method == "OPTIONS":
        response = current_app.make_response('')
        response.headers['Access-Control-Allow-Origin'] = request.headers.get('Origin', '*')
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response

    # ユーザー認証
    user, error_response, error_code = get_authenticated_user()
    if error_response:
        return jsonify(error_response), error_code

    if 'file' not in request.files:
        return jsonify({"error": "ファイルが添付されていません"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "ファイル名が空です"}), 400

    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
    extension = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
    if extension not in allowed_extensions:
        return jsonify({"error": "許可されていないファイル形式です"}), 400

    filename = str(uuid.uuid4()) + '.' + extension
    content_type = file.content_type if hasattr(file, 'content_type') else None
    file_url = upload_file(file, filename, content_type)
    if not file_url:
        return jsonify({"error": "ファイルのアップロードに失敗しました"}), 500

    image = ImageList(
        id=str(uuid.uuid4()),
        image_url=file_url,
        uploaded_by=user.id,
        upload_date=datetime.now(JST)
    )
    db.session.add(image)
    db.session.commit()

    return jsonify({"image_id": image.id})


@upload_bp.route("/age-verification", methods=["POST", "OPTIONS"])
def upload_age_verification():
    if request.method == "OPTIONS":
        response = current_app.make_response('')
        response.headers['Access-Control-Allow-Origin'] = request.headers.get('Origin', '*')
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response

    # ユーザー認証
    user, error_response, error_code = get_authenticated_user()
    if error_response:
        return jsonify(error_response), error_code

    if 'file' not in request.files:
        return jsonify({"error": "ファイルが添付されていません"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "ファイル名が空です"}), 400

    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'pdf'}
    extension = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
    if extension not in allowed_extensions:
        return jsonify({"error": "許可されていないファイル形式です。画像ファイル(PNG, JPG, JPEG, GIF)またはPDFをアップロードしてください"}), 400

    # ファイル内容を最初に保存（ストレージアップロードとOCR処理の両方で使用）
    print(f"[UPLOAD] 年齢認証処理開始: ファイル名={file.filename}, ユーザーID={user.id}")
    file.seek(0)  # ファイルポインタを先頭に戻す
    image_data = file.read()
    print(f"[UPLOAD] 画像データ読み込み完了: {len(image_data)} bytes")
    
    # ストレージアップロード用にファイルオブジェクトを再作成
    file_for_upload = io.BytesIO(image_data)
    file_for_upload.seek(0)
    
    # 年齢認証用の専用フォルダにアップロード
    filename = f"age-verification/{user.id}_{uuid.uuid4()}.{extension}"
    content_type = file.content_type if hasattr(file, 'content_type') else None
    file_url = upload_file(file_for_upload, filename, content_type)
    
    if not file_url:
        return jsonify({"error": "ファイルのアップロードに失敗しました"}), 500

    # OCRによる年齢認証処理
    age_verification_result = "extraction_failed"
    age = None
    error_message = None
    
    try:        
        # PILで画像を開く
        try:
            image = Image.open(io.BytesIO(image_data))
            print(f"[UPLOAD] PIL画像読み込み成功: モード={image.mode}, サイズ={image.size}")
            # RGBに変換（OCRに適した形式）
            if image.mode != 'RGB':
                image = image.convert('RGB')
                print(f"[UPLOAD] RGBに変換完了")
            
            # OCRで年齢を抽出
            print(f"[UPLOAD] OCR処理開始...")
            age = age_certify(image)
            print(f"[UPLOAD] OCR処理完了: age={age}")
            
            if age >= 18:
                age_verification_result = "approved"
                status_message = f"年齢認証が完了しました。推定年齢: {age}歳"
            elif age > 0:  # 年齢は検出できたが18歳未満
                age_verification_result = "rejected"
                status_message = f"年齢認証に失敗しました。18歳以上である必要があります。推定年齢: {age}歳"
            else:  # 年齢が検出できなかった
                age_verification_result = "extraction_failed"
                status_message = "書類から年齢情報を読み取れませんでした。鮮明な画像で再度お試しください。"
                
        except Exception as image_error:
            print(f"[UPLOAD] 画像処理エラー: {image_error}")
            age_verification_result = "extraction_failed"
            status_message = "画像の処理に失敗しました。ファイル形式や画質を確認してください。"
            
    except Exception as ocr_error:
        print(f"[UPLOAD] OCRエラー: {ocr_error}")
        age_verification_result = "extraction_failed"
        status_message = "書類の読み取りに失敗しました。鮮明な画像で再度お試しください。"

    print(f"[UPLOAD] 年齢認証処理完了: result={age_verification_result}, age={age}")
    
    # 年齢認証のステータスを更新
    user.age_verification_status = age_verification_result

    # 画像をデータベースに保存
    image = ImageList(
        id=str(uuid.uuid4()),
        image_url=file_url,
        uploaded_by=user.id,
        upload_date=datetime.now(JST)
    )
    db.session.add(image)
    db.session.commit()

    return jsonify({
        "message": status_message,
        "status": age_verification_result,
        "age": age if age and age > 0 else None,
        "user": {
            "id": user.id,
            "user_name": user.user_name,
            "is_age_verified": user.age_verification_status == 'approved'
        }
    })

