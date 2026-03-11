# import os
# import time
# import asyncio
# import mimetypes
# import traceback
# import requests
# import uuid
# from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type, wait_fixed
# from google import genai
# from google.genai import types
# from google.genai.errors import ClientError
# from langfuse import get_client

# from dotenv import load_dotenv
# load_dotenv()

# class GeminiVideoService:
#     def __init__(self):
#         self.api_key = os.getenv("GOOGLE_API_KEY")
#         self.client = genai.Client(
#             api_key=self.api_key, 
#             http_options={'api_version': 'v1alpha'}
#         )
#         self.model_name = "veo-3.1-fast-generate-preview"
#         self.temp_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "temp")

#     @retry(
#         retry=retry_if_exception_type(ClientError),
#         wait=wait_fixed(60),
#         stop=stop_after_attempt(2),
#         reraise=True
#     )
#     def _generate_video_op_with_retry(self, model, prompt, image_obj, config):
#         print("DEBUG: details of generation attempt...")
#         return self.client.models.generate_videos(
#             model=model,
#             prompt=prompt,
#             image=image_obj,
#             config=config
#         )

#     async def generate_video(self, prompt: str, image_path: str = None, duration: int = 5, aspect_ratio: str = "16:9", quality: str = "fast"):
#         """
#         Generates a video using Google Veo and downloads it locally.
#         Uses explicit Langfuse trace + generation for full observability.
#         """
#         # Get the Langfuse client (auto-discovers from env vars)
#         langfuse = get_client()

#         # Step 1: Create a trace for the entire video generation pipeline
#         with langfuse.start_as_current_span(name="video-generation") as trace_span:
#             trace_span.update_trace(
#                 name="video-generation",
#                 metadata={"quality": quality, "duration": duration, "aspect_ratio": aspect_ratio}
#             )

#             try:
#                 # RELOAD API KEY
#                 load_dotenv(override=True)
#                 self.api_key = os.getenv("GOOGLE_API_KEY")

#                 # Select model based on quality preference
#                 model_name = "veo-3.1-fast-generate-preview" if quality == "fast" else "veo-3.1-generate-preview"
#                 print(f"DEBUG: Using Google model: {model_name}")

#                 # Re-initialize client with potentially new key
#                 self.client = genai.Client(
#                     api_key=self.api_key, 
#                     http_options={'api_version': 'v1alpha'}
#                 )

#                 # Ensure duration is supported (Veo supports 4-8s)
#                 target_duration = min(max(duration, 4), 8)

#                 config = types.GenerateVideosConfig(
#                     duration_seconds=target_duration,
#                     aspect_ratio=aspect_ratio,
#                     resolution="1080p"
#                 )

#                 # Process image if provided
#                 image_obj = None
#                 if image_path and os.path.exists(image_path):
#                     mime_type, _ = mimetypes.guess_type(image_path)
#                     if not mime_type:
#                         mime_type = "image/jpeg"
#                     print(f"DEBUG: Using image {image_path} with mime_type {mime_type}")
#                     with open(image_path, "rb") as f:
#                         image_bytes = f.read()
#                         image_obj = types.Image(image_bytes=image_bytes, mime_type=mime_type)

#                 # Step 2: Create a generation span for the Veo API call
#                 with trace_span.start_as_current_generation(
#                     name="generate_video",
#                     model=model_name,
#                     input={"prompt": prompt[:500], "duration": target_duration, "aspect_ratio": aspect_ratio, "quality": quality},
#                     model_parameters={"resolution": "1080p", "duration_seconds": target_duration}
#                 ) as generation:

#                     print(f"DEBUG: Starting Gemini Veo ({quality}) generation for: {prompt[:50]}...")
#                     print(f"DEBUG: Initiating Veo ({model_name}) request with auto-retry enabled...")

#                     # Make the actual Veo API call
#                     operation = await asyncio.to_thread(
#                         self._generate_video_op_with_retry,
#                         model_name,
#                         prompt,
#                         image_obj,
#                         config
#                     )

#                     print(f"DEBUG: Veo Operation ID: {operation.name}")

