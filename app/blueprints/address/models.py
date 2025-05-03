from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from db.database import db


class Country(db.Model):
    __tablename__ = 'countries'
    
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    iso_code = Column(String(3), unique=True)

    
    states = relationship("State", back_populates="country")

class State(db.Model):
    __tablename__ = 'states'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    country_id = Column(Integer, ForeignKey('countries.id'), nullable=False)
    
    country = relationship("Country", back_populates="states")
    cities = relationship("City", back_populates="state")
    # addresses = relationship("Address", back_populates="state")

class City(db.Model):
    __tablename__ = 'cities'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    state_id = Column(Integer, ForeignKey('states.id'), nullable=False)
    postal_code_prefix = Column(String(10))
    
    state = relationship("State", back_populates="cities")
    # addresses = relationship("Address", back_populates="city")



class Address(db.Model):
    __tablename__ = 'addresses'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    lat = Column(Float)
    lan = Column(Float)
    street_address = Column(String(255), nullable=False)
    city_id = Column(Integer, ForeignKey('cities.id'), nullable=False)
    state_id = Column(Integer, ForeignKey('states.id'), nullable=False)
    country_id = Column(Integer, ForeignKey('countries.id'), nullable=False)
    postal_code = Column(String(20))
    is_primary = Column(Boolean, default=False)
    
    # user = relationship("User", back_populates="addresses")
    # city = relationship("City", back_populates="addresses")
    # state = relationship("State", back_populates="addresses")