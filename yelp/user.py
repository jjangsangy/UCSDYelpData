import json

from datetime import datetime, timedelta
from sqlalchemy import Table, Column, Integer, String, DateTime, ForeignKey, Boolean, Float
from sqlalchemy.orm import relationship, backref, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine

Base = declarative_base()

class User(Base):

    __tablename__ = 'user'

    id            =   Column(Integer,    primary_key=True)
    user_id       =   Column(String(23), unique=True, nullable=False)
    name          =   Column(String,     nullable=False)
    votes         =   Column(Integer,    ForeignKey('votes.id'))
    elite         =   Column(Boolean,    default=False)
    fans          =   Column(Integer,    default=0)
    review_count  =   Column(Integer,    default=0)
    yelping_since =   Column(String,     default='')
    average_stars =   Column(Float,      default=0.0)
    compliments   =   Column(Integer,    ForeignKey('compliments.id'))

    friends       =   relationship('Friends', backref='friends', lazy='dynamic')

    def __repr__(self):
        return "<User (name='%s', user_id='%s', review_count='%s')>" % (
            self.name, self.user_id, self.review_count
    )

class Friends(Base):

    __tablename__ = 'friends'

    user_id =   Column(String, primary_key=True)
    name    =   Column(String, nullable=False)

class Compliments(Base):

    __tablename__ = 'compliments'

    id      =   Column(Integer, primary_key=True)
    name    =   Column(String(255), unique=True, nullable=False)

    def __repr__(self):
        return "<Compliments (name='%s')>" % (self.name)

class Votes(Base):

    __tablename__ = 'votes'

    id      =   Column(Integer, primary_key=True)
    name    =   Column(String(255), unique=True, nullable=False)

def main():
    engine = create_engine('sqlite:///graph.db')

    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    funny   = Compliments(name='funny')
    cute    = Compliments(name='cute')
    photos  = Compliments(name='photos')
    more    = Compliments(name='more')
    cool    = Compliments(name='cool')
    profile = Compliments(name='profile')
    writer  = Compliments(name='writer')
    hot     = Compliments(name='hot')
    note    = Compliments(name='note')
    plain   = Compliments(name='plain')

    cool   = Votes(name='cool')
    funny  = Votes(name='funny')
    useful = Votes(name='useful')