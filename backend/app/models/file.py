import uuid
from datetime import datetime, timezone
from app.models import db

class ImageList(db.Model):
    __tablename__ = 'image_list'
    
    id = db.Column(db.String(36), primary_key=True)
    image_url = db.Column(db.String(512), nullable=False)
    uploaded_by = db.Column(db.String(36), db.ForeignKey('user.id'), nullable=False)
    upload_date = db.Column(db.DateTime, nullable=False, default=datetime.now(timezone.utc))
    
    def __init__(self, id, image_url, uploaded_by, upload_date=None):
        self.id = id
        self.image_url = image_url
        self.uploaded_by = uploaded_by
        if upload_date:
            self.upload_date = upload_date 
            
    def to_dict(self):
        """APIレスポンス用の辞書形式でデータを返す"""
        return {
            'id': self.id,
            'image_url': self.image_url,
            'uploaded_by': self.uploaded_by,
            'upload_date': self.upload_date.isoformat() if self.upload_date else None
        } 