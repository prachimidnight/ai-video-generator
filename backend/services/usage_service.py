"""
Usage Tracking Service - Tracks API token usage, costs, and generation history in MongoDB.
"""

import time
from datetime import datetime, timezone, timedelta
from typing import Optional, List
from pymongo.database import Database

# IST timezone
IST = timezone(timedelta(hours=5, minutes=30))

# Currency conversion (keep consistent everywhere)
USD_TO_INR = 85.0

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
        """Calculate real costs based on token/time usage."""
        video_model = kwargs.get("video_model", "veo-3.1-fast-generate-preview")
        video_duration = kwargs.get("video_duration", 0)
        script_input_tokens = kwargs.get("script_input_tokens", 0)
        script_output_tokens = kwargs.get("script_output_tokens", 0)
        tts_characters = kwargs.get("tts_characters", 0)
        dub_count = kwargs.get("dub_count", 0)
        
        # 1. Script Generation Cost (Gemini)
        # Default to flash if model unknown
        model_rates = PRICING.get("gemini-1.5-pro", { "input_per_1k_tokens": 1.25, "output_per_1k_tokens": 5.00 })
        script_cost = (script_input_tokens / 1000 * model_rates["input_per_1k_tokens"]) + \
                      (script_output_tokens / 1000 * model_rates["output_per_1k_tokens"])
        
        # 2. Video Generation Cost (Veo)
        veo_rates = PRICING.get(video_model, PRICING["veo-3.1-fast-generate-preview"])
        video_cost = video_duration * veo_rates.get("per_second", 0.35)
        
        # 3. TTS Cost (Approximate $15 per 1M characters -> $0.000015 per char)
        tts_cost = tts_characters * 0.000015
        
        # 4. Dubbing Cost ($0.10 per language)
        dub_cost = dub_count * 0.10
        
        total = script_cost + video_cost + tts_cost + dub_cost
        return {
            "script_usd": round(script_cost, 6),
            "video_usd": round(video_cost, 6),
            "tts_usd": round(tts_cost, 6),
            "dub_usd": round(dub_cost, 6),
            "total_usd": round(total, 4),
            "total_inr": round(total * USD_TO_INR, 2),
            "breakdown": {
                "tokens": script_input_tokens + script_output_tokens,
                "duration": round(video_duration, 1),
                "chars": tts_characters,
                "languages": dub_count
            }
        }

    def get_model_usage(self, db: Database) -> list:
        """Get usage stats grouped by model for the admin panel."""
        pipeline = [
            {
                "$group": {
                    "_id": "$video_model",
                    "count": {"$sum": 1},
                    "total_cost": {"$sum": "$cost.total_usd"},
                    "total_seconds": {"$sum": "$video_duration_actual"}
                }
            },
            {
                "$project": {
                    "name": "$_id",
                    "queries": "$count",
                    "revenue": "$total_cost",
                    "seconds": "$total_seconds"
                }
            }
        ]
        results = list(db.generations.aggregate(pipeline))
        # Add display details
        for res in results:
            if not res["name"]: res["name"] = "Unknown"
            res["share"] = round((res["queries"] / sum(r["queries"] for r in results) * 100) if results else 0, 1)
            res["revenue_inr"] = round(res["revenue"] * USD_TO_INR, 2)
        return results

    def get_summary(self, db: Database) -> dict:
        """Get overall usage summary from MongoDB."""
        stats = db.stats.find_one({"type": "overall_usage"}) or {}
        # Fetch actual sum for cost if stats are out of sync
        if not stats.get("total_estimated_cost_usd"):
            actual_cost = list(db.generations.aggregate([{"$group": {"_id": None, "total": {"$sum": "$cost.total_usd"}}}]))
            stats["total_estimated_cost_usd"] = actual_cost[0]["total"] if actual_cost else 0.0

        recent = list(db.generations.find().sort("timestamp", -1).limit(10))
        for r in recent: r["_id"] = str(r["_id"])
        
        return {
            "total_generations": stats.get("total_generations", 0),
            "total_script_tokens": stats.get("total_script_tokens", {"input": 0, "output": 0}),
            "total_video_seconds": round(stats.get("total_video_seconds", 0), 1),
            "total_estimated_cost_usd": round(stats.get("total_estimated_cost_usd", 0.0), 4),
            "total_estimated_cost_inr": round(stats.get("total_estimated_cost_usd", 0.0) * USD_TO_INR, 2),
            "recent_generations": recent,
        }

    def get_daily_stats(self, db: Database) -> dict:
        """Get today's usage stats from MongoDB."""
        today_str = datetime.now(IST).strftime("%d %b %Y")
        today_gens = list(db.generations.find({"date": today_str}))
        
        total_cost = sum(g.get("cost", {}).get("total_usd", 0) for g in today_gens)
        total_tokens = sum(g.get("script_input_tokens", 0) + g.get("script_output_tokens", 0) for g in today_gens)
        
        for g in today_gens: 
            g["_id"] = str(g["_id"])
            if "timestamp" in g: g["timestamp"] = str(g["timestamp"])
        
        return {
            "date": today_str,
            "generation_count": len(today_gens),
            "total_tokens": total_tokens,
            "total_cost_usd": round(total_cost, 4),
            "generations": today_gens
        }

usage_service = UsageService()
