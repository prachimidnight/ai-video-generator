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
from datetime import datetime, timedelta
from fastapi.security import OAuth2PasswordBearer
from fastapi import Header
from dotenv import set_key, find_dotenv
import models
import schemas
import auth
from database import get_db
from services.credit_service import credit_service
from services.usage_service import IST, USD_TO_INR

app = FastAPI(title="AI Video Generator API")

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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


# ========================
# AUTH HELPERS (defined early so all routes can use them)
# ========================

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

def get_current_user(
    db: Database = Depends(get_db),
    token: str = Depends(oauth2_scheme),
):
    try:
        payload = auth.decode_access_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    email = payload.get("sub")
    if not email:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = db.users.find_one({"email": email, "status": True})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    # Attach role from DB (source of truth)
    user["_id"] = str(user["_id"])
    return user

def require_admin(user=Depends(get_current_user)):
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


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


@app.post("/admin/users", response_model=schemas.UserResponse)
def admin_create_user(
    user: schemas.AdminUserCreate,
    db: Database = Depends(get_db),
    _admin=Depends(require_admin),
):
    existing = db.users.find_one({"email": user.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    password = user.password or "ChangeMe@123"
    hashed_password = auth.get_password_hash(password)

    new_user = models.User(
        full_name=user.full_name,
        email=user.email,
        password_hash=hashed_password,
        subscription_tier=user.subscription_tier.lower(),
        available_credits=user.available_credits,
        role=user.role.lower(),
    )
    user_dict = new_user.model_dump()
    db.users.insert_one(user_dict)
    return user_dict

@app.post("/login")
def login(email: str = Form(...), password: str = Form(...), db: Database = Depends(get_db)):
    user = db.users.find_one({"email": email, "status": True})
    if not user or not auth.verify_password(password, user.get("password_hash")):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    # Update last login
    db.users.update_one({"_id": user["_id"]}, {"$set": {"last_login_at": datetime.now(IST)}})

    token = auth.create_access_token({
        "sub": user.get("email"),
        "role": user.get("role", "user"),
        "guid": user.get("guid"),
    })

    return {
        "status": "success",
        "message": "Login successful",
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "guid": user.get("guid"),
            "full_name": user.get("full_name"),
            "email": user.get("email"),
            "role": user.get("role", "user"),
            "subscription_tier": user.get("subscription_tier", "basic"),
            "available_credits": user.get("available_credits", 2)
        }
    }

@app.post("/logout")
def logout():
    return {"status": "success", "message": "Logged out successfully"}




@app.get("/auth/me")
def auth_me(user=Depends(get_current_user)):
    return {
        "status": "success",
        "user": {
            "guid": user.get("guid"),
            "full_name": user.get("full_name"),
            "email": user.get("email"),
            "role": user.get("role", "user"),
            "subscription_tier": user.get("subscription_tier", "basic"),
            "available_credits": user.get("available_credits", 0),
        },
    }

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
    image: UploadFile | None = File(None),
    script: str = Form(""),
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
    user_email: str = Form(...),    # User who pays for this
    use_tts: str = Form("true"),
    use_image: str = Form("true"),
    db: Database = Depends(get_db)
):
    """
    Step 2: Pro pipeline with full customization.
    Now supports auto-captions and multi-format.
    """
    # 0. Credit Check & Deduction
    # This happens BEFORE we start the expensive generation
    remaining_credits = credit_service.deduct_credits(db, user_email, credits_to_deduct=1)
    print(f"User {user_email} charged 1 credit. Remaining: {remaining_credits}")

    print(f"--- Starting Advanced Video Generation ({engine}) ---")
    
    # 1. Save Image (optional)
    image_path = None
    image_url = None
    if use_image == "true" and image is not None:
        ext = os.path.splitext(image.filename)[1] or ".jpg"
        image_filename = f"avatar_{uuid.uuid4().hex}{ext}"
        image_path = os.path.join(temp_dir, image_filename)
        with open(image_path, "wb") as buffer:
            buffer.write(await image.read())
        image_url = f"{os.getenv('BASE_URL', 'http://localhost:8000')}/temp/{image_filename}"

    # 2. Optional TTS with custom settings
    audio_url = None
    if use_tts == "true" and script:
        print(f"Generating audio with voice: {voice}...")
        audio_filename = f"video_audio_{int(time.time())}.mp3"
        try:
            audio_path = await generate_audio(script, audio_filename, voice=voice, speed=speed, pitch=pitch)
            audio_url = f"{os.getenv('BASE_URL', 'http://localhost:8000')}/temp/{audio_filename}"
        except Exception as e:
            print(f"ERROR: Audio Generation Failed: {e}")
            return JSONResponse(
                status_code=500,
                content={"status": "error", "message": f"Audio service timeout (TTS). Please check your internet connection or try a different voice."}
            )

    # 3. Generation Logic (Gemini Only)
    print(f"Creating cinematic video with Gemini Veo ({veo_quality})...")
    # Ensure duration is within Veo 3.1 bounds (4-8s)
    target_duration = min(duration, 8) if duration >= 4 else 6
    
    # Humanization Step: Transform script into a visual-first prompt
    print(f"DEBUG: Enhancing visual prompt for humanization...")
    prompt_for_visual = script or topic
    visual_prompt = generate_visual_prompt(prompt_for_visual, topic)
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
        tts_characters=len(script) if use_tts == "true" else 0,
        captions_enabled=(captions_enabled == "true"),
        caption_style=caption_style if captions_enabled == "true" else "",
        formats_generated=list(format_urls.keys()),
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
async def get_usage_summary(db: Database = Depends(get_db), _admin=Depends(require_admin)):
    """Get high-level usage metrics for admin dashboard."""
    return {
        "status": "success",
        "data": usage_service.get_summary(db)
    }

