from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from db.database import db


class Profile(db.Model):
    __tablename__ = 'profile'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    bio = Column(String, nullable=True)
    phone_number = Column(String, nullable=True)
    is_visible = Column(Boolean, default=True)
    user_id=Column(Integer, ForeignKey('users.id'))
    location_id = Column(Integer, ForeignKey('addresses.id'), nullable=True)
    profile_image_url = Column(String, nullable=True)