"""
Translation & Dubbing Service - Auto-translates scripts and generates dubbed audio.

Workflow:
1. Takes original script + target languages
2. Translates each using Gemini AI
3. Generates TTS audio for each translated script
4. Returns translations + audio paths for video overlay
"""

import os
import time
import asyncio
from google import genai
from dotenv import load_dotenv

load_dotenv()

TEMP_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "temp")

# Language to TTS voice mapping (default voice per language)
LANGUAGE_VOICE_MAP = {
    "English": {"voice": "en-US-AndrewNeural", "code": "en"},
    "English (India)": {"voice": "en-IN-PrabhatNeural", "code": "en"},
    "Hindi": {"voice": "hi-IN-MadhurNeural", "code": "hi"},
    "Bengali": {"voice": "bn-IN-BashkarNeural", "code": "bn"},
    "Gujarati": {"voice": "gu-IN-NiranjanNeural", "code": "gu"},
    "Marathi": {"voice": "mr-IN-ManoharNeural", "code": "mr"},
    "Tamil": {"voice": "ta-IN-ValluvarNeural", "code": "ta"},
    "Telugu": {"voice": "te-IN-MohanNeural", "code": "te"},
    "Kannada": {"voice": "kn-IN-GaganNeural", "code": "kn"},
    "Malayalam": {"voice": "ml-IN-MidhunNeural", "code": "ml"},
    "Spanish": {"voice": "es-ES-AlvaroNeural", "code": "es"},
    "French": {"voice": "fr-FR-HenriNeural", "code": "fr"},
    "German": {"voice": "de-DE-ConradNeural", "code": "de"},
    "Japanese": {"voice": "ja-JP-KeitaNeural", "code": "ja"},
    "Korean": {"voice": "ko-KR-InJoonNeural", "code": "ko"},
    "Chinese": {"voice": "zh-CN-YunxiNeural", "code": "zh"},
    "Arabic": {"voice": "ar-SA-HamedNeural", "code": "ar"},
    "Portuguese": {"voice": "pt-BR-AntonioNeural", "code": "pt"},
    "Russian": {"voice": "ru-RU-DmitryNeural", "code": "ru"},
    "Italian": {"voice": "it-IT-DiegoNeural", "code": "it"},
}


class TranslationService:
    def __init__(self):
        self.api_key = os.getenv("GOOGLE_API_KEY")
        self.client = genai.Client(api_key=self.api_key)

    def _refresh_client(self):
        """Reload API key and reinitialize client."""
        load_dotenv(override=True)
        self.api_key = os.getenv("GOOGLE_API_KEY")
        self.client = genai.Client(api_key=self.api_key)

    def translate_script(self, script: str, source_language: str, target_language: str) -> str:
        """
        Translate a script from source to target language using Gemini.
        
        Args:
            script: The original script text
            source_language: Source language name (e.g., 'English')
            target_language: Target language name (e.g., 'Hindi')
        
        Returns:
            Translated script text
        """
        self._refresh_client()

        try:
            prompt = f"""Translate the following video script from {source_language} to {target_language}.

CRITICAL RULES:
1. Output ONLY the translated spoken text — no labels, no brackets, no scene descriptions.
2. Keep the same tone, emotion, and energy level as the original.
3. Maintain the same approximate length (word count) for proper lip-sync timing.
4. Use natural, conversational {target_language} — not overly formal or literal translations.
5. Preserve any brand names, product names, or technical terms in English if they are commonly used that way.

Original {source_language} Script:
{script}

Translated {target_language} Script:"""

            response = self.client.models.generate_content(
                model="gemini-1.5-flash-latest",
                contents=prompt
            )

            if response and response.text:
                translated = response.text.strip()
                # Remove any "Translation:" or similar prefix the model might add
                for prefix in ["Translation:", "Translated:", f"{target_language}:", f"{target_language} Script:"]:
                    if translated.lower().startswith(prefix.lower()):
                        translated = translated[len(prefix):].strip()
                return translated

        except Exception as e:
            print(f"ERROR: Translation failed ({source_language} → {target_language}): {e}")

        return f"[Translation to {target_language} failed. Original: {script[:100]}...]"

    async def translate_to_multiple(
        self,
        script: str,
        source_language: str,
        target_languages: list[str]
    ) -> dict:
        """
        Translate a script to multiple languages.
        
        Returns:
            Dictionary of {language: translated_text}
        """
        results = {}

        for lang in target_languages:
            if lang == source_language:
                results[lang] = script
                continue

            print(f"DEBUG: Translating to {lang}...")
            translated = self.translate_script(script, source_language, lang)
            results[lang] = translated
            # Small delay to avoid rate limiting
            await asyncio.sleep(0.5)

        return results

    async def generate_dubbed_audio(
        self,
        translated_text: str,
        language: str,
        voice: str = None,
        speed: int = 0,
        pitch: int = 0
    ) -> str:
        """
        Generate TTS audio for a translated script.
        
        Args:
            translated_text: The translated script
            language: Target language name
            voice: Optional specific voice ID (uses default if not provided)
            speed: Speed adjustment percentage
            pitch: Pitch adjustment in Hz
        
        Returns:
            Path to the generated audio file
        """
        from services.tts_service import generate_audio

        # Use provided voice or default for the language
        if not voice:
            lang_config = LANGUAGE_VOICE_MAP.get(language, LANGUAGE_VOICE_MAP["English"])
            voice = lang_config["voice"]

        filename = f"dub_{language.lower().replace(' ', '_')}_{int(time.time())}.mp3"

        try:
            audio_path = await generate_audio(
                translated_text,
                filename,
                voice=voice,
                speed=speed,
                pitch=pitch
            )
            print(f"DEBUG: Dubbed audio generated for {language}: {audio_path}")
            return audio_path
        except Exception as e:
            print(f"ERROR: TTS generation failed for {language}: {e}")
            return None

    async def auto_dub(
        self,
        script: str,
        source_language: str,
        target_languages: list[str],
        speed: int = 0,
        pitch: int = 0
    ) -> list[dict]:
        """
        Complete auto-dubbing pipeline: translate + generate audio for each language.
        
        Returns:
            List of dicts with {language, translated_script, audio_path, audio_filename}
        """
        results = []

        # First translate all
        translations = await self.translate_to_multiple(script, source_language, target_languages)

        # Then generate audio for each
        for lang, translated_text in translations.items():
            print(f"DEBUG: Generating dubbed audio for {lang}...")
            audio_path = await self.generate_dubbed_audio(translated_text, lang, speed=speed, pitch=pitch)

            result = {
                "language": lang,
                "translated_script": translated_text,
                "audio_path": audio_path,
                "audio_filename": os.path.basename(audio_path) if audio_path else None
            }
            results.append(result)

        return results


# Singleton instance
translation_service = TranslationService()
