from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.concurrency import run_in_threadpool
import shutil
import os
import uuid
import json
from typing import Optional
from services.gemini_service import generate_script, generate_visual_prompt
from services.tts_service import generate_audio
from services.gemini_video_service import gemini_video_service
from services.caption_service import add_captions_to_video, generate_srt, save_srt_file, get_video_duration
from services.format_service import convert_single_format, convert_to_all_formats
from services.translation_service import translation_service
from services.usage_service import usage_service
import time
from pymongo.database import Database
from fastapi import Depends
import models
import schemas
import auth
from database import get_db
from services.credit_service import credit_service

app = FastAPI(title="AI Video Generator API")

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173", 
        "http://127.0.0.1:5173",
        "https://ai-video-generator.prachi-0eb.workers.dev"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def add_ngrok_skip_header(request, call_next):
    response = await call_next(request)
    response.headers["ngrok-skip-browser-warning"] = "69420"
    return response

# Create temp dir if not exists
temp_dir = os.path.join(os.getcwd(), "temp")
if not os.path.exists(temp_dir):
    os.makedirs(temp_dir)

# Mount the temp folder to serve audio/video files
app.mount("/temp", StaticFiles(directory=temp_dir), name="temp")

@app.get("/")
async def root():
    return {"message": "Welcome to the AI Video Generator API"}

@app.post("/signup", response_model=schemas.UserResponse)
def signup(user: schemas.UserCreate, db: Database = Depends(get_db)):
    # Check if user exists
    db_user = db.users.find_one({"email": user.email})
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Hash password
    hashed_password = auth.get_password_hash(user.password)
    
    # Create user
    new_user = models.User(
        full_name=user.full_name,
        email=user.email,
        password_hash=hashed_password
    )
    user_dict = new_user.model_dump()
    db.users.insert_one(user_dict)
    
    return user_dict

@app.post("/login")
def login(email: str = Form(...), password: str = Form(...), db: Database = Depends(get_db)):
    user = db.users.find_one({"email": email, "status": True})
    if not user or not auth.verify_password(password, user.get("password_hash")):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    return {
        "status": "success",
        "message": "Login successful",
        "user": {
            "guid": user.get("guid"),
            "full_name": user.get("full_name"),
            "email": user.get("email"),
            "subscription_tier": user.get("subscription_tier", "basic"),
            "available_credits": user.get("available_credits", 2)
        }
    }

@app.post("/logout")
def logout():
    return {"status": "success", "message": "Logged out successfully"}

@app.get("/user/credits")
def get_user_credits(email: str, db: Database = Depends(get_db)):
    """GET current credit balance for a user."""
    return credit_service.get_credits(db, email)

@app.post("/draft-script")
async def draft_script(
    topic: str = Form(...),
    language: str = Form("English"),
    duration: int = Form(15),
    user_email: str = Form(...),  # Tracking user
    script_model: str = Form("gemini-2.5-flash") # The AI model for the script
):
    """Step 1: Just generate the script draft."""
    try:
        print(f"Drafting script for topic: {topic} ({language}, {duration}s) using {script_model}")
        script, in_tokens, out_tokens = generate_script(topic, language, duration, model_name=script_model)
        
        return {"script": script, "input_tokens": in_tokens, "output_tokens": out_tokens}
    except Exception as e:
        import traceback
        error_msg = traceback.format_exc()
        print(f"ERROR in draft-script: {error_msg}")
        return JSONResponse(status_code=500, content={"error": str(e), "traceback": error_msg})

