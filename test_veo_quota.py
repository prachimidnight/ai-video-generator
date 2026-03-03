import os
import time
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

def test_veo_quota():
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("ERROR: No GOOGLE_API_KEY found in .env")
        return

    print(f"Testing Gemini Veo Quota for key: {api_key[:8]}...{api_key[-4:]}")
    
    client = genai.Client(
        api_key=api_key, 
        http_options={'api_version': 'v1alpha'}
    )
    
    model_name = "veo-3.1-fast-generate-preview"
    prompt = "A simple 5-second cinematic shot of a sunset over a calm ocean."
    
    config = types.GenerateVideosConfig(
        duration_seconds=5,
        aspect_ratio="16:9"
    )
    
    try:
        print("Starting generation request...")
        operation = client.models.generate_videos(
            model=model_name,
            prompt=prompt,
            config=config
        )
        print(f"SUCCESS! Operation started: {operation.name}")
        print("If you see this, your key has Veo quota!")
    except Exception as e:
        print("\n--- QUOTA TEST FAILED ---")
        print(f"Error Type: {type(e).__name__}")
        print(f"Message: {str(e)}")
        if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
            print("\nRESULT: This key has EXHAUSTED its Gemini Veo quota.")
            print("Try a different Google Cloud Project or wait a few hours.")
        else:
            print("\nRESULT: There is a different issue with this key.")

if __name__ == "__main__":
    test_veo_quota()
