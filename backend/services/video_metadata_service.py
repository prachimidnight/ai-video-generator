import os
import json
import hmac
import hashlib
from datetime import datetime, timezone
from typing import Any, Dict, Optional, List


class VideoMetadataService:
    """
    Stores per-video generation metadata in a non-public directory.

    Optionally embeds a *non-sensitive* summary into the MP4 container metadata.
    """

    def __init__(self):
        base_dir = os.path.dirname(os.path.dirname(__file__))  # backend/
        self.private_dir = os.path.join(base_dir, "private_metadata")
        os.makedirs(self.private_dir, exist_ok=True)

        self.ffmpeg_path = os.path.join(base_dir, ".venv/bin/static_ffmpeg")
        if not os.path.exists(self.ffmpeg_path):
            self.ffmpeg_path = "ffmpeg"

        # Use explicit key if provided; otherwise fall back to JWT_SECRET so it's consistent.
        self.hmac_key = (
            os.getenv("METADATA_HMAC_KEY")
            or os.getenv("JWT_SECRET")
            or "dev-change-me"
        ).encode("utf-8")

    def _hmac_sha256_hex(self, value: str) -> str:
        return hmac.new(self.hmac_key, value.encode("utf-8"), hashlib.sha256).hexdigest()

    def build_record(
        self,
        *,
        video_filename: str,
        user_email: str,
        topic: str,
        engine: str,
        veo_quality: str,
        duration_requested: int,
        aspect_ratio_requested: str,
        use_tts: bool,
        use_image: bool,
        captions_enabled: bool,
        caption_style: str,
        formats_generated: Optional[list] = None,
        script_model: Optional[str] = None,
        voice: Optional[str] = None,
    ) -> Dict[str, Any]:
        now = datetime.now(timezone.utc)
        return {
            "schema_version": 1,
            "created_at_utc": now.isoformat(),
            "video_filename": video_filename,
            # Privacy: store only a stable hash of the user identifier.
            "user_id_hash": self._hmac_sha256_hex(user_email.lower().strip()),
            "inputs": {
                "topic": topic,
                "engine": engine,
                "veo_quality": veo_quality,
                "duration_requested": duration_requested,
                "aspect_ratio_requested": aspect_ratio_requested,
                "use_tts": bool(use_tts),
                "use_image": bool(use_image),
                "script_model": script_model,
                "voice": voice,
            },
            "post_processing": {
                "captions_enabled": bool(captions_enabled),
                "caption_style": caption_style if captions_enabled else "",
                "formats_generated": formats_generated or [],
            },
        }

    def write_private_json(self, record: Dict[str, Any]) -> str:
        video_filename = record.get("video_filename") or "unknown.mp4"
        safe_name = os.path.basename(video_filename)
        out_path = os.path.join(self.private_dir, f"{safe_name}.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(record, f, ensure_ascii=False, indent=2)
        return out_path

    def read_private_json(self, video_filename: str) -> Dict[str, Any]:
        safe_name = os.path.basename(video_filename)
        meta_path = os.path.join(self.private_dir, f"{safe_name}.json")
        if not os.path.exists(meta_path):
            raise FileNotFoundError(f"Metadata not found for {safe_name}")
        with open(meta_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def list_recent_private_json(self, limit: int = 50) -> List[Dict[str, Any]]:
        try:
            limit = max(1, min(int(limit), 200))
        except Exception:
            limit = 50

        files = []
        for name in os.listdir(self.private_dir):
            if not name.endswith(".json"):
                continue
            path = os.path.join(self.private_dir, name)
            try:
                mtime = os.path.getmtime(path)
            except Exception:
                mtime = 0
            files.append((mtime, path))

        files.sort(key=lambda x: x[0], reverse=True)
        out: List[Dict[str, Any]] = []
        for _, path in files[:limit]:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    out.append(json.load(f))
            except Exception:
                continue
        return out

    def embed_public_summary_into_mp4(
        self,
        *,
        input_video_path: str,
        output_video_path: str,
        public_summary: Dict[str, Any],
    ) -> bool:
        """
        Writes MP4 with container metadata. This is *not* encrypted—only embed non-sensitive fields.
        """
        try:
            summary_str = json.dumps(public_summary, ensure_ascii=False, separators=(",", ":"))
            # Keep metadata small and predictable.
            if len(summary_str) > 1500:
                summary_str = summary_str[:1500]

            import subprocess

            cmd = [
                self.ffmpeg_path,
                "-y",
                "-i",
                input_video_path,
                "-map",
                "0",
                "-c",
                "copy",
                "-metadata",
                "comment=" + summary_str,
                "-movflags",
                "+faststart",
                output_video_path,
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            return result.returncode == 0 and os.path.exists(output_video_path)
        except Exception as e:
            print(f"WARNING: Failed to embed MP4 metadata: {e}")
            return False


video_metadata_service = VideoMetadataService()

