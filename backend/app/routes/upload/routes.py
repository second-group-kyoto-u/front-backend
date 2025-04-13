from flask import Blueprint, request, jsonify
from app.models.user import db, User
import boto3, os
from werkzeug.utils import secure_filename

upload_bp = Blueprint('upload', __name__)

s3 = boto3.client(
    's3',
    endpoint_url=os.getenv('MINIO_ENDPOINT'),
    aws_access_key_id=os.getenv('MINIO_ACCESS_KEY'),
    aws_secret_access_key=os.getenv('MINIO_SECRET_KEY'),
    region_name='us-east-1'
)

@upload_bp.route('/upload', methods=['POST'])
def upload():
    file = request.files.get('file')
    user_id = request.form.get('user_id')
    if not file or not user_id:
        return jsonify({'error': 'ファイルまたはユーザーIDがありません'}), 400

    filename = f"{user_id}/{secure_filename(file.filename)}"
    bucket = os.getenv('MINIO_BUCKET')

    s3.upload_fileobj(file, bucket, filename)

    image_url = f"{os.getenv('MINIO_ENDPOINT')}/{bucket}/{filename}"

    # DBに保存
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'ユーザーが存在しません'}), 404
    user.profile_image_url = image_url
    db.session.commit()

    return jsonify({'url': image_url})
