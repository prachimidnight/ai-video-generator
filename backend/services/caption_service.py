"""
Caption Service - Auto-generates subtitles and burns them into video.

Workflow:
1. Takes a script text and audio duration
2. Splits text into timed subtitle segments
3. Generates an SRT file
4. Burns subtitles into video using ffmpeg
"""

import os
import re
import uuid
import subprocess
import math

TEMP_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "temp")
FFMPEG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".venv/bin/static_ffmpeg")
FFPROBE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".venv/bin/static_ffprobe")

if not os.path.exists(FFMPEG_PATH):
    FFMPEG_PATH = "ffmpeg"
    FFPROBE_PATH = "ffprobe"


def _split_into_segments(text: str, max_words_per_segment: int = 6) -> list[str]:
    """Split script text into short subtitle segments."""
    words = text.split()
    segments = []
    current_segment = []

    for word in words:
        current_segment.append(word)
        # Split on punctuation or when max words reached
        if (
            len(current_segment) >= max_words_per_segment
            or word.endswith((".", "!", "?", ",", ";", ":"))
        ):
            segments.append(" ".join(current_segment))
            current_segment = []

    if current_segment:
        segments.append(" ".join(current_segment))

    return segments


def _format_srt_time(seconds: float) -> str:
    """Convert seconds to SRT time format (HH:MM:SS,mmm)."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def generate_srt(script: str, audio_duration: float, max_words: int = 6) -> str:
    """
    Generate SRT subtitle content from script text.
    
    Args:
        script: The full script text
        audio_duration: Duration of the audio in seconds
        max_words: Max words per subtitle segment
    
    Returns:
        SRT formatted string
    """
    segments = _split_into_segments(script, max_words)
    if not segments:
        return ""

    # Calculate timing: distribute segments evenly across audio duration
    # Add a small buffer at start and end
    start_buffer = 0.2
    end_buffer = 0.3
    effective_duration = audio_duration - start_buffer - end_buffer

    # Weight segments by word count for more natural timing
    word_counts = [len(seg.split()) for seg in segments]
    total_words = sum(word_counts)

    srt_lines = []
    current_time = start_buffer

    for i, (segment, word_count) in enumerate(zip(segments, word_counts)):
        # Duration proportional to word count
        segment_duration = (word_count / total_words) * effective_duration
        segment_duration = max(segment_duration, 0.8)  # Minimum 0.8s per segment

        start_time = current_time
        end_time = min(current_time + segment_duration, audio_duration - 0.1)

        srt_lines.append(f"{i + 1}")
        srt_lines.append(f"{_format_srt_time(start_time)} --> {_format_srt_time(end_time)}")
        srt_lines.append(segment)
        srt_lines.append("")

        current_time = end_time + 0.05  # Small gap between subtitles

    return "\n".join(srt_lines)


def save_srt_file(srt_content: str) -> str:
    """Save SRT content to a file and return the path."""
    os.makedirs(TEMP_DIR, exist_ok=True)
    filename = f"captions_{uuid.uuid4().hex[:8]}.srt"
    filepath = os.path.join(TEMP_DIR, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(srt_content)
    print(f"DEBUG: SRT file saved to {filepath}")
    return filepath


def get_video_duration(video_path: str) -> float:
    """Get duration of a video file using ffprobe."""
    try:
        result = subprocess.run(
            [
                FFPROBE_PATH, "-v", "quiet",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                video_path
            ],
            capture_output=True, text=True, timeout=10
        )
        return float(result.stdout.strip())
    except Exception as e:
        print(f"DEBUG: Failed to get video duration: {e}")
        return 0.0


def burn_captions(
    video_path: str,
    srt_path: str,
    style: str = "default",
    aspect_ratio: str = "16:9"
) -> str:
    """
    Burn SRT subtitles into a video using ffmpeg.
    
    Args:
        video_path: Path to the input video
        srt_path: Path to the SRT file
        style: Caption style - 'default', 'bold', 'minimal', 'karaoke'
        aspect_ratio: Video aspect ratio for font sizing
    
    Returns:
        Path to the output video with burned captions
    """
    os.makedirs(TEMP_DIR, exist_ok=True)
    output_filename = f"captioned_{uuid.uuid4().hex[:8]}.mp4"
    output_path = os.path.join(TEMP_DIR, output_filename)

    # Determine font size based on aspect ratio
    font_sizes = {
        "16:9": 22,
        "9:16": 18
    }
    font_size = font_sizes.get(aspect_ratio, 22)

    # Build subtitle style based on user choice
    # We need to escape the SRT path for ffmpeg (replace : and \ etc.)
    escaped_srt = srt_path.replace("\\", "/").replace(":", "\\:")

    style_configs = {
        "default": f"FontSize={font_size},FontName=Arial,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BorderStyle=3,Outline=2,Shadow=1,MarginV=30",
        "bold": f"FontSize={font_size + 4},FontName=Arial,Bold=1,PrimaryColour=&H0000FFFF,OutlineColour=&H00000000,BorderStyle=1,Outline=3,Shadow=2,MarginV=35",
        "minimal": f"FontSize={font_size - 2},FontName=Arial,PrimaryColour=&H00FFFFFF,OutlineColour=&H80000000,BorderStyle=3,Outline=1,Shadow=0,MarginV=25",
        "karaoke": f"FontSize={font_size + 2},FontName=Impact,Bold=1,PrimaryColour=&H0000FF00,OutlineColour=&H00000000,BorderStyle=1,Outline=3,Shadow=2,MarginV=40"
    }

    subtitle_style = style_configs.get(style, style_configs["default"])

    try:
        # Use ffmpeg subtitles filter
        cmd = [
            FFMPEG_PATH, "-y",
            "-i", video_path,
            "-vf", f"subtitles={escaped_srt}:force_style='{subtitle_style}'",
            "-c:a", "copy",
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "23",
            output_path
        ]

        print(f"DEBUG: Running ffmpeg caption burn: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

        if result.returncode != 0:
            print(f"DEBUG: ffmpeg error: {result.stderr[:500]}")
            # Fallback: try with drawtext instead of subtitles filter
            return _burn_captions_drawtext(video_path, srt_path, font_size, output_path)

        print(f"DEBUG: Captioned video saved to {output_path}")
        return output_filename

    except FileNotFoundError:
        print("ERROR: ffmpeg not found. Please install ffmpeg.")
        return None
    except Exception as e:
        print(f"ERROR: Caption burn failed: {e}")
        return None


def _burn_captions_drawtext(
    video_path: str,
    srt_path: str,
    font_size: int,
    output_path: str
) -> str:
    """Fallback: burn captions using drawtext filter if subtitles filter fails."""
    try:
        # Parse SRT to get segments with timing
        with open(srt_path, "r") as f:
            srt_content = f.read()

        # Simple approach: single drawtext that changes
        # For the fallback, just overlay the text at the bottom
        cmd = [
            FFMPEG_PATH, "-y",
            "-i", video_path,
            "-vf", f"drawtext=textfile={srt_path}:fontsize={font_size}:fontcolor=white:borderw=2:bordercolor=black:x=(w-text_w)/2:y=h-th-40",
            "-c:a", "copy",
            "-c:v", "libx264",
            "-preset", "fast",
            output_path
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode == 0:
            return os.path.basename(output_path)

        print(f"DEBUG: Drawtext fallback also failed: {result.stderr[:300]}")
        return None
    except Exception as e:
        print(f"ERROR: Drawtext fallback failed: {e}")
        return None


async def add_captions_to_video(
    video_path: str,
    script: str,
    audio_duration: float = None,
    caption_style: str = "default",
    aspect_ratio: str = "16:9"
) -> str:
    """
    Main function: Generate captions and burn them into a video.
    
    Args:
        video_path: Path to the input video file
        script: The script text for generating subtitles
        audio_duration: Duration in seconds (auto-detected if None)
        caption_style: 'default', 'bold', 'minimal', 'karaoke'
        aspect_ratio: '16:9', '9:16', '1:1'
    
    Returns:
        Filename of the captioned video, or None on failure
    """
    if not audio_duration:
        audio_duration = get_video_duration(video_path)
        if audio_duration <= 0:
            # Estimate from script word count (2.5 words/sec)
            word_count = len(script.split())
            audio_duration = word_count / 2.5

    print(f"DEBUG: Generating captions for {audio_duration:.1f}s video...")

    # 1. Generate SRT
    srt_content = generate_srt(script, audio_duration)
    if not srt_content:
        print("ERROR: No captions generated.")
        return None

    srt_path = save_srt_file(srt_content)

    # 2. Burn into video
    result = burn_captions(video_path, srt_path, caption_style, aspect_ratio)

    # Clean up SRT file
    try:
        os.remove(srt_path)
    except:
        pass

    return result
