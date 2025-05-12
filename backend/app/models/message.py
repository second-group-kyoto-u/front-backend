from app.models import db
from datetime import datetime, timezone, timedelta

JST = timezone(timedelta(hours=9))  # 日本時間タイムゾーンを定義

class EventMessage(db.Model):
    __tablename__ = 'event_message'
    
    id = db.Column(db.String(36), primary_key=True)
    event_id = db.Column(db.String(36), db.ForeignKey('event.id'), nullable=False)
    sender_user_id = db.Column(db.String(36), db.ForeignKey('user.id'))
    content = db.Column(db.String(500))
    timestamp = db.Column(db.DateTime, default=datetime.now(JST))
    image_id = db.Column(db.String(36), db.ForeignKey('image_list.id'))
    message_type = db.Column(db.String(20), default='text')  # text/image/system/bot
    message_metadata = db.Column(db.JSON)
    
    # リレーションシップ
    image = db.relationship('ImageList', backref='event_messages')
    read_statuses = db.relationship('MessageReadStatus', backref='message', lazy=True,
                                  cascade='all, delete-orphan')
    
    def to_dict(self):
        """辞書形式でデータを返す（APIレスポンス用）"""
        return {
            'id': self.id,
            'event_id': self.event_id,
            'sender': self.sender.to_dict() if self.sender else None,
            'content': self.content,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'image_url': self.image.image_url if self.image else None,
            'message_type': self.message_type,
            'metadata': self.message_metadata,
            'read_count': len(self.read_statuses) if self.read_statuses else 0
        }


class MessageReadStatus(db.Model):
    __tablename__ = 'message_read_status'
    
    message_id = db.Column(db.String(36), db.ForeignKey('event_message.id'), primary_key=True)
    user_id = db.Column(db.String(36), db.ForeignKey('user.id'), primary_key=True)
    read_at = db.Column(db.DateTime, default=datetime.now(JST))
    
    # リレーションシップ
    user = db.relationship('User', backref='read_messages')


class FriendRelationship(db.Model):
    __tablename__ = 'friend_relationship'
    
    id = db.Column(db.String(36), primary_key=True)
    user_id = db.Column(db.String(36), db.ForeignKey('user.id'), nullable=False)
    friend_id = db.Column(db.String(36), db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending/accepted/rejected
    created_at = db.Column(db.DateTime, default=datetime.now(JST))
    updated_at = db.Column(db.DateTime, default=datetime.now(JST), onupdate=datetime.now(JST))
    
    def to_dict(self):
        """辞書形式でデータを返す（APIレスポンス用）"""
        return {
            'id': self.id,
            'requester': self.requester.to_dict() if self.requester else None,
            'receiver': self.receiver.to_dict() if self.receiver else None,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class DirectMessage(db.Model):
    __tablename__ = 'direct_message'
    
    id = db.Column(db.String(36), primary_key=True)
    sender_id = db.Column(db.String(36), db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.String(36), db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.String(500))
    image_id = db.Column(db.String(36), db.ForeignKey('image_list.id'))
    message_type = db.Column(db.String(20), default='text')  # text/image/system/bot
    message_metadata = db.Column(db.JSON)
    sent_at = db.Column(db.DateTime, default=datetime.now(JST))
    is_read = db.Column(db.Boolean, default=False)
    read_at = db.Column(db.DateTime)
    
    # リレーションシップ
    image = db.relationship('ImageList', backref='direct_messages')
    
    def to_dict(self):
        """辞書形式でデータを返す（APIレスポンス用）"""
        return {
            'id': self.id,
            'sender': self.sender.to_dict() if self.sender else None,
            'receiver': self.receiver.to_dict() if self.receiver else None,
            'content': self.content,
            'sent_at': self.sent_at.isoformat() if self.sent_at else None,
            'image_url': self.image.image_url if self.image else None,
            'message_type': self.message_type,
            'metadata': self.message_metadata,
            'is_read': self.is_read,
            'read_at': self.read_at.isoformat() if self.read_at else None
        }
