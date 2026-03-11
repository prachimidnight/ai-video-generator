from pymongo.database import Database
from fastapi import HTTPException

class CreditService:
    @staticmethod
    def has_sufficient_credits(db: Database, user_email: str, required_credits: int = 1) -> bool:
        """Check if user has enough credits."""
        user = db.users.find_one({"email": user_email})
        if not user:
            return False
        return user.get("available_credits", 0) >= required_credits

    @staticmethod
    def deduct_credits(db: Database, user_email: str, credits_to_deduct: int = 1) -> int:
        """Deduct credits from user and return remaining balance."""
        user = db.users.find_one({"email": user_email})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        current_credits = user.get("available_credits", 0)
        if current_credits < credits_to_deduct:
            raise HTTPException(
                status_code=402, 
                detail=f"Insufficient credits. Required: {credits_to_deduct}, Available: {current_credits}"
            )
        
        new_credits = current_credits - credits_to_deduct
        db.users.update_one(
            {"email": user_email},
            {"$set": {"available_credits": new_credits}}
        )
        return new_credits

    @staticmethod
    def get_credits(db: Database, user_email: str) -> dict:
        """Get current credit balance and subscription info."""
        user = db.users.find_one({"email": user_email})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return {
            "available_credits": user.get("available_credits", 0),
            "subscription_tier": user.get("subscription_tier", "basic"),
            "email": user.get("email")
        }

credit_service = CreditService()