@app.post("/generate")
async def generate_video(
    topic: str = Form(...),
    image: UploadFile = File(...),
    script: str = Form(...),
    voice: str = Form("en-US-AndrewNeural"),
    language: str = Form("English"),
    speed: int = Form(0),
    pitch: int = Form(0),
    background_type: str = Form("original"),
    music: str = Form("none"),
    duration: int = Form(15),
    aspect_ratio: str = Form("16:9"),
    music_volume: float = Form(0.2),
    engine: str = Form("gemini"),
    veo_quality: str = Form("fast"), # 'fast' or 'standard'
    # New parameters for captions
    captions_enabled: str = Form("false"),
    caption_style: str = Form("default"),
    # New parameters for multi-format
    generate_all_formats: str = Form("false"),
    # New parameters for auto-dubbing
    dub_languages: str = Form(""),  # Comma-separated list of languages
    user_email: str = Form(...),    # User who pays for this
    db: Database = Depends(get_db)
):
    """
    Step 2: Pro pipeline with full customization.
    Now supports auto-captions, multi-format, and auto-dubbing.
    """
    # 0. Credit Check & Deduction
    # This happens BEFORE we start the expensive generation
    remaining_credits = credit_service.deduct_credits(db, user_email, credits_to_deduct=1)
    print(f"User {user_email} charged 1 credit. Remaining: {remaining_credits}")

    print(f"--- Starting Advanced Video Generation ({engine}) ---")
    
    # 1. Save Image
    ext = os.path.splitext(image.filename)[1] or ".jpg"
    image_filename = f"avatar_{uuid.uuid4().hex}{ext}"
    image_path = os.path.join(temp_dir, image_filename)
    with open(image_path, "wb") as buffer:
        buffer.write(await image.read())
    
    image_url = f"{os.getenv('BASE_URL', 'http://localhost:8000')}/temp/{image_filename}"

    # 2. TTS with custom settings
    print(f"Generating audio with voice: {voice}...")
    audio_filename = f"video_audio_{int(time.time())}.mp3"
    try:
        audio_path = await generate_audio(script, audio_filename, voice=voice, speed=speed, pitch=pitch)
    except Exception as e:
        print(f"ERROR: Audio Generation Failed: {e}")
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": f"Audio service timeout (TTS). Please check your internet connection or try a different voice."}
        )
    
    audio_url = f"{os.getenv('BASE_URL', 'http://localhost:8000')}/temp/{audio_filename}"

    # 3. Generation Logic (Gemini Only)
    print(f"Creating cinematic video with Gemini Veo ({veo_quality})...")
    # Ensure duration is within Veo 3.1 bounds (4-8s)
    target_duration = min(duration, 8) if duration >= 4 else 6
    
    # Humanization Step: Transform script into a visual-first prompt
    print(f"DEBUG: Enhancing visual prompt for humanization...")
    visual_prompt = generate_visual_prompt(script, topic)
    print(f"DEBUG: Using Visual Prompt: {visual_prompt[:100]}...")

    try:
        local_filename = await gemini_video_service.generate_video(
            visual_prompt, image_path, 
            duration=target_duration, 
            aspect_ratio=aspect_ratio,
            quality=veo_quality
        )
        if local_filename:
            video_url = f"{os.getenv('BASE_URL', 'http://localhost:8000')}/temp/{local_filename}"
            local_video_path = os.path.join(temp_dir, local_filename)
            
            video_url = f"{os.getenv('BASE_URL', 'http://localhost:8000')}/temp/{local_filename}"
            local_video_path = os.path.join(temp_dir, local_filename)
    except Exception as e:
        error_msg = str(e)
        print(f"ERROR: Gemini Generation Failed: {error_msg}")
        status_code = 500
        if "RESOURCE_EXHAUSTED" in error_msg or "429" in error_msg:
            error_msg = "Gemini API Quota Exceeded (Rate Limit). Please wait a minute and try again."
            status_code = 429
        
        return JSONResponse(
            status_code=status_code,
            content={"status": "error", "message": error_msg}
        )
    
    if not video_url:
        return {
            "status": "error",
            "message": f"{engine.upper()} generation failed. Please check your credits/API key."
        }
    
    # === POST-PROCESSING PIPELINE ===
    
    # 4. Auto Captions
    captioned_video_url = None
    if captions_enabled == "true" and local_video_path and os.path.exists(local_video_path):
        print(f"Adding captions (style: {caption_style})...")
        try:
            captioned_filename = await add_captions_to_video(
                local_video_path, script,
                caption_style=caption_style,
                aspect_ratio=aspect_ratio
            )
            if captioned_filename:
                captioned_video_url = f"{os.getenv('BASE_URL', 'http://localhost:8000')}/temp/{captioned_filename}"

                # Use captioned version as the main video
                video_url = captioned_video_url
                local_video_path = os.path.join(temp_dir, captioned_filename)
                print(f"Captions added successfully!")
        except Exception as e:
            print(f"WARNING: Caption generation failed (non-fatal): {e}")
    
    # 5. Multi-Format Output
    format_urls = {}
    if generate_all_formats == "true" and local_video_path and os.path.exists(local_video_path):
        print("Generating all format variants...")
        try:
            format_results = await convert_to_all_formats(local_video_path, original_ratio=aspect_ratio)
            for ratio, filename in format_results.items():
                format_urls[ratio] = f"{os.getenv('BASE_URL', 'http://localhost:8000')}/temp/{filename}"

            print(f"Generated {len(format_urls)} format(s)")
        except Exception as e:
            print(f"WARNING: Multi-format generation failed (non-fatal): {e}")
    
    # 6. Auto-Dubbing
    dub_results = []
    if dub_languages:
        languages_list = [lang.strip() for lang in dub_languages.split(",") if lang.strip()]
        if languages_list:
            print(f"Auto-dubbing to: {', '.join(languages_list)}...")
            try:
                dub_results = await translation_service.auto_dub(
                    script, language, languages_list,
                    speed=speed, pitch=pitch
                )
                # Convert audio paths to URLs
                for dub in dub_results:
                    if dub.get("audio_filename"):
                        dub["audio_url"] = f"{os.getenv('BASE_URL', 'http://localhost:8000')}/temp/{dub['audio_filename']}"

                    # Remove file system paths from response
                    dub.pop("audio_path", None)
                print(f"Auto-dubbing complete for {len(dub_results)} language(s)")
            except Exception as e:
                print(f"WARNING: Auto-dubbing failed (non-fatal): {e}")

    # === USAGE TRACKING ===
    video_duration_actual = 0
    video_file_size = 0
    video_model_used = ""
    if local_video_path and os.path.exists(local_video_path):
        video_file_size = os.path.getsize(local_video_path)
        video_model_used = "veo-3.1-fast-generate-preview"
        # Try to get actual duration
        try:
            duration_val = get_video_duration(local_video_path)
            if duration_val:
                video_duration_actual = duration_val
        except:
            video_duration_actual = min(duration, 8)
    print(f"DEBUG: Logging generation - Topic: {topic}, Language: {language}")
    # Log usage in MongoDB
    usage_entry = usage_service.log_generation(
        db=db,
        topic=topic,
        script=script,
        language=language,
        engine=engine,
        voice=voice,
        duration_requested=duration,
        video_duration_actual=video_duration_actual,
        video_file_size_bytes=video_file_size,
        script_input_tokens=0,
        script_output_tokens=0,
        tts_characters=len(script),
        captions_enabled=(captions_enabled == "true"),
        caption_style=caption_style if captions_enabled == "true" else "",
        formats_generated=list(format_urls.keys()),
        dub_languages=[lang.strip() for lang in dub_languages.split(",") if lang.strip()],
        video_model=video_model_used,
        user_email=user_email
    )

    # Build response
    response_data = {
        "topic": topic,
        "script": script,
        "audio_url": audio_url,
        "image_url": image_url,
        "video_url": video_url,
        "usage": usage_entry if usage_entry else {},
    }
    
    # Add optional data
    if format_urls:
        response_data["format_urls"] = format_urls
    
    if dub_results:
        response_data["dub_results"] = dub_results
    
    if captioned_video_url:
        response_data["captioned_video_url"] = captioned_video_url
    
    return {
        "status": "success",
        "data": response_data
    }


