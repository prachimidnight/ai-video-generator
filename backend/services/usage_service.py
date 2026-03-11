"""
Usage Tracking Service - Tracks API token usage, costs, and generation history in MongoDB.
"""

import time
from datetime import datetime, timezone, timedelta
from typing import Optional, List
from pymongo.database import Database

# IST timezone
IST = timezone(timedelta(hours=5, minutes=30))

# Pricing - Kept for cost calculation logic
PRICING = {
    "gemini-2.0-flash": { "input_per_1k_tokens": 0.0, "output_per_1k_tokens": 0.0 }, # Free tier normally
    "gemini-1.5-pro": { "input_per_1k_tokens": 1.25, "output_per_1k_tokens": 5.00 },
    "gemini-2.0-flash-lite-preview-02-05": { "input_per_1k_tokens": 0.0, "output_per_1k_tokens": 0.0 },
    "veo-3.1-fast-generate-preview": { "per_second": 0.35, "free_tier": True },
}

class UsageService:
    def log_generation(
        self,
        db: Database,
        topic: str,
        script: str,
        language: str,
        engine: str,
        voice: str,
        duration_requested: int,
        video_duration_actual: float = 0,
        video_file_size_bytes: int = 0,
        script_input_tokens: int = 0,
        script_output_tokens: int = 0,
        tts_characters: int = 0,
        captions_enabled: bool = False,
        caption_style: str = "",
        formats_generated: list = None,
        dub_languages: list = None,
        status: str = "success",
        error_message: str = "",
        video_model: str = "",
        user_email: str = ""
    ) -> dict:
        """Log a complete video generation with all usage metrics to MongoDB."""
        now = datetime.now(IST)
        
        if tts_characters == 0 and script:
            tts_characters = len(script)
        
        # Calculate costs
        cost_breakdown = self._calculate_costs(
            engine=engine,
            video_model=video_model,
            video_duration=video_duration_actual or duration_requested,
            script_input_tokens=script_input_tokens,
            script_output_tokens=script_output_tokens,
            tts_characters=tts_characters,
            dub_count=len(dub_languages) if dub_languages else 0
        )
        
        entry = {
            "id": int(time.time() * 1000),
            "timestamp": now,
            "date": now.strftime("%d %b %Y"),
            "time": now.strftime("%I:%M %p IST"),
            "user": user_email,
            "topic": topic[:100],
            "language": language,
            "engine": engine,
            "voice": voice,
            "status": status,
            "error": error_message,
            
            # Script metrics
            "script_length_chars": len(script) if script else 0,
            "script_word_count": len(script.split()) if script else 0,
            "script_input_tokens": script_input_tokens,
            "script_output_tokens": script_output_tokens,
            
            # Video metrics
            "duration_requested": duration_requested,
            "video_duration_actual": video_duration_actual,
            "video_file_size_mb": round(video_file_size_bytes / (1024 * 1024), 2) if video_file_size_bytes else 0,
            "video_model": video_model,
            
            # TTS metrics
            "tts_characters": tts_characters,
            "tts_voice": voice,
            
            # Post-processing
            "captions_enabled": captions_enabled,
            "caption_style": caption_style,
            "formats_generated": formats_generated or [],
            "dub_languages": dub_languages or [],
            
            # Cost breakdown
            "cost": cost_breakdown,
        }
        
        # Insert into MongoDB
        db.generations.insert_one(entry)
        
        # Update aggregate stats
        update_doc = {
            "$inc": {
                "total_generations": 1,
                "total_script_tokens.input": script_input_tokens,
                "total_script_tokens.output": script_output_tokens,
                "total_video_seconds": video_duration_actual or duration_requested,
                "total_tts_characters": tts_characters,
                "total_estimated_cost_usd": cost_breakdown["total_usd"]
            }
        }
        
        if captions_enabled: update_doc["$inc"]["total_caption_burns"] = 1
        if formats_generated: update_doc["$inc"]["total_format_conversions"] = len(formats_generated)
        if dub_languages: update_doc["$inc"]["total_dub_translations"] = len(dub_languages)
        
        db.stats.update_one({"type": "overall_usage"}, update_doc, upsert=True)
        
        # Clean ID for response
        entry["_id"] = str(entry["_id"])
        return entry

    def _calculate_costs(self, **kwargs) -> dict:
        # Simplified logic based on provided pricing
        # Inputting similar logic as before
        video_duration = kwargs.get("video_duration", 0)
        script_input_tokens = kwargs.get("script_input_tokens", 0)
        script_output_tokens = kwargs.get("script_output_tokens", 0)
        dub_count = kwargs.get("dub_count", 0)
        
        # Assume Flash for now
        script_cost = 0.0 # Free tiers
        video_cost = 0.0
        
        total = script_cost + video_cost
        return {
            "total_usd": round(total, 6),
            "total_inr": round(total * 83, 2),
            "total_paid_usd": round(video_duration * 0.35, 4), # Logic for visualization
        }

    def get_summary(self, db: Database) -> dict:
        """Get overall usage summary from MongoDB."""
        stats = db.stats.find_one({"type": "overall_usage"}) or {}
        recent = list(db.generations.find().sort("timestamp", -1).limit(10))
        for r in recent: r["_id"] = str(r["_id"])
        
        return {
            "total_generations": stats.get("total_generations", 0),
            "total_script_tokens": stats.get("total_script_tokens", {"input": 0, "output": 0}),
            "total_video_seconds": round(stats.get("total_video_seconds", 0), 1),
            "total_estimated_cost_usd": round(stats.get("total_estimated_cost_usd", 0.0), 4),
            "recent_generations": recent,
        }

    def get_daily_stats(self, db: Database) -> dict:
        """Get today's usage stats from MongoDB."""
        today_str = datetime.now(IST).strftime("%d %b %Y")
        today_gens = list(db.generations.find({"date": today_str}))
        
        total_cost = sum(g["cost"]["total_usd"] for g in today_gens)
        total_tokens = sum(g.get("script_input_tokens", 0) + g.get("script_output_tokens", 0) for g in today_gens)
        
        for g in today_gens: g["_id"] = str(g["_id"])
        
        return {
            "date": today_str,
            "generation_count": len(today_gens),
            "total_tokens": total_tokens,
            "total_cost_usd": round(total_cost, 4),
            "generations": today_gens
        }

usage_service = UsageService()
