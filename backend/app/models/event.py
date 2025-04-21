from app.models import db
from datetime import datetime, timezone
from app.models.area import AreaList
from app.models.file import ImageList


class Event(db.Model):
    __tablename__ = 'event'
    
    id = db.Column(db.String(36), primary_key=True)
    message = db.Column(db.String(500), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    image_id = db.Column(db.String(36), db.ForeignKey('image_list.id'))
    current_persons = db.Column(db.Integer, default=1)
    limit_persons = db.Column(db.Integer)
    is_request = db.Column(db.Boolean, default=False)
    is_deleted = db.Column(db.Boolean, default=False)
    author_user_id = db.Column(db.String(36), db.ForeignKey('user.id'), nullable=False)
    area_id = db.Column(db.String(36), db.ForeignKey('area_list.area_id'))
    published_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    status = db.Column(db.String(20), default='pending')  # pending/started/ended
    
    # リレーションシップ
    image = db.relationship('ImageList', backref='events')
    area = db.relationship('AreaList', backref='events')
    messages = db.relationship('EventMessage', backref='event', lazy=True)
    
    def to_dict(self):
        """辞書形式でデータを返す（APIレスポンス用）"""
        return {
            'id': self.id,
            'message': self.message,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'published_at': self.published_at.isoformat() if self.published_at else None,
            'current_persons': self.current_persons,
            'limit_persons': self.limit_persons,
            'is_request': self.is_request,
            'status': self.status,
            'author': self.author.to_dict() if self.author else None,
            'area': {
                'id': self.area.area_id,
                'name': self.area.area_name
            } if self.area else None,
            'image_url': self.image.image_url if self.image else None
        }


class UserMemberGroup(db.Model):
    __tablename__ = 'user_member_group'
    
    user_id = db.Column(db.String(36), db.ForeignKey('user.id'), primary_key=True)
    event_id = db.Column(db.String(36), db.ForeignKey('event.id'), primary_key=True)
    joined_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))


class UserHeartEvent(db.Model):
    __tablename__ = 'user_heart_event'
    
    user_id = db.Column(db.String(36), db.ForeignKey('user.id'), primary_key=True)
    event_id = db.Column(db.String(36), db.ForeignKey('event.id'), primary_key=True)


class TagMaster(db.Model):
    __tablename__ = 'tag_master'
    
    id = db.Column(db.String(36), primary_key=True)
    tag_name = db.Column(db.String(50), nullable=False, unique=True)
    category = db.Column(db.String(50))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    
    # リレーションシップ
    associations = db.relationship('TagAssociation', backref='tag', lazy=True)


class TagAssociation(db.Model):
    __tablename__ = 'tag_association'
    
    id = db.Column(db.String(36), primary_key=True)
    tag_id = db.Column(db.String(36), db.ForeignKey('tag_master.id'), nullable=False)
    entity_id = db.Column(db.String(36), nullable=False)
    entity_type = db.Column(db.String(20), nullable=False)  # user/event/thread
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc)) 