@app.post("/generate-voice")
async def generate_voice(
    script: str = Form(...),
    voice: str = Form("en-US-AndrewNeural"),
    speed: int = Form(0),
    pitch: int = Form(0)
):
    """Standalone TTS generation."""
    print(f"Generating audio only with voice: {voice}...")
    audio_filename = f"audio_only_{int(time.time())}.mp3"
    try:
        audio_path = await generate_audio(script, audio_filename, voice=voice, speed=speed, pitch=pitch)
        audio_url = f"{os.getenv('BASE_URL', 'http://localhost:8000')}/temp/{audio_filename}"
        return {
            "status": "success",
            "data": {
                "audio_url": audio_url,
                "filename": audio_filename
            }
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": f"Audio generation failed: {str(e)}"}
        )


# ========================
# STANDALONE POST-PROCESSING ENDPOINTS
# ========================

@app.post("/translate-script")
async def translate_script_endpoint(
    script: str = Form(...),
    source_language: str = Form("English"),
    target_language: str = Form(...)
):
    """Translate a script from one language to another."""
    print(f"Translating script from {source_language} to {target_language}...")
    try:
        translated = translation_service.translate_script(script, source_language, target_language)
        return {
            "status": "success",
            "data": {
                "original_language": source_language,
                "target_language": target_language,
                "translated_script": translated
            }
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": f"Translation failed: {str(e)}"}
        )


