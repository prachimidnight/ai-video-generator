import os
import time
import asyncio
import mimetypes
import traceback
import requests
import uuid
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type, wait_fixed
from google import genai
from google.genai import types
from google.genai.errors import ClientError
from dotenv import load_dotenv

load_dotenv()

class GeminiVideoService:
    def __init__(self):
        self.api_key = os.getenv("GOOGLE_API_KEY")
        # Veo requires v1alpha for now
        self.client = genai.Client(
            api_key=self.api_key, 
            http_options={'api_version': 'v1alpha'}
        )
        self.model_name = "veo-3.1-fast-generate-preview"
        self.temp_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "temp")

    @retry(
        retry=retry_if_exception_type(ClientError),
        wait=wait_fixed(60), # Wait exactly 60s before retrying to give quota time to reset
        stop=stop_after_attempt(2), # Only try twice total
        reraise=True
    )
    def _generate_video_op_with_retry(self, model, prompt, image_obj, config):
        print("DEBUG: details of generation attempt...")
        return self.client.models.generate_videos(
            model=model,
            prompt=prompt,
            image=image_obj,
            config=config
        )

    async def generate_video(self, prompt: str, image_path: str = None, duration: int = 5, aspect_ratio: str = "16:9", quality: str = "fast"):
        """
        Generates a video using Google Veo and downloads it locally.
        quality: 'fast' or 'standard'
        """
        try:
            # RELOAD API KEY to ensure we are using the latest one from .env
            load_dotenv(override=True)
            self.api_key = os.getenv("GOOGLE_API_KEY")
            
            # Select model based on quality preference
            model_name = "veo-3.1-fast-generate-preview" if quality == "fast" else "veo-3.1-generate-preview"
            print(f"DEBUG: Using Google model: {model_name}")

            # Re-initialize client with potentially new key
            self.client = genai.Client(
                api_key=self.api_key, 
                http_options={'api_version': 'v1alpha'}
            )

            print(f"DEBUG: Starting Gemini Veo ({quality}) generation for: {prompt[:50]}... (Duration: {duration}s, Ratio: {aspect_ratio})")
            
            # Ensure duration is supported (Veo supports 4-8s)
            target_duration = min(max(duration, 4), 8) 
            
            config = types.GenerateVideosConfig(
                duration_seconds=target_duration,
                aspect_ratio=aspect_ratio
            )

            # ... (image processing code remains same) ...
            image_obj = None
            if image_path and os.path.exists(image_path):
                mime_type, _ = mimetypes.guess_type(image_path)
                if not mime_type:
                    mime_type = "image/jpeg"
                
                print(f"DEBUG: Using image {image_path} with mime_type {mime_type}")
                with open(image_path, "rb") as f:
                    image_bytes = f.read()
                    image_obj = types.Image(image_bytes=image_bytes, mime_type=mime_type)

            # Use retry logic for the initial request
            print(f"DEBUG: Initiating Veo ({model_name}) request with auto-retry enabled...")
            operation = await asyncio.to_thread(
                self._generate_video_op_with_retry,
                model_name,
                prompt,
                image_obj,
                config
            )

            print(f"DEBUG: Veo Operation ID: {operation.name}")
            op_name = operation.name
            
            # Polling for completion
            start_time = time.time()
            timeout = 900 # 15 minutes
            
            while True:
                if time.time() - start_time > timeout:
                    print(f"DEBUG: Gemini Veo generation timed out after {timeout}s.")
                    return None
                
                await asyncio.sleep(30) # Poll less frequently (every 30s) to save bandwidth/quota
                try:
                    operation = self.client.operations.get(operation=operation)
                    print(f"DEBUG: Veo Status... Done: {operation.done}")
                    if operation.done:
                        break
                except Exception as poll_err:
                    print(f"DEBUG: Polling error: {poll_err}")
                    continue

            if operation.error:
                error_msg = f"Veo Operation Error: {operation.error}"
                print(f"DEBUG: {error_msg}")
                raise Exception(error_msg)

            # Get the result URL and download it locally
            if operation.result and operation.result.generated_videos:
                google_video_url = operation.result.generated_videos[0].video.uri
                # Add API key to URL for downloading
                download_url = f"{google_video_url}&key={self.api_key}"
                
                print(f"DEBUG: Downloading video from Google...")
                local_filename = f"gemini_video_{uuid.uuid4().hex}.mp4"
                local_path = os.path.join(self.temp_dir, local_filename)
                
                response = requests.get(download_url)
                if response.status_code == 200:
                    with open(local_path, "wb") as f:
                        f.write(response.content)
                    print(f"DEBUG: Video saved locally to: {local_path}")
                    return local_filename
                else:
                    error_msg = f"Failed to download video. Status: {response.status_code}"
                    print(f"DEBUG: {error_msg}")
                    raise Exception(error_msg)
            
            raise Exception("Operation finished but no video URL found in results.")

        except Exception as e:
            print(f"DEBUG: Gemini Video Service Exception: {e}")
            traceback.print_exc()
            raise e

# Singleton instance
gemini_video_service = GeminiVideoService()

