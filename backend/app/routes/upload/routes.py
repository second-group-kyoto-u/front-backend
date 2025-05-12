from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
import os
import uuid
from app.models import db
from app.models.file import ImageList
from app.routes.protected.routes import get_authenticated_user
from datetime import datetime, timezone, timedelta
from app.utils.storage import upload_file

JST = timezone(timedelta(hours=9))

upload_bp = Blueprint("upload", __name__)

@upload_bp.route("/image", methods=["POST"])
def upload_image():
    # ユーザー認証
    user, error_response, error_code = get_authenticated_user()
    if error_response:
        return jsonify(error_response), error_code
    
    # ファイルが添付されているか確認
    if 'file' not in request.files:
        return jsonify({"error": "ファイルが添付されていません"}), 400
    
    file = request.files['file']
    
    # ファイル名が空でないか確認
    if file.filename == '':
        return jsonify({"error": "ファイル名が空です"}), 400
    
    # ファイル拡張子の確認
    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
    extension = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
    
    if extension not in allowed_extensions:
        return jsonify({"error": "許可されていないファイル形式です"}), 400
    
    # ファイル名をセキュアにして一意にする
    filename = str(uuid.uuid4()) + '.' + extension
    
    # コンテンツタイプを判定
    content_type = file.content_type if hasattr(file, 'content_type') else None
    
    # S3/minioにファイルをアップロード
    file_url = upload_file(file, filename, content_type)
    
    if not file_url:
        return jsonify({"error": "ファイルのアップロードに失敗しました"}), 500
    
    # 画像情報をデータベースに保存
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