@app.post("/auto-dub")
async def auto_dub_endpoint(
    script: str = Form(...),
    source_language: str = Form("English"),
    target_languages: str = Form(...),  # Comma-separated
    speed: int = Form(0),
    pitch: int = Form(0)
):
    """Auto-translate and generate dubbed audio for multiple languages."""
    langs = [l.strip() for l in target_languages.split(",") if l.strip()]
    if not langs:
        return JSONResponse(
            status_code=400,
            content={"status": "error", "message": "No target languages provided."}
        )

    print(f"Auto-dubbing from {source_language} to: {', '.join(langs)}...")
    try:
        results = await translation_service.auto_dub(
            script, source_language, langs,
            speed=speed, pitch=pitch
        )

        for dub in results:
            if dub.get("audio_path"):
                dub["audio_url"] = f"{os.getenv('BASE_URL', 'http://localhost:8000')}/temp/{dub['audio_filename']}"
            dub.pop("audio_path", None)

        return {
            "status": "success",
            "data": {
                "source_language": source_language,
                "dubs": results
            }
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": f"Auto-dubbing failed: {str(e)}"}
        )


@app.post("/add-captions")
async def add_captions_endpoint(
    video_filename: str = Form(...),
    script: str = Form(...),
    caption_style: str = Form("default"),
    aspect_ratio: str = Form("16:9")
):
    """Add captions/subtitles to an existing video."""
    video_path = os.path.join(temp_dir, video_filename)
    if not os.path.exists(video_path):
        return JSONResponse(
            status_code=404,
            content={"status": "error", "message": "Video file not found."}
        )

    print(f"Adding captions to {video_filename}...")
    try:
        captioned = await add_captions_to_video(
            video_path, script,
            caption_style=caption_style,
            aspect_ratio=aspect_ratio
        )
        if captioned:
            return {
                "status": "success",
                "data": {
                    "captioned_video_url": f"{os.getenv('BASE_URL', 'http://localhost:8000')}/temp/{captioned}"
                }
            }
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": "Caption generation failed. Is ffmpeg installed?"}
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": f"Caption generation failed: {str(e)}"}
        )


@app.post("/convert-format")
async def convert_format_endpoint(
    video_filename: str = Form(...),
    target_ratio: str = Form(...),
    mode: str = Form("fit")
):
    """Convert a video to a different aspect ratio."""
    video_path = os.path.join(temp_dir, video_filename)
    if not os.path.exists(video_path):
        return JSONResponse(
            status_code=404,
            content={"status": "error", "message": "Video file not found."}
        )

    print(f"Converting {video_filename} to {target_ratio}...")
    try:
        converted = await convert_single_format(video_path, target_ratio, mode=mode)
        if converted:
            return {
                "status": "success",
                "data": {
                    "converted_video_url": f"{os.getenv('BASE_URL', 'http://localhost:8000')}/temp/{converted}",
                    "format": target_ratio
                }
            }
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": "Format conversion failed. Is ffmpeg installed?"}
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": f"Format conversion failed: {str(e)}"}
        )


@app.post("/generate-all-formats")
async def generate_all_formats_endpoint(
    video_filename: str = Form(...),
    original_ratio: str = Form("16:9"),
    mode: str = Form("fit")
):
    """Generate all three format variants of a video."""
    video_path = os.path.join(temp_dir, video_filename)
    if not os.path.exists(video_path):
        return JSONResponse(
            status_code=404,
            content={"status": "error", "message": "Video file not found."}
        )

    print(f"Generating all formats for {video_filename}...")
    try:
        results = await convert_to_all_formats(video_path, original_ratio=original_ratio, mode=mode)
        base_url = os.getenv('BASE_URL', 'http://localhost:8000')
        format_urls = {ratio: f"{base_url}/temp/{filename}" for ratio, filename in results.items()}

        return {
            "status": "success",
            "data": {
                "formats": format_urls
            }
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": f"Format generation failed: {str(e)}"}
        )




# ========================
# USAGE TRACKING ENDPOINTS
# ========================

@app.get("/admin/usage-summary")
async def get_usage_summary(db: Database = Depends(get_db)):
    """Get high-level usage metrics for admin dashboard."""
    return {
        "status": "success",
        "data": usage_service.get_summary(db)
    }

@app.get("/admin/daily-stats")
async def get_daily_stats(db: Database = Depends(get_db)):
    """Get usage statistics for the current day."""
    return {
        "status": "success",
        "data": usage_service.get_daily_stats(db)
    }

