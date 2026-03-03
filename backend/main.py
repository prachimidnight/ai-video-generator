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
from services.gemini_service import generate_script
from services.tts_service import generate_audio
from services.video_service import create_video
from services.gemini_video_service import gemini_video_service
from services.caption_service import add_captions_to_video, generate_srt, save_srt_file, get_video_duration
from services.format_service import convert_single_format, convert_to_all_formats
from services.translation_service import translation_service
from services.usage_service import usage_service
import time

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

@app.post("/draft-script")
async def draft_script(
    topic: str = Form(...),
    language: str = Form("English"),
    duration: int = Form(15)
):
    """Step 1: Just generate the script draft."""
    print(f"Drafting script for topic: {topic} ({language}, {duration}s)")
    script = generate_script(topic, language, duration)
    
    return {"script": script}

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
    engine: str = Form("did"),
    veo_quality: str = Form("fast"), # 'fast' or 'standard'
    # New parameters for captions
    captions_enabled: str = Form("false"),
    caption_style: str = Form("default"),
    # New parameters for multi-format
    generate_all_formats: str = Form("false"),
    # New parameters for auto-dubbing
    dub_languages: str = Form(""),  # Comma-separated list of languages
):
    """
    Step 2: Pro pipeline with full customization.
    Now supports auto-captions, multi-format, and auto-dubbing.
    """
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

    # 3. Generation Logic based on Engine
    print(f"Using Engine: {engine} (Quality: {veo_quality})")
    video_url = None
    local_video_path = None
    
    if engine == "gemini":
        print(f"Creating cinematic video with Gemini Veo ({veo_quality})...")
        # Ensure duration is within Veo 3.1 bounds (4-8s)
        target_duration = min(duration, 8) if duration >= 4 else 6
        
        try:
            local_filename = await gemini_video_service.generate_video(
                script, image_path, 
                duration=target_duration, 
                aspect_ratio=aspect_ratio,
                quality=veo_quality
            )
            if local_filename:
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
    else:
        print("Creating lip-synced video with D-ID...")
        video_url = await run_in_threadpool(create_video, image_path, audio_path, image_url, audio_url, background_type)
    
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
        video_model_used = "veo-3.1-fast-generate-preview" if engine == "gemini" else "d-id"
        # Try to get actual duration
        try:
            duration_val = get_video_duration(local_video_path)
            if duration_val:
                video_duration_actual = duration_val
        except:
            video_duration_actual = min(duration, 8) if engine == "gemini" else duration
    
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
