from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# モデルのインポート
from app.models.user import User, get_user_by_email
from app.models.area import AreaList
from app.models.file import ImageList
from app.models.event import (
    Event, UserMemberGroup, UserHeartEvent, 
    TagMaster, TagAssociation
)
from app.models.thread import (
    Thread, ThreadMessage, 
    UserHeartThread
)
from app.models.message import (
    EventMessage, MessageReadStatus,
    FriendRelationship, DirectMessage
)
