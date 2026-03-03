import requests
import time
import os
import base64
from dotenv import load_dotenv

load_dotenv()

DID_API_KEY = os.getenv("DID_API_KEY")
BASE_URL = os.getenv("BASE_URL")

def get_auth_header():
    if not DID_API_KEY or "your_did_api_key" in DID_API_KEY:
        return None
    auth_str = DID_API_KEY
    if ":" in auth_str:
        encoded_auth = base64.b64encode(auth_str.encode()).decode()
    else:
        encoded_auth = auth_str
    return {"Authorization": f"Basic {encoded_auth}", "Content-Type": "application/json"}

def upload_to_did(file_path: str, endpoint: str):
    headers = get_auth_header()
    del headers["Content-Type"] # Files use multipart, not json
    url = f"https://api.d-id.com/{endpoint}"
    file_field = "image" if endpoint == "images" else "audio"
    
    with open(file_path, "rb") as f:
        files = {file_field: f}
        response = requests.post(url, files=files, headers=headers)
        if response.status_code not in [200, 201]:
            print(f"DEBUG: Upload failed ({endpoint}): {response.status_code} - {response.text}")
            return None
        return response.json().get("url")

def poll_video(talk_id, headers):
    url = f"https://api.d-id.com/talks/{talk_id}"
    print(f"Polling video {talk_id}...")
    start_time = time.time()
    while time.time() - start_time < 120: # 2 minute timeout
        response = requests.get(url, headers=headers)
        data = response.json()
        status = data.get("status")
        if status == "done":
            return data.get("result_url")
        elif status == "error":
            error_data = data.get("error", {})
            desc = data.get("description", "")
            if "moderation" in str(data).lower() or "rekognition" in str(data).lower():
                print(f"D-ID MODERATION ERROR: The AI could not process this image. Try a clearer photo of a face.")
            else:
                print(f"D-ID Generation Error Record: {data}")
            return None
        time.sleep(5)
    return None

def create_video(image_path: str, audio_path: str, image_url: str = None, audio_url: str = None, background_type: str = "original"):
    """
    Final generation with custom background and widescreen config.
    """
    headers = get_auth_header()
    if not headers:
        return "https://res.cloudinary.com/dmsf7u0tc/video/upload/v1708000000/placeholder_video.mp4"

    # Define config based on user choice
    # 'stitch' keeps the head on the original body/background
    use_stitch = True if background_type == "original" else False
    
    methods = [
        {
            "name": "Pro Studio Render", 
            "use_did_assets": True, 
            "config": {
                "fluent": "true", 
                "stitch": use_stitch,
                "result_format": "mp4",
                "align_driver": True
            }
        },
        {"name": "Public URL Fallback", "use_did_assets": False, "config": None}
    ]

    did_assets = None
    if any(m["use_did_assets"] for m in methods):
        print("Uploading assets to D-ID...")
        did_image_url = upload_to_did(image_path, "images")
        did_audio_url = upload_to_did(audio_path, "audios")
        if did_image_url and did_audio_url:
            did_assets = (did_image_url, did_audio_url)
            print("Assets uploaded. Waiting 3s...")
            time.sleep(3)

    for method in methods:
        print(f"ATTEMPTING METHOD: {method['name']}...")
        
        img = did_assets[0] if method["use_did_assets"] and did_assets else image_url
        aud = did_assets[1] if method["use_did_assets"] and did_assets else audio_url
        
        if not img or not aud:
            continue
            
        payload = {
            "source_url": img,
            "script": {
                "type": "audio",
                "audio_url": aud
            }
        }
        if method["config"]:
            payload["config"] = method["config"]

        try:
            url = "https://api.d-id.com/talks"
            response = requests.post(url, json=payload, headers=headers)
            if response.status_code == 201:
                talk_id = response.json()["id"]
                result = poll_video(talk_id, headers)
                if result:
                    return result
            else:
                print(f"DEBUG: {method['name']} failed with {response.status_code}: {response.text}")
        except Exception as e:
            print(f"DEBUG: {method['name']} error: {e}")

    print("CRITICAL: All D-ID attempts failed. This is likely due to insufficient credits or image moderation.")
    return None

if __name__ == "__main__":
    print("Robust Experimental Video Service Loaded.")
