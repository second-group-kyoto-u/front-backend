import uuid
from datetime import datetime, timezone, timedelta
from app.models import db

JST = timezone(timedelta(hours=9))  # 日本標準時 (JST) のタイムゾーンを定義

class ImageList(db.Model):
    __tablename__ = 'image_list'
    
    id = db.Column(db.String(36), primary_key=True)
    image_url = db.Column(db.String(512), nullable=False)
    uploaded_by = db.Column(db.String(36), db.ForeignKey('user.id'), nullable=False)
    upload_date = db.Column(db.DateTime, nullable=False, default=datetime.now(JST))
    
    # 関連エンティティを表す新しいカラム
    entity_type = db.Column(db.String(50))  # 'thread', 'event', 'thread_message', 'event_message', 'direct_message', 'user_profile'
    entity_id = db.Column(db.String(36))  # 関連するエンティティのID
    
    def __init__(self, id, image_url, uploaded_by, entity_type=None, entity_id=None, upload_date=None):
        self.id = id
        self.image_url = image_url
        self.uploaded_by = uploaded_by
        self.entity_type = entity_type
        self.entity_id = entity_id
        self.upload_date = upload_date if upload_date else datetime.now(JST)
            
    def to_dict(self):
        """APIレスポンス用の辞書形式でデータを返す"""
        return {
            'id': self.id,
            'image_url': self.image_url,
            'uploaded_by': self.uploaded_by,
            'upload_date': self.upload_date.isoformat() if self.upload_date else None,
            'entity_type': self.entity_type,
            'entity_id': self.entity_id
        }
