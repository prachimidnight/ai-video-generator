import os
import subprocess
import uuid
import asyncio

class MergeService:
    def __init__(self):
        self.temp_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "temp")
        # Find static-ffmpeg binary path in .venv
        self.ffmpeg_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".venv/bin/static_ffmpeg")
        if not os.path.exists(self.ffmpeg_path):
            self.ffmpeg_path = "static_ffmpeg" # fallback

    async def get_audio_duration(self, audio_path: str) -> float:
        """Get duration of audio using static_ffprobe (internal to static_ffmpeg package)."""
        ffprobe_path = self.ffmpeg_path.replace("static_ffmpeg", "static_ffprobe")
        try:
            cmd = [
                ffprobe_path, "-v", "quiet",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                audio_path
            ]
            result = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await result.communicate()
            return float(stdout.decode().strip())
        except:
            return 8.0 # fallback

    async def merge_audio_video(self, video_path: str, audio_path: str) -> str:
        """Merges audio and video, looping the video if it is shorter than the audio."""
        output_filename = f"social_stamp_merged_{uuid.uuid4().hex[:8]}.mp4"
        output_path = os.path.join(self.temp_dir, output_filename)
        
        try:
            # We use stream_loop -1 to repeat the video until the audio (shortest) finishes
            # Mapping 0:v (video) and 1:a (audio)
            # Shortest flag ensures it stops when the audio ends
            cmd = [
                self.ffmpeg_path, "-y",
                "-stream_loop", "-1",
                "-i", video_path,
                "-i", audio_path,
                "-map", "0:v:0",
                "-map", "1:a:0",
                "-c:v", "copy",
                "-c:a", "aac",
                "-shortest",
                output_path
            ]
            
            print(f"DEBUG: Running merge: {' '.join(cmd)}")
            result = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            await result.wait()
            
            if os.path.exists(output_path):
                return output_filename
            return None
        except Exception as e:
            print(f"ERROR: Merge failed: {e}")
            return None

merge_service = MergeService()
