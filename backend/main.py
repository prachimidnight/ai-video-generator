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
from sqlalchemy.orm import Session
from fastapi import Depends
import models
import schemas
import auth
from database import engine, get_db
from services.credit_service import credit_service

# Create tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI Video Generator API")

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
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
def signup(user: schemas.UserCreate, db: Session = Depends(get_db)):
    # Check if user exists
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
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
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.post("/login")
def login(email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == email, models.User.status == True).first()
    if not user or not auth.verify_password(password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    return {
        "status": "success",
        "message": "Login successful",
        "user": {
            "guid": user.guid,
            "full_name": user.full_name,
            "email": user.email,
            "subscription_tier": user.subscription_tier,
            "available_credits": user.available_credits
        }
    }

@app.post("/logout")
def logout():
    return {"status": "success", "message": "Logged out successfully"}

@app.get("/user/credits")
def get_user_credits(email: str, db: Session = Depends(get_db)):
    """GET current credit balance for a user."""
    return credit_service.get_credits(db, email)

@app.post("/draft-script")
async def draft_script(
    topic: str = Form(...),
    language: str = Form("English"),
    duration: int = Form(15),
    user_email: str = Form(...)  # Tracking user
):
    """Step 1: Just generate the script draft."""
    print(f"Drafting script for topic: {topic} ({language}, {duration}s)")
    script, in_tokens, out_tokens = generate_script(topic, language, duration)
    
    return {"script": script, "input_tokens": in_tokens, "output_tokens": out_tokens}

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
    db: Session = Depends(get_db)
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
    
    usage_entry = usage_service.log_generation(
        topic=topic,
        script=script,
        language=language,
        engine=engine,
        voice=voice,
        duration_requested=duration,
        video_duration_actual=video_duration_actual,
        video_file_size_bytes=video_file_size,
        tts_characters=len(script),
        captions_enabled=(captions_enabled == "true"),
        caption_style=caption_style if captions_enabled == "true" else "",
        formats_generated=list(format_urls.keys()) if format_urls else [],
        dub_languages=[l.strip() for l in dub_languages.split(",") if l.strip()] if dub_languages else [],
        status="success",
        video_model=video_model_used,
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

@app.get("/usage")
async def get_usage():
    """Get overall usage summary with recent generations."""
    return {
        "status": "success",
        "data": usage_service.get_summary()
    }


@app.get("/usage/daily")
async def get_daily_usage():
    """Get today's usage stats."""
    return {
        "status": "success",
        "data": usage_service.get_daily_stats()
    }


@app.post("/usage/reset")
async def reset_usage():
    """Reset all usage data (admin action)."""
    usage_service.usage_data = {
        "total_generations": 0,
        "total_script_tokens": {"input": 0, "output": 0},
        "total_video_seconds": 0,
        "total_tts_characters": 0,
        "total_estimated_cost_usd": 0.0,
        "total_dub_translations": 0,
        "total_caption_burns": 0,
        "total_format_conversions": 0,
        "generations": []
    }
    usage_service._save_data()
    return {"status": "success", "message": "Usage data reset."}


@app.get("/admin/users")
async def get_admin_users(db: Session = Depends(get_db)):
    """Get list of users for admin panel from real database."""
    users = db.query(models.User).filter(models.User.status == True).all()
    user_list = []
    for u in users:
        user_list.append({
            "id": u.id,
            "name": u.full_name,
            "email": u.email,
            "tier": u.subscription_tier.capitalize(),
            "status": "Active" if u.status else "Inactive",
            "usage": u.available_credits, # Showing credits as usage/balance
            "joined": u.created_at.strftime("%d %b %Y")
        })
    return {
        "status": "success",
        "data": user_list
    }


@app.put("/admin/users/{user_id}")
async def update_admin_user(user_id: int, user_update: schemas.UserUpdate, db: Session = Depends(get_db)):
    """Update user details as an admin."""
    db_user = db.query(models.User).filter(models.User.id == user_id, models.User.status == True).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    update_data = user_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_user, key, value)
    
    db.commit()
    db.refresh(db_user)
    return {"status": "success", "message": "User updated successfully", "data": db_user}


@app.delete("/admin/users/{user_id}")
async def delete_admin_user(user_id: int, db: Session = Depends(get_db)):
    """Soft delete a user as an admin (set status to 0)."""
    db_user = db.query(models.User).filter(models.User.id == user_id, models.User.status == True).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    db_user.status = False
    db.commit()
    return {"status": "success", "message": "User deleted successfully"}


@app.get("/admin/stats")
async def get_admin_stats(db: Session = Depends(get_db)):
    """Get high-level system metrics."""
    total_users = db.query(models.User).filter(models.User.status == True).count()
    usage = usage_service.get_summary()
    
    # Calculate revenue from transactions
    transactions = db.query(models.Transaction).filter(models.Transaction.status == "Completed").all()
    total_revenue_inr = 0
    for tx in transactions:
        try:
            # Extract number from string like "₹1,499"
            amt_str = tx.amount.replace("₹", "").replace(",", "")
            total_revenue_inr += int(amt_str)
        except:
            continue
            
    return {
        "status": "success",
        "data": {
            "total_users": total_users,
            "total_generations": usage["total_generations"],
            "total_revenue_inr": total_revenue_inr,
            "system_load": "24.2%", # Heuristic/Static for now but could be dynamic
            "revenue_formatted": f"₹{total_revenue_inr/100000:.1f}L" if total_revenue_inr >= 100000 else f"₹{total_revenue_inr:,}"
        }
    }


@app.get("/admin/analytics/weekly")
async def get_weekly_analytics():
    """Get last 7 days of generation activity."""
    gens = usage_service.usage_data["generations"]
    
    # Get last 7 days names
    days = []
    today = datetime.now(IST)
    for i in range(6, -1, -1):
        days.append((today - timedelta(days=i)).strftime("%a"))
        
    # Count per day
    day_counts = {day: 0 for day in days}
    for gen in gens:
        # gen["date"] is e.g. "06 Mar 2026"
        try:
            gen_date = datetime.strptime(gen["date"], "%d %b %Y")
            gen_day = gen_date.strftime("%a")
            if gen_day in day_counts:
                day_counts[gen_day] += 1
        except:
            continue
            
    result = []
    for day in days:
        result.append({
            "day": day,
            "count": day_counts[day],
            "cost": day_counts[day] * 20 # Dummy cost per gen in INR for chart
        })
        
    return {
        "status": "success",
        "data": result
    }


@app.get("/admin/analytics/models")
async def get_model_distribution():
    """Get distribution of models used."""
    gens = usage_service.usage_data["generations"]
    counts = {"Gemini": 0}
    
    for gen in gens:
        counts["Gemini"] += 1
            
    total = sum(counts.values()) or 1
    result = [
        {"name": "Gemini 2.0 Flash", "share": round((counts["Gemini"] / total) * 100)}
    ]
    
    return {
        "status": "success",
        "data": result
    }


@app.get("/admin/transactions")
async def get_admin_transactions(db: Session = Depends(get_db)):
    """Fetch transaction history."""
    txs = db.query(models.Transaction).order_by(models.Transaction.created_at.desc()).all()
    
    # Seed if empty for demo
    if not txs:
        dummy_txs = [
            models.Transaction(txn_id="TXN-9021", user_name="Abhishek Sharma", amount="₹14,999", plan="Agency Yearly", status="Completed", method="Razorpay"),
            models.Transaction(txn_id="TXN-9020", user_name="Priya Patel", amount="₹1,499", plan="Pro Monthly", status="Completed", method="UPI"),
            models.Transaction(txn_id="TXN-9019", user_name="Rahul Varma", amount="₹499", plan="Basic Top-up", status="Failed", method="Card"),
            models.Transaction(txn_id="TXN-9018", user_name="Sanjana Reddy", amount="₹1,499", plan="Pro Monthly", status="Processing", method="NetBanking"),
            models.Transaction(txn_id="TXN-9017", user_name="Vikram Singh", amount="₹14,999", plan="Agency Yearly", status="Completed", method="Razorpay"),
        ]
        db.add_all(dummy_txs)
        db.commit()
        txs = db.query(models.Transaction).order_by(models.Transaction.created_at.desc()).all()

    result = []
    for tx in txs:
        result.append({
            "id": tx.txn_id,
            "user": tx.user_name,
            "amount": tx.amount,
            "plan": tx.plan,
            "date": tx.created_at.strftime("%d %b %Y"),
            "status": tx.status,
            "method": tx.method
        })
        
    return {
        "status": "success",
        "data": result
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
