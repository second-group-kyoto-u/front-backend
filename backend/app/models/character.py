from app.models import db


class Character(db.Model):
    __tablename__ = "characters"

    id = db.Column(db.String(36), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    personality = db.Column(db.Text, nullable=True)
    speech_pattern = db.Column(db.Text, nullable=True)
    interests = db.Column(db.Text, nullable=True)
    traits = db.Column(db.Text, nullable=True)
    favorite_trip = db.Column(db.Text, nullable=True)
    avatar_url = db.Column(db.String(255), nullable=True)
    
    def __init__(self, id, name, description=None, personality=None, 
                 speech_pattern=None, interests=None, traits=None, 
                 favorite_trip=None, avatar_url=None):
        self.id = id
        self.name = name
        self.description = description
        self.personality = personality
        self.speech_pattern = speech_pattern
        self.interests = interests
        self.traits = traits
        self.favorite_trip = favorite_trip
        self.avatar_url = avatar_url
    
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "personality": self.personality,
            "speech_pattern": self.speech_pattern,
            "interests": self.interests,
            "traits": self.traits,
            "favorite_trip": self.favorite_trip,
            "avatar_url": self.avatar_url
        } 