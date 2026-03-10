"""
Format Service - Converts video to multiple aspect ratios.

Supports:
- 16:9 (YouTube, Landscape)
- 9:16 (Reels, TikTok, Shorts)
- 1:1  (Instagram Square)

Uses ffmpeg to crop/pad/resize videos.
"""

import os
import uuid
import subprocess

TEMP_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "temp")
FFMPEG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".venv/bin/static_ffmpeg")
FFPROBE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".venv/bin/static_ffprobe")

if not os.path.exists(FFMPEG_PATH):
    FFMPEG_PATH = "ffmpeg"
    FFPROBE_PATH = "ffprobe"


# Aspect ratio configs with target resolutions
FORMAT_CONFIGS = {
    "16:9": {
        "name": "Landscape (YouTube)",
        "width": 1920,
        "height": 1080,
        "ratio": 16 / 9
    },
    "9:16": {
        "name": "Portrait (Reels/TikTok)",
        "width": 1080,
        "height": 1920,
        "ratio": 9 / 16
    },
    "1:1": {
        "name": "Square (Instagram)",
        "width": 1080,
        "height": 1080,
        "ratio": 1.0
    }
}


def get_video_info(video_path: str) -> dict:
    """Get video width, height, and duration using ffprobe."""
    try:
        result = subprocess.run(
            [
                FFPROBE_PATH, "-v", "quiet",
                "-show_entries", "stream=width,height,duration",
                "-show_entries", "format=duration",
                "-of", "json",
                video_path
            ],
            capture_output=True, text=True, timeout=10
        )
        import json
        data = json.loads(result.stdout)

        width = None
        height = None
        duration = None

        for stream in data.get("streams", []):
            if "width" in stream:
                width = int(stream["width"])
                height = int(stream["height"])
            if "duration" in stream:
                duration = float(stream["duration"])

        if duration is None and "format" in data:
            duration = float(data["format"].get("duration", 0))

        return {"width": width, "height": height, "duration": duration}
    except Exception as e:
        print(f"DEBUG: ffprobe error: {e}")
        return {"width": 1920, "height": 1080, "duration": 0}


def convert_format(
    video_path: str,
    target_ratio: str,
    bg_color: str = "black",
    mode: str = "fit"  # "fit" (pad with bg) or "fill" (crop to fill)
) -> str:
    """
    Convert a video to a different aspect ratio.
    
    Args:
        video_path: Path to the input video
        target_ratio: Target aspect ratio ('16:9', '9:16', '1:1')
        bg_color: Background color for padding (when mode='fit')
        mode: 'fit' (letterbox/pillarbox) or 'fill' (crop)
    
    Returns:
        Filename of the converted video, or None on failure
    """
    os.makedirs(TEMP_DIR, exist_ok=True)

    config = FORMAT_CONFIGS.get(target_ratio)
    if not config:
        print(f"ERROR: Unknown aspect ratio: {target_ratio}")
        return None

    target_w = config["width"]
    target_h = config["height"]

    output_filename = f"format_{target_ratio.replace(':', 'x')}_{uuid.uuid4().hex[:8]}.mp4"
    output_path = os.path.join(TEMP_DIR, output_filename)

    try:
        video_info = get_video_info(video_path)
        src_w = video_info["width"] or 1920
        src_h = video_info["height"] or 1080

        if mode == "fill":
            # Crop to fill: scale up and crop center
            # Calculate crop dimensions
            src_ratio = src_w / src_h
            target_ratio_val = target_w / target_h

            if src_ratio > target_ratio_val:
                # Source is wider, crop sides
                vf = f"scale=-1:{target_h},crop={target_w}:{target_h}"
            else:
                # Source is taller, crop top/bottom
                vf = f"scale={target_w}:-1,crop={target_w}:{target_h}"
        else:
            # Fit mode: scale down and pad with background color
            # First scale to fit within target dimensions, then pad
            vf = (
                f"scale={target_w}:{target_h}:force_original_aspect_ratio=decrease,"
                f"pad={target_w}:{target_h}:(ow-iw)/2:(oh-ih)/2:color={bg_color},"
                f"setsar=1"
            )

        cmd = [
            FFMPEG_PATH, "-y",
            "-i", video_path,
            "-vf", vf,
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "23",
            "-c:a", "aac",
            "-b:a", "128k",
            "-movflags", "+faststart",
            output_path
        ]

        print(f"DEBUG: Converting to {target_ratio} ({mode} mode): {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

        if result.returncode != 0:
            print(f"DEBUG: Format conversion failed: {result.stderr[:500]}")
            return None

        print(f"DEBUG: Format conversion done: {output_path}")
        return output_filename

    except FileNotFoundError:
        print("ERROR: ffmpeg not found. Please install ffmpeg.")
        return None
    except Exception as e:
        print(f"ERROR: Format conversion failed: {e}")
        return None


async def convert_to_all_formats(
    video_path: str,
    original_ratio: str = "16:9",
    mode: str = "fit"
) -> dict:
    """
    Convert a video to all three formats (skipping the original).
    
    Args:
        video_path: Path to the input video
        original_ratio: The original aspect ratio (will be skipped)
        mode: 'fit' or 'fill'
    
    Returns:
        Dictionary of {ratio: filename} for successfully generated formats
    """
    results = {}

    for ratio, config in FORMAT_CONFIGS.items():
        if ratio == original_ratio:
            # Skip the original format — the video is already in that format
            results[ratio] = os.path.basename(video_path)
            continue

        print(f"DEBUG: Converting to {config['name']}...")
        filename = convert_format(video_path, ratio, mode=mode)
        if filename:
            results[ratio] = filename

    return results


async def convert_single_format(
    video_path: str,
    target_ratio: str,
    mode: str = "fit"
) -> str:
    """
    Convert a video to a single target format.
    
    Returns:
        Filename of converted video, or None on failure
    """
    return convert_format(video_path, target_ratio, mode=mode)
