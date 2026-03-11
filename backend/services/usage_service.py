"""
Usage Tracking Service - Tracks API token usage, costs, and generation history.

Stores all usage data in a local JSON file for easy access.
Tracks:
- Gemini Script tokens (input/output)
- Gemini Veo video generation (seconds, estimated cost)
- TTS usage (characters, voice)
- D-ID usage (credits)
- Total cost per generation and cumulative
"""

import os
import json
import time
from datetime import datetime, timezone, timedelta
from typing import Optional

USAGE_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "usage_log.json")

# IST timezone
IST = timezone(timedelta(hours=5, minutes=30))

# Pricing - Now tracked primary via Langfuse
# This table is kept for local historical logging if needed
PRICING = {
    "gemini-2.0-flash": {
        "input_per_1k_tokens": 0.0,       # Tracked in Langfuse
        "output_per_1k_tokens": 0.0,
    },
    "veo-3.1-fast-generate-preview": {
        "per_second": 0.0,                # Tracked in Langfuse
        "free_tier": True,
    },
    "d-id": {
        "per_credit": 0.0,
        "credits_per_video": 1,
    }
}


class UsageService:
    def __init__(self):
        self.usage_data = self._load_data()

    def _load_data(self) -> dict:
        """Load existing usage data from file."""
        if os.path.exists(USAGE_FILE):
            try:
                with open(USAGE_FILE, "r") as f:
                    return json.load(f)
            except (json.JSONDecodeError, Exception):
                pass
        
        return {
            "total_generations": 0,
            "total_script_tokens": {"input": 0, "output": 0},
            "total_video_seconds": 0,
            "total_tts_characters": 0,
            "total_estimated_cost_usd": 0.0,
            "total_dub_translations": 0,
            "total_caption_burns": 0,
            "total_format_conversions": 0,

            "generations": [
                {
                    "id": "gen-123",
                    "user": "aadil.sayyad@company.com",
                    "date": "06 Mar 2026",
                    "cost": {"total_usd": 0.0015, "total_inr": 0.12}
                },
                {
                    "id": "gen-124",
                    "user": "aadil.sayyad@company.com",
                    "date": "06 Mar 2026",
                    "cost": {"total_usd": 0.0015, "total_inr": 0.12}
                },
                {
                    "id": "gen-125",
                    "user": "aadil.sayyad@company.com",
                    "date": "07 Mar 2026",
                    "cost": {"total_usd": 0.0015, "total_inr": 0.13}
                },
                {
                    "id": "gen-126",
                    "user": "rahul.sharma@startup.in",
                    "date": "06 Mar 2026",
                    "cost": {"total_usd": 0.0015, "total_inr": 0.12}
                },
                {
                    "id": "gen-127",
                    "user": "rahul.sharma@startup.in",
                    "date": "07 Mar 2026",
                    "cost": {"total_usd": 0.0015, "total_inr": 0.13}
                }
            ]
        }

    def _save_data(self):
        """Save usage data to file."""
        try:
            with open(USAGE_FILE, "w") as f:
                json.dump(self.usage_data, f, indent=2, default=str)
        except Exception as e:
            print(f"ERROR: Failed to save usage data: {e}")

    def log_generation(
        self,
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
    ) -> dict:
        """
        Log a complete video generation with all usage metrics.
        Returns the generation log entry.
        """
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
            "timestamp": now.isoformat(),
            "date": now.strftime("%d %b %Y"),
            "time": now.strftime("%I:%M %p IST"),
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
        
        # Update totals
        self.usage_data["total_generations"] += 1
        self.usage_data["total_script_tokens"]["input"] += script_input_tokens
        self.usage_data["total_script_tokens"]["output"] += script_output_tokens
        self.usage_data["total_video_seconds"] += video_duration_actual or duration_requested
        self.usage_data["total_tts_characters"] += tts_characters
        self.usage_data["total_estimated_cost_usd"] += cost_breakdown["total_usd"]
        if captions_enabled:
            self.usage_data["total_caption_burns"] += 1
        if formats_generated:
            self.usage_data["total_format_conversions"] += len(formats_generated)
        if dub_languages:
            self.usage_data["total_dub_translations"] += len(dub_languages)
        
        # Prepend to generations list (newest first), keep last 100
        self.usage_data["generations"].insert(0, entry)
        self.usage_data["generations"] = self.usage_data["generations"][:100]
        
        self._save_data()
        print(f"USAGE: Logged generation #{self.usage_data['total_generations']} | "
              f"Cost: ${cost_breakdown['total_usd']:.4f} | "
              f"Script: {script_input_tokens}+{script_output_tokens} tokens | "
              f"Video: {video_duration_actual}s")
        
        return entry

    def _calculate_costs(
        self,
        engine: str,
        video_model: str,
        video_duration: float,
        script_input_tokens: int,
        script_output_tokens: int,
        tts_characters: int,
        dub_count: int = 0
    ) -> dict:
        """Calculate estimated costs for a generation."""
        
        # Script cost (Gemini Flash)
        # Use gemini-flash-latest as default since it's the most reliable alias in this environment
        flash_pricing = PRICING.get("gemini-flash-latest", {})
        script_input_cost = (script_input_tokens / 1000) * flash_pricing.get("input_per_1k_tokens", 0)
        script_output_cost = (script_output_tokens / 1000) * flash_pricing.get("output_per_1k_tokens", 0)
        script_cost = script_input_cost + script_output_cost
        
        # Video cost
        video_cost = 0.0
        if engine == "gemini":
            model_key = video_model or "veo-3.1-fast-generate-preview"
            veo_pricing = PRICING.get(model_key, {})
            if veo_pricing.get("free_tier"):
                video_cost = 0.0  # Preview = free
                video_cost_paid = video_duration * veo_pricing.get("per_second", 0.35)
            else:
                video_cost = video_duration * veo_pricing.get("per_second", 0.35)
                video_cost_paid = video_cost
        elif engine == "did":
            did_pricing = PRICING.get("d-id", {})
            video_cost = did_pricing.get("credits_per_video", 1) * did_pricing.get("per_credit", 0)
            video_cost_paid = video_cost
        else:
            video_cost_paid = 0.0
        
        # TTS cost (Edge TTS = free)
        tts_cost = 0.0
        
        # Dubbing cost (translation tokens)
        dub_cost = 0.0
        if dub_count > 0:
            # Each dub = ~translation tokens + TTS
            est_translation_tokens = script_output_tokens * dub_count
            dub_cost = (est_translation_tokens / 1000) * flash_pricing.get("input_per_1k_tokens", 0)
        
        total = script_cost + video_cost + tts_cost + dub_cost
        total_paid = script_cost + video_cost_paid + tts_cost + dub_cost
        
        return {
            "script_usd": round(script_cost, 6),
            "video_usd": round(video_cost, 6),
            "video_usd_if_paid": round(video_cost_paid, 4),
            "tts_usd": round(tts_cost, 6),
            "dub_usd": round(dub_cost, 6),
            "total_usd": round(total, 6),
            "total_paid_usd": round(total_paid, 4),
            "total_inr": round(total * 83, 2),
            "total_paid_inr": round(total_paid * 83, 2),
            "pricing_note": "Free tiers are active. Costs shown are based on standard pay-as-you-go rates."
        }

    def get_summary(self) -> dict:
        """Get overall usage summary."""
        data = self.usage_data
        return {
            "total_generations": data["total_generations"],
            "total_script_tokens": data["total_script_tokens"],
            "total_video_seconds": round(data["total_video_seconds"], 1),
            "total_video_minutes": round(data["total_video_seconds"] / 60, 2),
            "total_tts_characters": data["total_tts_characters"],
            "total_estimated_cost_usd": round(data["total_estimated_cost_usd"], 4),
            "total_estimated_cost_inr": round(data["total_estimated_cost_usd"] * 83, 2),
            "total_dub_translations": data.get("total_dub_translations", 0),
            "total_caption_burns": data.get("total_caption_burns", 0),
            "total_format_conversions": data.get("total_format_conversions", 0),
            "recent_generations": data["generations"][:10],
        }

    def get_generation_by_id(self, gen_id: int) -> Optional[dict]:
        """Get a specific generation log by ID."""
        for gen in self.usage_data["generations"]:
            if gen["id"] == gen_id:
                return gen
        return None

    def get_daily_stats(self) -> dict:
        """Get today's usage stats."""
        today = datetime.now(IST).strftime("%d %b %Y")
        today_gens = [g for g in self.usage_data["generations"] if g.get("date") == today]
        
        total_cost = sum(g["cost"]["total_usd"] for g in today_gens)
        total_video_secs = sum(g.get("video_duration_actual", 0) or g.get("duration_requested", 0) for g in today_gens)
        total_tokens = sum(g.get("script_input_tokens", 0) + g.get("script_output_tokens", 0) for g in today_gens)
        
        return {
            "date": today,
            "generation_count": len(today_gens),
            "total_video_seconds": round(total_video_secs, 1),
            "total_tokens": total_tokens,
            "total_cost_usd": round(total_cost, 4),
            "total_cost_inr": round(total_cost * 83, 2),
            "generations": today_gens
        }


# Singleton
usage_service = UsageService()
