from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from datetime import datetime, timezone
import uuid

class User(BaseModel):
    id: Optional[str] = None
    guid: str = Field(default_factory=lambda: str(uuid.uuid4()))
    full_name: str
    email: str
    password_hash: str
    phone_no: Optional[str] = None
    auth_provider: str = "local"
    role: str = "user"
    subscription_tier: str = "basic"
    available_credits: int = 2
    status: bool = True
    last_login_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Transaction(BaseModel):
    id: Optional[str] = None
    txn_id: str                         # Razorpay order_id
    razorpay_payment_id: Optional[str] = None  # Razorpay payment_id after capture
    razorpay_signature: Optional[str] = None   # HMAC signature for verification
    user_id: Optional[str] = None
    user_name: str
    user_email: Optional[str] = None
    amount: str                         # formatted e.g. "₹2,499"
    amount_paise: int = 0               # raw Razorpay amount in paise
    plan: str
    plan_credits: int = 0               # credits to award on success
    status: str                         # Pending / Completed / Failed
    method: str = "Razorpay"            # payment method
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
