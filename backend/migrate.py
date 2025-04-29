from app import create_app
from app.models import db
from app.models.user import User
from app.models.area import AreaList
from app.models.file import ImageList
from app.models.thread import Thread, ThreadMessage, ThreadComment, ThreadFavor, UserHeartThread
from app.models.event import Event, UserMemberGroup, UserHeartEvent, TagMaster, UserTagAssociation, EventTagAssociation, ThreadTagAssociation
from app.models.message import EventMessage, MessageReadStatus, FriendRelationship, DirectMessage

app = create_app()
with app.app_context():
    # アプリケーションの状態にデータがある場合、バックアップは推奨されます
    # 既存のテーブルが存在する場合はカラムを追加するなどの方法もあります

    # 以下は開発環境での使用を想定しています - 本番環境では注意が必要です
    # まず既存のテーブルを削除
    try:
        db.session.execute('SET FOREIGN_KEY_CHECKS=0;')
        
        # メッセージ関連テーブル
        db.session.execute('DROP TABLE IF EXISTS message_read_status;')
        db.session.execute('DROP TABLE IF EXISTS direct_message;')
        db.session.execute('DROP TABLE IF EXISTS event_message;')
        
        # スレッド関連テーブル
        db.session.execute('DROP TABLE IF EXISTS thread_comment;')
        db.session.execute('DROP TABLE IF EXISTS thread_message;')
        db.session.execute('DROP TABLE IF EXISTS thread_favor;')
        db.session.execute('DROP TABLE IF EXISTS user_heart_thread;')
        
        # イベント関連テーブル
        db.session.execute('DROP TABLE IF EXISTS tag_association;')
        db.session.execute('DROP TABLE IF EXISTS tag_master;')
        db.session.execute('DROP TABLE IF EXISTS user_heart_event;')
        db.session.execute('DROP TABLE IF EXISTS user_member_group;')
        db.session.execute('DROP TABLE IF EXISTS event;')
        
        # 友達関係テーブル
        db.session.execute('DROP TABLE IF EXISTS friend_relationship;')
        
        # その他メインテーブル
        db.session.execute('DROP TABLE IF EXISTS thread;')
        db.session.execute('DROP TABLE IF EXISTS image_list;')
        db.session.execute('DROP TABLE IF EXISTS area_list;')
        db.session.execute('DROP TABLE IF EXISTS user;')
        
        db.session.execute('SET FOREIGN_KEY_CHECKS=1;')
        db.session.commit()
        print("既存のテーブルを削除しました")
    except Exception as e:
        db.session.rollback()
        print(f"テーブル削除中にエラーが発生しました: {e}")

    # テーブルを新しく作成
    try:
        db.create_all()
        db.session.commit()
        print("データベーステーブルが再作成されました")
    except Exception as e:
        db.session.rollback()
        print(f"テーブル作成中にエラーが発生しました: {e}") 