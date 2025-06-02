import os
import boto3
from botocore.exceptions import ClientError
from flask import current_app
import logging

logger = logging.getLogger(__name__)

def get_s3_client():
    """
    環境に応じてS3クライアントまたはMinioクライアントを返す
    """
    # 環境変数から設定を取得
    endpoint_url = os.getenv('MINIO_ENDPOINT')  # MinioのURL
    aws_access_key_id = os.getenv('MINIO_ACCESS_KEY')
    aws_secret_access_key = os.getenv('MINIO_SECRET_KEY')
    region_name = os.getenv('AWS_REGION', 'ap-northeast-1')  # デフォルトは東京リージョン
    
    # S3/Minioクライアントを作成
    s3_client = boto3.client(
        's3',
        endpoint_url=endpoint_url,  # MinioならURL指定、AWS S3ならNone
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        region_name=region_name
    )
    
    return s3_client

def ensure_bucket_exists(bucket_name):
    """
    指定されたバケットが存在するか確認し、存在しない場合は作成する
    
    Args:
        bucket_name: バケット名
        
    Returns:
        bool: 成功時はTrue、失敗時はFalse
    """
    if not bucket_name:
        logger.error("バケット名が指定されていません")
        return False
        
    s3_client = get_s3_client()
    
    try:
        # バケットが存在するか確認
        s3_client.head_bucket(Bucket=bucket_name)
        logger.info(f"バケット '{bucket_name}' は既に存在します")
        return True
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code')
        
        # バケットが存在しない場合は作成
        if error_code == '404':
            try:
                # バケットを作成
                s3_client.create_bucket(Bucket=bucket_name)
                logger.info(f"バケット '{bucket_name}' を作成しました")
                
                # パブリックアクセスの設定
                s3_client.put_bucket_policy(
                    Bucket=bucket_name,
                    Policy=f'''{{
                        "Version": "2012-10-17",
                        "Statement": [
                            {{
                                "Effect": "Allow",
                                "Principal": "*",
                                "Action": "s3:GetObject",
                                "Resource": "arn:aws:s3:::{bucket_name}/*"
                            }}
                        ]
                    }}'''
                )
                logger.info(f"バケット '{bucket_name}' の公開読み取りポリシーを設定しました")
                return True
            except ClientError as create_error:
                logger.error(f"バケット '{bucket_name}' の作成に失敗しました: {create_error}")
                return False
        else:
            logger.error(f"バケット '{bucket_name}' の確認中にエラーが発生しました: {e}")
            return False

def upload_file(file_data, filename, content_type=None):
    """
    ファイルをS3/Minioにアップロードする
    
    Args:
        file_data: アップロードするファイルデータ
        filename: 保存するファイル名
        content_type: ファイルのMIMEタイプ（オプション）
    
    Returns:
        成功時: アップロードされたファイルのURL
        失敗時: None
    """
    bucket_name = os.getenv('MINIO_BUCKET')
    if not bucket_name:
        logger.error("MINIO_BUCKET環境変数が設定されていません")
        return None
    
    # バケットが存在することを確認し、なければ作成
    if not ensure_bucket_exists(bucket_name):
        logger.error(f"バケット '{bucket_name}' の確認/作成に失敗しました")
        return None
    
    # ファイルをアップロード
    try:
        extra_args = {}
        if content_type:
            extra_args['ContentType'] = content_type
        
        # 公開読み取り権限を追加
        extra_args['ACL'] = 'public-read'
        
        s3_client = get_s3_client()
        s3_client.upload_fileobj(
            file_data,
            bucket_name,
            filename,
            ExtraArgs=extra_args
        )
        
        # ファイルのURLを生成
        endpoint_url = os.getenv('MINIO_ENDPOINT')
        if endpoint_url:  # Minio
            # 直接MinIOエンドポイントのIPアドレスを使用
            file_url = f"http://57.182.254.92:9000/{bucket_name}/{filename}"
        else:  # AWS S3
            file_url = f"https://{bucket_name}.s3.{os.getenv('AWS_REGION', 'ap-northeast-1')}.amazonaws.com/{filename}"
        
        return file_url
    
    except ClientError as e:
        logger.error(f"S3/Minioへのアップロードエラー: {e}")
        return None

def delete_file(filename):
    """
    S3/Minioからファイルを削除する
    
    Args:
        filename: 削除するファイル名
    
    Returns:
        bool: 削除成功時はTrue、失敗時はFalse
    """
    bucket_name = os.getenv('MINIO_BUCKET')
    if not bucket_name:
        logger.error("MINIO_BUCKET環境変数が設定されていません")
        return False
    
    try:
        s3_client = get_s3_client()
        s3_client.delete_object(
            Bucket=bucket_name,
            Key=filename
        )
        return True
    
    except ClientError as e:
        logger.error(f"S3/Minioからのファイル削除エラー: {e}")
        return False 