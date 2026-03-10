from sqlalchemy import Column, Integer, String, Boolean, DateTime
from database import Base
from datetime import datetime
import uuid

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    guid = Column(String(36), unique=True, default=lambda: str(uuid.uuid4()))
    full_name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    phone_no = Column(String(20), nullable=True)
    auth_provider = Column(String(50), default="local")
    role = Column(String(50), default="user")
    subscription_tier = Column(String(50), default="basic")
    available_credits = Column(Integer, default=2)
    status = Column(Boolean, default=True)  # Using boolean to map to tinyint(1)
    last_login_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    txn_id = Column(String(50), unique=True, index=True)
    user_id = Column(Integer, index=True)
    user_name = Column(String(255))
    amount = Column(String(50)) # e.g. "₹1,499"
    plan = Column(String(100))
    status = Column(String(50)) # Completed, Failed, Processing
    method = Column(String(50)) # UPI, Card, Razorpay
    created_at = Column(DateTime, default=datetime.utcnow)
