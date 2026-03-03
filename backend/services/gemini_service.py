import os
from google import genai
from dotenv import load_dotenv
import PIL.Image

# Load environment variables
load_dotenv()

class GeminiService:
    def __init__(self):
        self.api_key = os.getenv("GOOGLE_API_KEY")
        self.client = genai.Client(api_key=self.api_key)

    def generate_script(self, topic: str, language: str = "English", duration_seconds: int = 15):
        """
        Uses Gemini AI to generate a video script.
        """
        # Reload key to match video service behavior
        from dotenv import load_dotenv
        load_dotenv(override=True)
        self.api_key = os.getenv("GOOGLE_API_KEY")
        self.client = genai.Client(api_key=self.api_key)

        word_count = int((duration_seconds / 60) * 150)
        
        # New SDK uses just the model ID string
        model_name = "gemini-1.5-flash-latest" 
        
        try:
            print(f"DEBUG: Generating script using {model_name}...")
            prompt = f"""
            Write a video script about {topic}.
            Target Duration: {duration_seconds} seconds.
            Language: {language}
            
            Critical Requirements:
            - The script MUST be exactly {duration_seconds} seconds long when spoken at a moderate pace.
            - Aim for approximately {word_count} words total (which is roughly 2.5 words per second).
            - Output ONLY the spoken text.
            - Do NOT include scene descriptions, bracketed text, stage directions, or "Speaker:" labels.
            """
            
            response = self.client.models.generate_content(
                model=model_name,
                contents=prompt
            )
            
            if response and response.text:
                return response.text.strip()
        except Exception as e:
            print(f"DEBUG: Script generation failed: {e}")
            return f"Welcome! Today we are discussing {topic}. It's a key topic in 2025. Stay tuned for more insights!"

    def detect_gender(self, image_path: str):
        """
        Detects gender using the new SDK patterns.
        """
        try:
            from PIL import Image
            img = Image.open(image_path)
            
            # Use the new SDK client pattern
            response = self.client.models.generate_content(
                model="gemini-1.5-flash-latest",
                contents=[
                    "Is the person in this image male or female? Reply only 'male' or 'female'.",
                    img
                ]
            )
            
            result = response.text.strip().lower()
            return 'female' if 'female' in result else 'male'
        except Exception as e:
            print(f"DEBUG: Gender detection failed: {e}")
            return 'male'

# Legacy compatibility functions for main.py
_service = GeminiService()

def generate_script(topic, language="English", duration=15):
    return _service.generate_script(topic, language, duration)

def detect_gender(path):
    return _service.detect_gender(path)