#                     # Polling for completion
#                     start_time = time.time()
#                     timeout = 900  # 15 minutes

#                     while True:
#                         if time.time() - start_time > timeout:
#                             print(f"DEBUG: Gemini Veo generation timed out after {timeout}s.")
#                             generation.update(
#                                 output={"status": "timeout", "error": f"Timed out after {timeout}s"},
#                                 level="ERROR",
#                                 status_message="Generation timed out"
#                             )
#                             return None

#                         await asyncio.sleep(30)
#                         try:
#                             operation = self.client.operations.get(operation=operation)
#                             print(f"DEBUG: Veo Status... Done: {operation.done}")
#                             if operation.done:
#                                 break
#                         except Exception as poll_err:
#                             print(f"DEBUG: Polling error: {poll_err}")
#                             continue

#                     if operation.error:
#                         error_msg = f"Veo Operation Error: {operation.error}"
#                         print(f"DEBUG: {error_msg}")
#                         generation.update(
#                             output={"status": "error", "error": error_msg},
#                             level="ERROR",
#                             status_message=error_msg
#                         )
#                         raise Exception(error_msg)

#                     # Get the result URL and download it locally
#                     if operation.result and operation.result.generated_videos:
#                         google_video_url = operation.result.generated_videos[0].video.uri
#                         download_url = f"{google_video_url}&key={self.api_key}"

#                         print(f"DEBUG: Downloading video from Google...")
#                         local_filename = f"gemini_video_{uuid.uuid4().hex}.mp4"
#                         local_path = os.path.join(self.temp_dir, local_filename)

#                         response = requests.get(download_url)
#                         if response.status_code == 200:
#                             with open(local_path, "wb") as f:
#                                 f.write(response.content)
#                             print(f"DEBUG: Video saved locally to: {local_path}")

#                             # Step 3: Update generation with output + usage
#                             generation.update(
#                                 output={"video_file": local_filename, "status": "success"},
#                                 usage_details={"input": 0, "output": target_duration, "total": target_duration}
#                             )

#                             return local_filename
#                         else:
#                             error_msg = f"Failed to download video. Status: {response.status_code}"
#                             print(f"DEBUG: {error_msg}")
#                             generation.update(
#                                 output={"status": "error", "error": error_msg},
#                                 level="ERROR",
#                                 status_message=error_msg
#                             )
#                             raise Exception(error_msg)

#                     generation.update(
#                         output={"status": "error", "error": "No video URL in results"},
#                         level="ERROR",
#                         status_message="Operation finished but no video URL found"
#                     )
#                     raise Exception("Operation finished but no video URL found in results.")

#             except Exception as e:
#                 print(f"DEBUG: Gemini Video Service Exception: {e}")
#                 traceback.print_exc()
#                 trace_span.update(level="ERROR", status_message=str(e))
#                 raise e

# # Singleton instance
# gemini_video_service = GeminiVideoService()


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
from langfuse import get_client

from dotenv import load_dotenv
load_dotenv()

