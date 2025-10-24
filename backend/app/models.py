from sqlalchemy import Column, Integer, String, Text, DateTime, func
from .db import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(120), nullable=False)
    city = Column(String(120), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