@app.post("/admin/reset-stats")
async def reset_stats(db: Database = Depends(get_db)):
    """Reset all usage statistics (Admin only)."""
    db.stats.delete_one({"type": "overall_usage"})
    db.generations.delete_many({})
    return {"status": "success", "message": "Stats reset successfully"}


@app.get("/admin/users")
async def get_admin_users(db: Database = Depends(get_db)):
    """Get list of users for admin panel from real database."""
    users = list(db.users.find({"status": True}))
    user_list = []
    for u in users:
        user_list.append({
            "id": u.get("id") or u.get("guid"),
            "name": u.get("full_name"),
            "email": u.get("email"),
            "tier": u.get("subscription_tier", "basic").capitalize(),
            "status": "Active" if u.get("status") else "Inactive",
            "usage": u.get("available_credits"), # Showing credits as usage/balance
            "joined": u.get("created_at").strftime("%d %b %Y") if hasattr(u.get("created_at"), "strftime") else str(u.get("created_at"))
        })
    return {
        "status": "success",
        "data": user_list
    }


@app.put("/admin/users/{user_id}")
async def update_admin_user(user_id: str, user_update: schemas.UserUpdate, db: Database = Depends(get_db)):
    """Update user details as an admin."""
    # Assuming user_id passed from frontend is the guid or id string
    db_user = db.users.find_one({"$or": [{"guid": user_id}, {"id": user_id}], "status": True})
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    update_data = user_update.model_dump(exclude_unset=True)
    db.users.update_one({"_id": db_user["_id"]}, {"$set": update_data})
    
    # Return updated
    db_user.update(update_data)
    # Fix ObjectId serialization issue
    db_user["_id"] = str(db_user["_id"])
    return {"status": "success", "message": "User updated successfully", "data": db_user}


@app.delete("/admin/users/{user_id}")
async def delete_admin_user(user_id: str, db: Database = Depends(get_db)):
    """Soft delete a user as an admin (set status to False)."""
    db_user = db.users.find_one({"$or": [{"guid": user_id}, {"id": user_id}], "status": True})
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    db.users.update_one({"_id": db_user["_id"]}, {"$set": {"status": False}})
    return {"status": "success", "message": "User deleted successfully"}


@app.get("/admin/stats")
async def get_admin_stats(db: Database = Depends(get_db)):
    """Get high-level system metrics."""
    total_users = db.users.count_documents({"status": True})
    usage = usage_service.get_summary(db)
    
    # Calculate revenue from transactions
    transactions = list(db.transactions.find({"status": "Completed"}))
    total_revenue_inr = 0
    for tx in transactions:
        try:
            # Extract number from string like "₹1,499"
            amt_str = tx.get("amount", "0").replace("₹", "").replace(",", "")
            total_revenue_inr += int(amt_str)
        except:
            continue
            
    # Calculate a dynamic system load based on recent activity (last 1 hour)
    one_hour_ago = datetime.now(IST) - timedelta(hours=1)
    recent_gens_count = db.generations.count_documents({"timestamp": {"$gt": one_hour_ago}})
    # Simple heuristic: 10 concurrent generations = 100% load
    load_percent = min(100, (recent_gens_count / 10) * 100)
    
    return {
        "status": "success",
        "data": {
            "total_users": total_users,
            "total_generations": usage["total_generations"],
            "total_revenue_inr": total_revenue_inr,
            "system_load": f"{load_percent:.1f}%",
            "revenue_formatted": f"₹{total_revenue_inr/100000:.1f}L" if total_revenue_inr >= 100000 else f"₹{total_revenue_inr:,}"
        }
    }


@app.get("/admin/top-users")
async def get_admin_top_users(db: Database = Depends(get_db)):
    """Get the top users by total transaction cost and query count."""
    gens = list(db.generations.find())
    
    user_stats = {}
    for gen in gens:
        email = gen.get("user_email", "Unknown")
        cost = gen.get("cost", {}).get("total_usd", 0.0)
        
        if email not in user_stats:
            # Basic dummy resolving of names from emails (since usage_data stores emails directly)
            parts = email.split('@')[0].split('.')
            name = " ".join([p.capitalize() for p in parts]) if len(parts)>0 else email
            initials = "".join([p[0].upper() for p in parts])[:2] if len(parts)>0 else "U"

            user_stats[email] = {
                "name": name,
                "initials": initials,
                "queries": 0,
                "total_cost_usd": 0.0,
                "total_cost_inr": 0.0
            }
        
        user_stats[email]["queries"] += 1
        user_stats[email]["total_cost_usd"] += cost
        user_stats[email]["total_cost_inr"] += cost * 83.0

    # Convert to list and sort by queries (descending)
    sorted_users = sorted(user_stats.values(), key=lambda x: x["queries"], reverse=True)
    
    # Take top 5
    top_users = sorted_users[:5]
    
    return {
        "status": "success",
        "data": top_users
    }

