from app.models import db
from datetime import datetime

class AreaList(db.Model):
    __tablename__ = 'area_list'
    
    area_id = db.Column(db.String(36), primary_key=True)
    area_name = db.Column(db.String(100), nullable=False)
    
    def __init__(self, area_id, area_name):
        self.area_id = area_id
        self.area_name = area_name
    
    def to_dict(self):
        """辞書形式でデータを返す（APIレスポンス用）"""
        return {
            'id': self.area_id,
            'name': self.area_name
        } 