import os
from google import genai
from dotenv import load_dotenv
import PIL.Image

from langfuse import get_client

# Load environment variables
load_dotenv()

class GeminiService:
    def __init__(self):
        self.api_key = os.getenv("GOOGLE_API_KEY")
        self.client = genai.Client(api_key=self.api_key)

    def generate_script(self, topic: str, language: str = "English", duration_seconds: int = 15, model_name: str = "gemini-2.5-flash"):
        """
        Uses Gemini AI to generate a video script with explicit Langfuse tracing.
        """
        from dotenv import load_dotenv
        load_dotenv(override=True)
        self.api_key = os.getenv("GOOGLE_API_KEY")
        self.client = genai.Client(api_key=self.api_key)

        word_count = int((duration_seconds / 60) * 150)

        langfuse = get_client()

        # Create trace + generation (like JS SDK pattern)
        with langfuse.start_as_current_span(name="script-generation") as trace_span:
            trace_span.update_trace(
                name="script-generation",
                metadata={"topic": topic[:100], "language": language, "duration": duration_seconds}
            )

            prompt_text = f"""
            Write a video script about {topic}.
            Target Duration: {duration_seconds} seconds.
            Language: {language}
            
            Critical Requirements:
            - The script MUST be exactly {duration_seconds} seconds long when spoken at a moderate pace.
            - Aim for approximately {word_count} words total (which is roughly 2.5 words per second).
            - Output ONLY the spoken text.
            - Do NOT include scene descriptions, bracketed text, stage directions, or "Speaker:" labels.
            """

            with trace_span.start_as_current_generation(
                name="generate_script",
                model=model_name,
                input={"topic": topic, "language": language, "duration_seconds": duration_seconds}
            ) as generation:
                try:
                    print(f"DEBUG: Generating script using {model_name}...")
                    response = self.client.models.generate_content(
                        model=model_name,
                        contents=prompt_text
                    )

                    usage = response.usage_metadata
                    input_tokens = usage.prompt_token_count
                    output_tokens = usage.candidates_token_count

                    if response and response.text:
                        script = response.text.strip()
                        generation.update(
                            output=script[:500],
                            usage_details={
                                "input": input_tokens,
                                "output": output_tokens,
                                "total": input_tokens + output_tokens
                            }
                        )
                        return script, input_tokens, output_tokens

                except Exception as e:
                    print(f"DEBUG: Script generation failed: {e}")
                    generation.update(
                        output={"error": str(e)},
                        level="ERROR",
                        status_message=str(e)
                    )
                    return f"Hey everyone! Today we're diving into {topic}. It's honestly one of the most interesting things happening right now, and I can't wait to share some fresh insights with you. Stay tuned!", 10, 20

    def generate_visual_prompt(self, script: str, topic: str):
        """
        Transforms a spoken script into a high-quality visual description for video generation.
        """
        model_name = "gemini-2.5-flash"
        langfuse = get_client()

        with langfuse.start_as_current_span(name="visual-prompt-generation") as trace_span:
            trace_span.update_trace(
                name="visual-prompt-generation",
                metadata={"topic": topic[:100]}
            )

            prompt_text = f"""
            Analyze this video script and topic, then write a highly detailed VISUAL PROMPT for an AI video generator (like Gemini Veo).
            
            Topic: {topic}
            Script to be spoken: {script}
            
            Visual Direction Guidelines:
            - Character Action: The person in the video should be speaking the script provided above CLEARLY. 
            - Lip-Sync: Focus on vivid, natural lip-syncing movements that match the spoken words of the script. 
            - Style: Photorealistic, cinematic, and professional.
            - Quality: 4K resolution, sharp details, cinematic lighting (studio-lit or office setting).
            - Humanization: Focus on authentic human expressions, natural micro-movements (blinking, head tilting), and lifelike skin textures.
            - Composition: Medium close-up or medium shot to show the face and shoulders clearly.
            - Atmosphere: High-end production value, shallow depth of field (bokeh background).
            
            The goal is to create a video where the character appears to be genuinely speaking the script. 
            Output ONLY the visual description paragraph.
            """

            with trace_span.start_as_current_generation(
                name="generate_visual_prompt",
                model=model_name,
                input={"topic": topic, "script": script[:200]}
            ) as generation:
                try:
                    print(f"DEBUG: Generating visual prompt for topic: {topic}...")
                    response = self.client.models.generate_content(
                        model=model_name,
                        contents=prompt_text
                    )

                    if response and response.text:
                        visual_prompt = response.text.strip()

                        usage_data = {}
                        if response.usage_metadata:
                            usage_data = {
                                "input": response.usage_metadata.prompt_token_count,
                                "output": response.usage_metadata.candidates_token_count,
                                "total": response.usage_metadata.prompt_token_count + response.usage_metadata.candidates_token_count
                            }

                        generation.update(
                            output=visual_prompt[:500],
                            usage_details=usage_data
                        )
                        return visual_prompt

                    generation.update(output="Fallback prompt used")
                    return f"A professional presenter speaking the script: '{script}' in a cinematic corporate studio with professional setup."

                except Exception as e:
                    print(f"DEBUG: Visual prompt generation failed: {e}")
                    generation.update(
                        output={"error": str(e)},
                        level="ERROR",
                        status_message=str(e)
                    )
                    return f"Cinematic high-quality video of a professional person speaking the script: {script}."

    def detect_gender(self, image_path: str):
        """
        Detects gender using Gemini with Langfuse tracking.
        """
        model_name = "gemini-2.5-flash"
        langfuse = get_client()

        with langfuse.start_as_current_span(name="gender-detection") as trace_span:
            with trace_span.start_as_current_generation(
                name="detect_gender",
                model=model_name,
                input={"image_path": image_path}
            ) as generation:
                try:
                    from PIL import Image
                    img = Image.open(image_path)

                    response = self.client.models.generate_content(
                        model=model_name,
                        contents=[
                            "Is the person in this image male or female? Reply only 'male' or 'female'.",
                            img
                        ]
                    )

                    result = response.text.strip().lower()
                    gender = 'female' if 'female' in result else 'male'

                    usage_data = {}
                    if response.usage_metadata:
                        usage_data = {
                            "input": response.usage_metadata.prompt_token_count,
                            "output": response.usage_metadata.candidates_token_count,
                            "total": response.usage_metadata.prompt_token_count + response.usage_metadata.candidates_token_count
                        }

                    generation.update(
                        output=gender,
                        usage_details=usage_data
                    )
                    return gender

                except Exception as e:
                    print(f"DEBUG: Gender detection failed: {e}")
                    generation.update(
                        output={"error": str(e)},
                        level="ERROR",
                        status_message=str(e)
                    )
                    return 'male'

# Legacy compatibility functions for main.py
_service = GeminiService()

def generate_script(topic, language="English", duration=15):
    return _service.generate_script(topic, language, duration)

def detect_gender(path):
    return _service.detect_gender(path)

def generate_visual_prompt(script, topic):
    return _service.generate_visual_prompt(script, topic)