@app.get("/admin/analytics/weekly")
async def get_weekly_analytics(db: Database = Depends(get_db)):
    """Mock weekly analytics for dashboard charts."""
    # In a real app, you would aggregate by day for the last 7 days
    gens = list(db.generations.find().sort("timestamp", -1).limit(100))
    # Simplify for demo: just showing the counts
    return {
        "status": "success",
        "data": [
            {"day": "Mon", "value": 12},
            {"day": "Tue", "value": 19},
            {"day": "Wed", "value": 15},
            {"day": "Thu", "value": 22},
            {"day": "Fri", "value": 30},
            {"day": "Sat", "value": len(gens) // 2},
            {"day": "Sun", "value": len(gens)}
        ]
    }


@app.get("/admin/analytics/models")
async def get_model_distribution(db: Database = Depends(get_db)):
    """Calculate distribution of used models."""
    model_stats = usage_service.get_model_usage(db)
    total_queries = sum(m["queries"] for m in model_stats) or 1
    
    return {
        "status": "success",
        "data": [
            {
                "name": m["name"], 
                "value": round((m["queries"] / total_queries) * 100),
                "queries": m["queries"],
                "revenue": m["revenue"]
            } for m in model_stats
        ]
    }

@app.get("/admin/pricing")
async def get_pricing():
    """Get dynamic pricing for all models."""
    from services.usage_service import PRICING
    return {
        "status": "success",
        "data": PRICING
    }


@app.get("/admin/analytics/usage")
async def get_detailed_usage(db: Database = Depends(get_db)):
    """Detailed category breakdown."""
    gens = list(db.generations.find().limit(100))
    
    total_sec = sum(g.get("video_duration_actual", 0) for g in gens)
    total_tokens = sum(g.get("script_input_tokens", 0) + g.get("script_output_tokens", 0) for g in gens)
    
    return {
        "status": "success",
        "data": {
            "total_generations": len(gens),
            "total_video_seconds": total_sec,
            "total_script_tokens": total_tokens,
            "total_tts_characters": sum(g.get("tts_characters", 0) for g in gens),
            "total_caption_burns": sum(1 for g in gens if g.get("captions_enabled")),
            "total_format_conversions": sum(len(g.get("formats_generated", [])) for g in gens),
            "total_dub_translations": sum(len(g.get("dub_languages", [])) for g in gens),
        }
    }


@app.get("/admin/transactions")
async def get_admin_transactions(db: Database = Depends(get_db)):
    """Fetch transaction history."""
    txs = list(db.transactions.find().sort("created_at", -1))
    
    # Seed if empty for demo
    if not txs:
        dummy_txs = [
            models.Transaction(txn_id="TXN-9021", user_name="Abhishek Sharma", amount="₹14,999", plan="Agency Yearly", status="Completed", method="Razorpay").model_dump(),
            models.Transaction(txn_id="TXN-9020", user_name="Priya Patel", amount="₹1,499", plan="Pro Monthly", status="Completed", method="UPI").model_dump(),
            models.Transaction(txn_id="TXN-9019", user_name="Rahul Varma", amount="₹499", plan="Basic Top-up", status="Failed", method="Card").model_dump(),
            models.Transaction(txn_id="TXN-9018", user_name="Sanjana Reddy", amount="₹1,499", plan="Pro Monthly", status="Processing", method="NetBanking").model_dump(),
            models.Transaction(txn_id="TXN-9017", user_name="Vikram Singh", amount="₹14,999", plan="Agency Yearly", status="Completed", method="Razorpay").model_dump(),
        ]
        db.transactions.insert_many(dummy_txs)
        txs = list(db.transactions.find().sort("created_at", -1))

    result = []
    for tx in txs:
        created_at = tx.get("created_at")
        date_str = created_at.strftime("%d %b %Y") if hasattr(created_at, "strftime") else str(created_at)
        result.append({
            "id": tx.get("txn_id"),
            "user": tx.get("user_name"),
            "amount": tx.get("amount"),
            "plan": tx.get("plan"),
            "date": date_str,
            "status": tx.get("status"),
            "method": tx.get("method")
        })
        
    return {
        "status": "success",
        "data": result
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
