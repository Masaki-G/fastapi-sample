from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from sqlalchemy_utils import UUIDType
from uuid import uuid4
from sqlalchemy import create_engine, Column, String, Integer, Unicode, DateTime

from databases import Base
class UserModel(Base):
    """
    UserModel
    """
    __tablename__ = 'users'
    
    id = Column(UUIDType(binary=False), primary_key=True, default=uuid4)
    name = Column(String(50), nullable=False)
    email = Column(String(50), nullable=False, unique=True)
    password = Column(String(100), nullable=False)
    description = Column(Unicode(200))
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, nullable=False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)