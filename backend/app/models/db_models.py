import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)

    reports = relationship("Report", back_populates="user", cascade="all, delete-orphan")


class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)
    patient_name = Column(String, nullable=True)
    source_type = Column(String, nullable=False, default="text")
    word_count = Column(Integer, default=0)
    sentence_count = Column(Integer, default=0)
    structured_summary_json = Column(Text, nullable=True)
    extractive_summary = Column(Text, nullable=True)
    abstractive_summary = Column(Text, nullable=True)

    user = relationship("User", back_populates="reports")