@app.get("/admin/daily-stats")
async def get_daily_stats(db: Database = Depends(get_db), _admin=Depends(require_admin)):
    """Get usage statistics for the current day."""
    return {
        "status": "success",
        "data": usage_service.get_daily_stats(db)
    }

@app.post("/admin/reset-stats")
async def reset_stats(db: Database = Depends(get_db), _admin=Depends(require_admin)):
    """Reset all usage statistics (Admin only)."""
    db.stats.delete_one({"type": "overall_usage"})
    db.generations.delete_many({})
    return {"status": "success", "message": "Stats reset successfully"}


@app.get("/admin/users")
async def get_admin_users(db: Database = Depends(get_db), _admin=Depends(require_admin)):
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
async def update_admin_user(user_id: str, user_update: schemas.UserUpdate, db: Database = Depends(get_db), _admin=Depends(require_admin)):
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
async def delete_admin_user(user_id: str, db: Database = Depends(get_db), _admin=Depends(require_admin)):
    """Soft delete a user as an admin (set status to False)."""
    db_user = db.users.find_one({"$or": [{"guid": user_id}, {"id": user_id}], "status": True})
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    db.users.update_one({"_id": db_user["_id"]}, {"$set": {"status": False}})
    return {"status": "success", "message": "User deleted successfully"}


@app.get("/admin/stats")
async def get_admin_stats(db: Database = Depends(get_db), _admin=Depends(require_admin)):
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
async def get_admin_top_users(db: Database = Depends(get_db), _admin=Depends(require_admin)):
    """Get the top users by total transaction cost and query count."""
    gens = list(db.generations.find())
    
    user_stats = {}
    for gen in gens:
        # usage_service logs email in "user"
        email = gen.get("user") or gen.get("user_email") or "Unknown"
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
        user_stats[email]["total_cost_inr"] += cost * USD_TO_INR

    # Convert to list and sort by queries (descending)
    sorted_users = sorted(user_stats.values(), key=lambda x: x["queries"], reverse=True)
    
    # Take top 5
    top_users = sorted_users[:5]
    
    return {
        "status": "success",
        "data": top_users
    }

@app.get("/admin/analytics/weekly")
async def get_weekly_analytics(db: Database = Depends(get_db), _admin=Depends(require_admin)):
    """Weekly analytics for dashboard charts (last 7 days)."""
    end = datetime.now(IST)
    start = end - timedelta(days=6)

    pipeline = [
        {"$match": {"timestamp": {"$gte": start, "$lte": end}}},
        {"$group": {"_id": "$date", "value": {"$sum": 1}}},
    ]
    grouped = {d["_id"]: d["value"] for d in db.generations.aggregate(pipeline)}

    data = []
    for i in range(6, -1, -1):
        day_dt = end - timedelta(days=i)
        date_str = day_dt.strftime("%d %b %Y")
        data.append({"day": day_dt.strftime("%a"), "value": int(grouped.get(date_str, 0))})

    return {"status": "success", "data": data}


