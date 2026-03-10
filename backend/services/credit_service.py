from sqlalchemy.orm import Session
from models import User
from fastapi import HTTPException

class CreditService:
    @staticmethod
    def has_sufficient_credits(db: Session, user_email: str, required_credits: int = 1) -> bool:
        """Check if user has enough credits."""
        user = db.query(User).filter(User.email == user_email).first()
        if not user:
            return False
        return user.available_credits >= required_credits

    @staticmethod
    def deduct_credits(db: Session, user_email: str, credits_to_deduct: int = 1) -> int:
        """Deduct credits from user and return remaining balance."""
        user = db.query(User).filter(User.email == user_email).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        if user.available_credits < credits_to_deduct:
            raise HTTPException(
                status_code=402, 
                detail=f"Insufficient credits. Required: {credits_to_deduct}, Available: {user.available_credits}"
            )
        
        user.available_credits -= credits_to_deduct
        db.commit()
        db.refresh(user)
        return user.available_credits

    @staticmethod
    def get_credits(db: Session, user_email: str) -> dict:
        """Get current credit balance and subscription info."""
        user = db.query(User).filter(User.email == user_email).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return {
            "available_credits": user.available_credits,
            "subscription_tier": user.subscription_tier,
            "email": user.email
        }

credit_service = CreditService()
