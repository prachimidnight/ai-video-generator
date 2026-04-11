import os
from google import genai
from dotenv import load_dotenv
import PIL.Image

from langfuse import Langfuse

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

        langfuse = Langfuse()
        trace = langfuse.trace(
            name="script-generation",
            metadata={"topic": topic[:100], "language": language, "duration": duration_seconds}
        )

        generation = trace.generation(
            name="generate_script",
            model=model_name,
            input={"topic": topic, "language": language, "duration_seconds": duration_seconds}
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
                generation.end(
                    output=script[:500],
                    usage={
                        "input": input_tokens,
                        "output": output_tokens,
                        "total": input_tokens + output_tokens
                    }
                )
                langfuse.flush()
                return script, input_tokens, output_tokens

        except Exception as e:
            print(f"DEBUG: Script generation failed: {e}")
            generation.end(
                output={"error": str(e)},
                level="ERROR",
                status_message=str(e)
            )
            langfuse.flush()
            return f"Hey everyone! Today we're diving into {topic}. It's honestly one of the most interesting things happening right now, and I can't wait to share some fresh insights with you. Stay tuned!", 10, 20

    def generate_visual_prompt(self, script: str, topic: str, *, use_image: bool = True, use_tts: bool = True):
        """
        Transforms a spoken script into a high-quality visual description for video generation.
        """
        model_name = "gemini-2.5-flash"
        langfuse = Langfuse()
        trace = langfuse.trace(
            name="visual-prompt-generation",
            metadata={"topic": topic[:100]}
        )

        generation = trace.generation(
            name="generate_visual_prompt",
            model=model_name,
            input={"topic": topic, "script": script[:200]}
        )

        identity_rules = ""
        if use_image:
            identity_rules = """
        Identity Rules (CRITICAL):
        - Use the provided reference face image as the ONLY person shown.
        - Keep the same identity (face, age, skin details) consistently across the entire clip.
        - Do NOT introduce additional people, characters, or faces in the background.
        """

        if use_tts:
            action_block = f"""
        Character Action:
        - The person should be speaking the script clearly and naturally.
        - Strong, believable lip-sync aligned to speech.
        - Authentic micro-movements (blinks, subtle head/shoulder shifts), realistic skin texture.

        Script to be spoken (for mouth movement): {script}
            """
        else:
            action_block = f"""
        Character Action:
        - No speaking, no lip-sync, no on-screen text.
        - Pure cinematic visuals that communicate the topic through scenes, camera motion, and lighting.
        - If a person is shown, keep it subtle and avoid dialogue-like mouth movements.

        Topic to visualize: {topic}
            """

        prompt_text = f"""
        Write a single highly-detailed VISUAL PROMPT for an AI video generator (Gemini Veo style).

        Topic: {topic}
        {identity_rules}
        Visual Direction Guidelines:
        - Style: Photorealistic, cinematic, professional.
        - Lighting: cinematic lighting, high-end look.
        - Composition: clean framing, shallow depth of field, premium production value.
        - Camera: gentle cinematic motion (dolly, slider, handheld subtle), no shaky cam.
        - Restrictions: no watermarks, no captions, no text overlays, no logos.

        {action_block}

        Output ONLY the visual description paragraph.
        """

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

                generation.end(output=visual_prompt[:500], usage=usage_data)
                langfuse.flush()
                return visual_prompt

            generation.end(output="Fallback prompt used")
            langfuse.flush()
            if use_tts:
                return f"A single professional presenter speaking the script: '{script}' in a cinematic corporate studio, photorealistic, high-end lighting, shallow depth of field."
            return f"Cinematic photorealistic visuals that communicate the topic '{topic}', premium lighting, smooth camera motion, no text overlays."

        except Exception as e:
            print(f"DEBUG: Visual prompt generation failed: {e}")
            generation.end(
                output={"error": str(e)},
                level="ERROR",
                status_message=str(e)
            )
            langfuse.flush()
            if use_tts:
                return f"Cinematic high-quality video of a single professional person speaking the script: {script}."
            return f"Cinematic high-quality visuals that communicate the topic: {topic}."

    def detect_gender(self, image_path: str):
        """
        Detects gender using Gemini with Langfuse tracking.
        """
        model_name = "gemini-2.5-flash"
        langfuse = Langfuse()
        trace = langfuse.trace(name="gender-detection")
        generation = trace.generation(
            name="detect_gender",
            model=model_name,
            input={"image_path": image_path}
        )

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

            generation.end(output=gender, usage=usage_data)
            langfuse.flush()
            return gender

        except Exception as e:
            print(f"DEBUG: Gender detection failed: {e}")
            generation.end(
                output={"error": str(e)},
                level="ERROR",
                status_message=str(e)
            )
            langfuse.flush()
            return 'male'

# Legacy compatibility functions for main.py
_service = GeminiService()

def generate_script(topic, language="English", duration=15, model_name="gemini-2.5-flash"):
    return _service.generate_script(topic, language, duration, model_name)

def detect_gender(path):
    return _service.detect_gender(path)

def generate_visual_prompt(script, topic, use_image: bool = True, use_tts: bool = True):
    return _service.generate_visual_prompt(script, topic, use_image=use_image, use_tts=use_tts)