@app.get("/admin/analytics/models")
async def get_model_distribution(db: Database = Depends(get_db), _admin=Depends(require_admin)):
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
                "revenue": m["revenue"],
                "revenue_inr": m.get("revenue_inr", round((m.get("revenue") or 0) * USD_TO_INR, 2))
            } for m in model_stats
        ]
    }

@app.get("/admin/pricing")
async def get_pricing(_admin=Depends(require_admin)):
    """Get dynamic pricing for all models."""
    from services.usage_service import PRICING
    return {
        "status": "success",
        "data": PRICING
    }


@app.get("/admin/active-model")
async def get_active_model(db: Database = Depends(get_db), _admin=Depends(require_admin)):
    doc = db.stats.find_one({"type": "active_model"}) or {}
    model_id = doc.get("model_id", "gemini-2.5-flash")
    return {"status": "success", "data": {"model_id": model_id}}


@app.put("/admin/active-model")
async def set_active_model(
    model_id: str = Form(...),
    db: Database = Depends(get_db),
    _admin=Depends(require_admin),
):
    db.stats.update_one(
        {"type": "active_model"},
        {"$set": {"model_id": model_id, "updated_at": datetime.now(IST)}},
        upsert=True,
    )
    return {"status": "success", "data": {"model_id": model_id}}


@app.get("/admin/service-keys")
async def get_service_keys(_admin=Depends(require_admin)):
    """Return whether critical service keys are configured (not the raw secrets)."""
    has_google = bool(os.getenv("GOOGLE_API_KEY"))
    return {"status": "success", "data": {"google_configured": has_google}}


@app.put("/admin/service-keys")
async def update_service_keys(
    google_api_key: str = Form(...),
    _admin=Depends(require_admin),
):
    """Update the Google Gemini API key in the .env file."""
    env_path = find_dotenv()
    if not env_path:
        env_path = os.path.join(os.path.dirname(__file__), ".env")
    try:
        set_key(env_path, "GOOGLE_API_KEY", google_api_key)
        # Also update current process env so it's picked up immediately
        os.environ["GOOGLE_API_KEY"] = google_api_key
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update key: {e}" )


@app.get("/admin/analytics/usage")
async def get_detailed_usage(db: Database = Depends(get_db), _admin=Depends(require_admin)):
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
async def get_admin_transactions(db: Database = Depends(get_db), _admin=Depends(require_admin)):
    """Fetch all Razorpay transaction history for admin."""
    txs = list(db.transactions.find().sort("created_at", -1).limit(200))

    result = []
    for tx in txs:
        created_at = tx.get("created_at")
        date_str = created_at.strftime("%d %b %Y, %I:%M %p") if hasattr(created_at, "strftime") else str(created_at)
        result.append({
            "id": tx.get("txn_id"),
            "payment_id": tx.get("razorpay_payment_id"),
            "user": tx.get("user_name"),
            "email": tx.get("user_email"),
            "amount": tx.get("amount"),
            "plan": tx.get("plan"),
            "credits": tx.get("plan_credits", 0),
            "date": date_str,
            "status": tx.get("status"),
            "method": tx.get("method", "Razorpay"),
        })

    return {
        "status": "success",
        "data": result
    }


# ========================
# RAZORPAY PAYMENT
# ========================
import razorpay
import hmac
import hashlib

def get_razorpay_client():
    key_id = os.getenv("RAZORPAY_KEY_ID")
    key_secret = os.getenv("RAZORPAY_KEY_SECRET")
    if not key_id or not key_secret:
        raise HTTPException(status_code=500, detail="Razorpay keys not configured")
    return razorpay.Client(auth=(key_id, key_secret))

# Plan definitions — amount in paise (INR × 100)
PLANS = {
    "pro": {
        "name": "Professional",
        "amount_paise": 249900,   # ₹2,499
        "amount_display": "₹2,499",
        "credits": 50,
    },
    "agency": {
        "name": "Agency",
        "amount_paise": 799900,   # ₹7,999
        "amount_display": "₹7,999",
        "credits": 999,
    },
}


