import edge_tts
import os

async def generate_audio(text: str, filename: str, voice: str = "en-US-AndrewNeural", speed: int = 0, pitch: int = 0):
    """
    Converts text to speech with custom voice settings.
    speed: percentage increase/decrease (e.g., +10, -5)
    pitch: Hz increase/decrease (e.g., +5, -2)
    """
    temp_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "temp")
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)
        
    output_path = os.path.join(temp_dir, filename)
    
    # Format speed and pitch for edge-tts
    rate_str = f"{'+' if speed >= 0 else ''}{speed}%"
    pitch_str = f"{'+' if pitch >= 0 else ''}{pitch}Hz"
    
    print(f"DEBUG: TTS Voice: {voice}, Rate: {rate_str}, Pitch: {pitch_str}")
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            communicate = edge_tts.Communicate(text, voice, rate=rate_str, pitch=pitch_str)
            await communicate.save(output_path)
            return output_path
        except Exception as e:
            print(f"DEBUG: TTS Attempt {attempt+1} failed: {e}")
            if attempt == max_retries - 1:
                raise e
            await asyncio.sleep(2) # Wait 2s before retrying

if __name__ == "__main__":
    # For standalone testing ONLY
    import asyncio
    test_text = "Hello! This is a test of the automated video generation system."
    asyncio.run(generate_audio(test_text, "test_audio.mp3", "female"))
    print("Test audio generated.")