class GeminiVideoService:
    def __init__(self):
        self.api_key = os.getenv("GOOGLE_API_KEY")
        self.client = genai.Client(
            api_key=self.api_key, 
            http_options={'api_version': 'v1alpha'}
        )
        self.model_name = "veo-3.1-fast-generate-preview"
        self.temp_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "temp")

    @retry(
        retry=retry_if_exception_type(ClientError),
        wait=wait_fixed(60),
        stop=stop_after_attempt(2),
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
        Uses explicit Langfuse trace + generation for full observability.
        """
        # Get the Langfuse client (auto-discovers from env vars)
        langfuse = get_client()

        # Step 1: Create a trace for the entire video generation pipeline
        with langfuse.start_as_current_span(name="video-generation") as trace_span:
            trace_span.update_trace(
                name="video-generation",
                metadata={"quality": quality, "duration": duration, "aspect_ratio": aspect_ratio}
            )

            try:
                # RELOAD API KEY
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

                # Ensure duration is supported (Veo supports 4-8s)
                target_duration = min(max(duration, 4), 8)

                config = types.GenerateVideosConfig(
                    duration_seconds=target_duration,
                    aspect_ratio=aspect_ratio,
                    resolution="1080p"
                )

                # Process image if provided
                image_obj = None
                if image_path and os.path.exists(image_path):
                    mime_type, _ = mimetypes.guess_type(image_path)
                    if not mime_type:
                        mime_type = "image/jpeg"
                    print(f"DEBUG: Using image {image_path} with mime_type {mime_type}")
                    with open(image_path, "rb") as f:
                        image_bytes = f.read()
                        image_obj = types.Image(image_bytes=image_bytes, mime_type=mime_type)

                # Step 2: Create a generation span for the Veo API call
                with trace_span.start_as_current_generation(
                    name="generate_video",
                    model=model_name,
                    input={"prompt": prompt[:500], "duration": target_duration, "aspect_ratio": aspect_ratio, "quality": quality},
                    model_parameters={"resolution": "1080p", "duration_seconds": target_duration}
                ) as generation:

                    print(f"DEBUG: Starting Gemini Veo ({quality}) generation for: {prompt[:50]}...")
                    print(f"DEBUG: Initiating Veo ({model_name}) request with auto-retry enabled...")

                    # Make the actual Veo API call
                    operation = await asyncio.to_thread(
                        self._generate_video_op_with_retry,
                        model_name,
                        prompt,
                        image_obj,
                        config
                    )

                    print(f"DEBUG: Veo Operation ID: {operation.name}")

                    # Polling for completion
                    start_time = time.time()
                    timeout = 900  # 15 minutes

                    while True:
                        if time.time() - start_time > timeout:
                            print(f"DEBUG: Gemini Veo generation timed out after {timeout}s.")
                            generation.update(
                                output={"status": "timeout", "error": f"Timed out after {timeout}s"},
                                level="ERROR",
                                status_message="Generation timed out"
                            )
                            return None

                        await asyncio.sleep(30)
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
                        generation.update(
                            output={"status": "error", "error": error_msg},
                            level="ERROR",
                            status_message=error_msg
                        )
                        raise Exception(error_msg)

                    # Get the result URL and download it locally
                    if operation.result and operation.result.generated_videos:
                        google_video_url = operation.result.generated_videos[0].video.uri
                        download_url = f"{google_video_url}&key={self.api_key}"

                        print(f"DEBUG: Downloading video from Google...")
                        local_filename = f"gemini_video_{uuid.uuid4().hex}.mp4"
                        local_path = os.path.join(self.temp_dir, local_filename)

                        response = requests.get(download_url)
                        if response.status_code == 200:
                            with open(local_path, "wb") as f:
                                f.write(response.content)
                            print(f"DEBUG: Video saved locally to: {local_path}")

                            # Calculate estimated cost based on official 1080p video generation pricing
                            # (Veo 3.1 Fast = $0.10/s, Veo 3.1 = $0.20/s)
                            cost_per_second = 0.10 if quality == "fast" else 0.20
                            estimated_cost = target_duration * cost_per_second

                            # Step 3: Update generation with output + usage + explicit cost
                            generation.update(
                                output={"video_file": local_filename, "status": "success"},
                                usage_details={"input": 0, "output": target_duration, "total": target_duration},
                                cost=estimated_cost
                            )

                            return local_filename
                        else:
                            error_msg = f"Failed to download video. Status: {response.status_code}"
                            print(f"DEBUG: {error_msg}")
                            generation.update(
                                output={"status": "error", "error": error_msg},
                                level="ERROR",
                                status_message=error_msg
                            )
                            raise Exception(error_msg)

                    generation.update(
                        output={"status": "error", "error": "No video URL in results"},
                        level="ERROR",
                        status_message="Operation finished but no video URL found"
                    )
                    raise Exception("Operation finished but no video URL found in results.")

            except Exception as e:
                print(f"DEBUG: Gemini Video Service Exception: {e}")
                traceback.print_exc()
                trace_span.update(level="ERROR", status_message=str(e))
                raise e

# Singleton instance
gemini_video_service = GeminiVideoService()