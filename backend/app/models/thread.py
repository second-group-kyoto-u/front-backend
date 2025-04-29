from app.models import db
from datetime import datetime, timezone
from app.models.event import TagMaster, ThreadTagAssociation


class Thread(db.Model):
    __tablename__ = 'thread'
    
    id = db.Column(db.String(36), primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    message = db.Column(db.String(500), nullable=False)
    image_id = db.Column(db.String(36), db.ForeignKey('image_list.id'))
    area_id = db.Column(db.String(36), db.ForeignKey('area_list.area_id'))
    published_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    author_id = db.Column(db.String(36), db.ForeignKey('user.id'), nullable=False)
    
    # リレーションシップ
    image = db.relationship('ImageList', backref='threads')
    area = db.relationship('AreaList', backref='threads')
    messages = db.relationship('ThreadMessage', backref='thread', lazy=True)
    tags = db.relationship('ThreadTagAssociation', backref='thread', lazy=True)
    
    @property
    def author(self):
        # Userモデルを遅延インポート
        from app.models.user import User
        return User.query.get(self.author_id)
    
    def to_dict(self):
        """辞書形式でデータを返す（APIレスポンス用）"""
        # 直接tagsをクエリするために必要なインポートを確認
        from app.models.event import TagMaster
        
        tags = []
        try:
            # スレッドに関連付けられたタグを取得
            for assoc in self.tags:
                tag = TagMaster.query.get(assoc.tag_id)
                if tag:
                    tags.append({
                        'id': tag.id,
                        'name': tag.tag_name
                    })
        except Exception as e:
            # エラーが発生した場合は空のリストを使用
            tags = []
            
        # 画像URLを取得（より明示的な方法）
        image_url = None
        if self.image_id:
            from app.models.file import ImageList
            image = ImageList.query.get(self.image_id)
            if image:
                image_url = image.image_url
                
        return {
            'id': self.id,
            'title': self.title,
            'message': self.message,
            'created_at': self.published_at.isoformat() if self.published_at else None,
            'created_by': {
                'id': self.author.id,
                'user_name': self.author.user_name,
                'profile_image_url': self.author.user_image_url if hasattr(self.author, 'user_image_url') else None
            } if self.author else None,
            'area': {
                'id': self.area.area_id,
                'name': self.area.area_name
            } if self.area else None,
            'image_url': image_url,
            'hearts_count': len(self.hearted_by) if hasattr(self, 'hearted_by') else 0,
            'messages_count': len(self.messages) if hasattr(self, 'messages') else 0,
            'tags': tags,
            'is_hearted': False  # デフォルト値、実際の値はAPI呼び出し時に設定する
        }


class ThreadMessage(db.Model):
    __tablename__ = 'thread_message'
    
    id = db.Column(db.String(36), primary_key=True)
    thread_id = db.Column(db.String(36), db.ForeignKey('thread.id'), nullable=False)
    sender_user_id = db.Column(db.String(36), db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.String(500), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    image_id = db.Column(db.String(36), db.ForeignKey('image_list.id'))
    message_type = db.Column(db.String(20), default='text')  # text/image/system
    message_metadata = db.Column(db.JSON)
    
    # リレーションシップ
    image = db.relationship('ImageList', backref='thread_messages')
    
    @property
    def sender(self):
        # Userモデルを遅延インポート
        from app.models.user import User
        return User.query.get(self.sender_user_id)
    
    def to_dict(self):
        """辞書形式でデータを返す（APIレスポンス用）"""
        # 画像URLを取得（より明示的な方法）
        image_url = None
        if self.image_id and self.message_type == 'image':
            from app.models.file import ImageList
            image = ImageList.query.get(self.image_id)
            if image:
                image_url = image.image_url
                
        return {
            'id': self.id,
            'thread_id': self.thread_id,
            'created_by': {
                'id': self.sender.id,
                'user_name': self.sender.user_name,
                'profile_image_url': self.sender.user_image_url if hasattr(self.sender, 'user_image_url') else None
            } if self.sender else None,
            'content': self.content if self.message_type == 'text' else image_url,
            'created_at': self.timestamp.isoformat() if self.timestamp else None,
            'message_type': self.message_type,
            'metadata': self.message_metadata
        }


class UserHeartThread(db.Model):
    __tablename__ = 'user_heart_thread'
    
    user_id = db.Column(db.String(36), db.ForeignKey('user.id'), primary_key=True)
    thread_id = db.Column(db.String(36), db.ForeignKey('thread.id'), primary_key=True) 