@app.post("/payment/create-order")
async def create_payment_order(
    plan_id: str = Form(...),       # "pro" or "agency"
    user_email: str = Form(...),
    db: Database = Depends(get_db),
):
    """Create a Razorpay order and return order details to frontend."""
    plan = PLANS.get(plan_id)
    if not plan:
        raise HTTPException(status_code=400, detail="Invalid plan")

    client = get_razorpay_client()
    try:
        order = client.order.create({
            "amount": plan["amount_paise"],
            "currency": "INR",
            "receipt": f"receipt_{uuid.uuid4().hex[:10]}",
            "notes": {
                "plan_id": plan_id,
                "user_email": user_email,
            }
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Razorpay order creation failed: {e}")

    # Save a pending transaction in DB
    user = db.users.find_one({"email": user_email})
    txn = models.Transaction(
        txn_id=order["id"],
        user_id=str(user["_id"]) if user else None,
        user_name=user.get("full_name", user_email) if user else user_email,
        user_email=user_email,
        amount=plan["amount_display"],
        amount_paise=plan["amount_paise"],
        plan=plan["name"],
        plan_credits=plan["credits"],
        status="Pending",
        method="Razorpay",
    )
    db.transactions.insert_one(txn.model_dump())

    return {
        "status": "success",
        "data": {
            "order_id": order["id"],
            "amount": plan["amount_paise"],
            "currency": "INR",
            "key_id": os.getenv("RAZORPAY_KEY_ID"),
            "plan_name": plan["name"],
            "plan_credits": plan["credits"],
        }
    }


@app.post("/payment/verify")
async def verify_payment(
    razorpay_order_id: str = Form(...),
    razorpay_payment_id: str = Form(...),
    razorpay_signature: str = Form(...),
    user_email: str = Form(...),
    db: Database = Depends(get_db),
):
    """Verify Razorpay payment signature, update transaction, award credits."""
    key_secret = os.getenv("RAZORPAY_KEY_SECRET", "")

    # HMAC-SHA256 signature verification
    message = f"{razorpay_order_id}|{razorpay_payment_id}"
    expected_sig = hmac.new(
        key_secret.encode(),
        message.encode(),
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(expected_sig, razorpay_signature):
        # Mark transaction as Failed
        db.transactions.update_one(
            {"txn_id": razorpay_order_id},
            {"$set": {"status": "Failed", "updated_at": datetime.now(IST)}}
        )
        raise HTTPException(status_code=400, detail="Payment signature verification failed")

    # Mark transaction as Completed
    txn = db.transactions.find_one({"txn_id": razorpay_order_id})
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found")

    db.transactions.update_one(
        {"txn_id": razorpay_order_id},
        {"$set": {
            "status": "Completed",
            "razorpay_payment_id": razorpay_payment_id,
            "razorpay_signature": razorpay_signature,
            "method": "Razorpay",
            "updated_at": datetime.now(IST),
        }}
    )

    # Award credits to user
    credits_to_add = txn.get("plan_credits", 0)
    plan_name = txn.get("plan", "pro").lower()
    tier = "pro" if "professional" in plan_name.lower() else "agency"

    db.users.update_one(
        {"email": user_email},
        {"$inc": {"available_credits": credits_to_add},
         "$set": {"subscription_tier": tier, "updated_at": datetime.now(IST)}}
    )

    return {
        "status": "success",
        "message": f"Payment verified! {credits_to_add} credits added to your account.",
        "data": {
            "payment_id": razorpay_payment_id,
            "credits_added": credits_to_add,
        }
    }


@app.get("/payment/history")
async def get_payment_history(
    user_email: str,
    db: Database = Depends(get_db),
):
    """Get payment history for a specific user."""
    txns = list(db.transactions.find(
        {"user_email": user_email},
        sort=[("created_at", -1)]
    ).limit(20))

    result = []
    for tx in txns:
        created_at = tx.get("created_at")
        date_str = created_at.strftime("%d %b %Y, %I:%M %p") if hasattr(created_at, "strftime") else str(created_at)
        result.append({
            "order_id": tx.get("txn_id"),
            "payment_id": tx.get("razorpay_payment_id"),
            "amount": tx.get("amount"),
            "plan": tx.get("plan"),
            "credits": tx.get("plan_credits", 0),
            "status": tx.get("status"),
            "date": date_str,
        })

    return {"status": "success", "data": result}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
