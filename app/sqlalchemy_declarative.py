import os
import sys
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
 
Base = declarative_base()
 
class Person(Base):
    __tablename__ = 'person'
    # Here we define columns for the table person
    # Notice that each column is also a normal Python instance attribute.
    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
 
class User(Base):
  __tablename__ = 'users'
  id = Column(Integer, primary_key = True)
  email = Column(String(64), unique=True, index=True)
  username = Column(String(64), unique=True, index=True)
  # password_hash = Column(String(128))
  password = Column(String(128))
  role_id = Column(Integer, ForeignKey('roles.id'))

class Role(Base):
  __tablename__ = 'roles'
  id = Column(Integer, primary_key=True)
  name = Column(String(64), unique=True)
  default = Column(Integer, default=1, index=2)
  permissions = Column(Integer)
  users = relationship('User', backref='role', lazy='dynamic')
# Create an engine that stores data in the local directory's
# sqlalchemy_example.db file.
engine = create_engine('sqlite:///example.db')
 
# Create all tables in the engine. This is equivalent to "Create Table"
# statements in raw SQL.
Base.metadata.create_all(engine)