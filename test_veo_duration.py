import sys
import os
import asyncio
from dotenv import load_dotenv

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from services.gemini_video_service import gemini_video_service

async def test():
    load_dotenv('backend/.env')
    prompt = "A futuristic city with flying cars cyberpunk style."
    # Reuse the image from the previous successful run if possible, or any image in temp
    # Let's find an image in backend/temp
    temp_dir = os.path.join(os.getcwd(), 'backend', 'temp')
    images = [f for f in os.listdir(temp_dir) if f.endswith('.png')]
    if not images:
        print("No images found in temp to test with.")
        return

    image_path = os.path.join(temp_dir, images[0])
    print(f"Testing with image: {image_path}")
    
    print("\n--- Testing Duration 8s ---")
    video_url = await gemini_video_service.generate_video(prompt, image_path, duration=8)
    if video_url:
        print(f"SUCCESS (8s): {video_url}")
    else:
        print("FAILED (8s)")

    # print("\n--- Testing Duration 6s (Fallback) ---")
    # video_url = await gemini_video_service.generate_video(prompt, image_path, duration=6)
    # if video_url:
    #     print(f"SUCCESS (6s): {video_url}")
    # else:
    #     print("FAILED (6s)")

if __name__ == '__main__':
    asyncio.run(test())
