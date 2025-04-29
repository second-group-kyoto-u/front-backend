# アプリケーション内でユーザーに関するデータ構造と処理をまとめる場所
from app.models import db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timezone
from sqlalchemy.sql.expression import and_
from sqlalchemy.orm import foreign


class User(db.Model):
    __tablename__ = 'user'
    
    id = db.Column(db.String(36), primary_key=True)
    user_name = db.Column(db.String(100), nullable=False)
    birthdate = db.Column(db.DateTime)
    user_image_url = db.Column(db.String(512))
    email_address = db.Column(db.String(120), unique=True, nullable=False)
    profile_message = db.Column(db.String(500))
    is_certificated = db.Column(db.Boolean, default=False)
    password_hash = db.Column(db.String(256), nullable=False)
    
    # 認証関連の新しいフィールド
    email_verified = db.Column(db.Boolean, default=False)
    email_verified_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))
    last_login_at = db.Column(db.DateTime)
    
    # リレーションシップ
    events = db.relationship('Event', backref='author', lazy=True, foreign_keys='Event.author_user_id')
    created_threads = db.relationship('Thread', lazy=True, foreign_keys='Thread.author_id')
    
    # タグ関連
    tags = db.relationship('UserTagAssociation', backref='user', lazy=True)
    
    # メンバーとして参加しているイベント
    joined_events = db.relationship('Event', secondary='user_member_group',
                                  backref=db.backref('event_members', lazy=True))
    
    # いいねしたイベント関連
    hearted_events = db.relationship('Event', secondary='user_heart_event',
                                    backref=db.backref('hearted_by', lazy=True))
    
    # いいねしたスレッド関連
    hearted_threads = db.relationship('Thread', secondary='user_heart_thread',
                                      backref=db.backref('hearted_by', lazy=True))
    
    # 送信したイベントメッセージ
    event_messages = db.relationship('EventMessage', backref='sender', lazy=True, 
                                    foreign_keys='EventMessage.sender_user_id')
    
    # 送信したスレッドメッセージ
    sent_messages = db.relationship('ThreadMessage', lazy=True, 
                                     foreign_keys='ThreadMessage.sender_user_id')
    
    # フレンド関係（送信者側）
    friend_requests_sent = db.relationship('FriendRelationship', 
                                         backref='requester', lazy=True,
                                         foreign_keys='FriendRelationship.user_id')
    
    # フレンド関係（受信者側）
    friend_requests_received = db.relationship('FriendRelationship', 
                                             backref='receiver', lazy=True,
                                             foreign_keys='FriendRelationship.friend_id')
    
    # 送信したDM
    direct_messages_sent = db.relationship('DirectMessage', 
                                          backref='sender', lazy=True,
                                          foreign_keys='DirectMessage.sender_id')
    
    # 受信したDM
    direct_messages_received = db.relationship('DirectMessage', 
                                             backref='receiver', lazy=True,
                                             foreign_keys='DirectMessage.receiver_id')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def verify_email(self):
        """メールアドレスを認証済みにする"""
        self.email_verified = True
        self.email_verified_at = datetime.now(timezone.utc)
        self.is_certificated = True  # 既存のフィールドも更新
    
    def record_login(self):
        """ログイン日時を記録する"""
        self.last_login_at = datetime.now(timezone.utc)
    
    def to_dict(self):
        """辞書形式でデータを返す（APIレスポンス用）"""
        return {
            'id': self.id,
            'user_name': self.user_name,
            'user_image_url': self.user_image_url,
            'profile_message': self.profile_message,
            'is_certificated': self.is_certificated,
            'email_verified': self.email_verified,
            'email_address': self.email_address,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


# DBアクセス用ヘルパー関数
def get_user_by_email(email: str) -> User | None:
    return User.query.filter_by(email_address=email).first()

def get_user_by_id(user_id: str) -> User | None:
    return User.query.get(user_id)
