from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class UserCreate(BaseModel):
    full_name: str
    email: EmailStr
    password: str

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[str] = None
    subscription_tier: Optional[str] = None
    status: Optional[bool] = None
    available_credits: Optional[int] = None

class UserResponse(BaseModel):
    guid: str
    full_name: str
    email: str
    status: bool
    role: str
    available_credits: int
    subscription_tier: str
    created_at: datetime
    
    class Config:
        from_attributes = True
