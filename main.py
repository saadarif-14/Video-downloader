from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
import requests
from pytube import YouTube
import urllib3
import ssl
import re
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
rapid_key = os.getenv("X_RAPID_API_KEY")
rapid_host = os.getenv("X_RAPID_API_HOST")
shotstack_api_key = os.getenv("SHOTSTACK_API_KEY")

app = FastAPI()

# Request schema
class UploadRequest(BaseModel):
    youtube_url: str


def extract_video_id(youtube_url):
    regex = r"(?:v=|\/)([0-9A-Za-z_-]{11}).*"
    match = re.search(regex, youtube_url)
    if match:
        return match.group(1)
    raise ValueError("Invalid YouTube URL")


def download_small_video(youtube_url, output_folder="/tmp"):
    video_id = extract_video_id(youtube_url)

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    url = f"https://{rapid_host}/dl"
    querystring = {"id": video_id}
    headers = {
        "x-rapidapi-key": rapid_key,
        "x-rapidapi-host": rapid_host,
    }

    response = requests.get(url, headers=headers, params=querystring)
    if response.status_code != 200:
        raise Exception("Failed to get download URL from API")

    data = response.json()
    formats = data.get("formats", [])
    if not formats or not formats[0].get("url"):
        raise Exception("No downloadable video URL found.")

    video_url = formats[0]["url"]
    file_path = os.path.join(output_folder, f"{video_id}.mp4")

    video_response = requests.get(video_url, stream=True)
    video_response.raise_for_status()

    with open(file_path, "wb") as f:
        for chunk in video_response.iter_content(chunk_size=8192):
            f.write(chunk)

    print(f"✅ Downloaded {os.path.getsize(file_path)} bytes to {file_path}")
    return file_path


def get_shotstack_upload_url(api_key):
    headers = {
        "Accept": "application/json",
        "x-api-key": api_key
    }

    res = requests.post("https://api.shotstack.io/ingest/stage/upload", headers=headers)
    if res.status_code != 200:
        raise Exception("Failed to get Shotstack upload URL")

    data = res.json()
    upload_url = data.get("data", {}).get("attributes", {}).get("url")
    asset_id = data.get("data", {}).get("id")

    if not upload_url or not asset_id:
        raise Exception("Incomplete response from Shotstack")

    return upload_url, asset_id


def upload_video(upload_url, path, api_key):
    ssl_context = ssl.create_default_context()
    http = urllib3.PoolManager(ssl_context=ssl_context)

    with open(path, "rb") as video_file:
        video_bytes = video_file.read()

    response = http.request(
        "PUT", upload_url,
        body=video_bytes,
        headers={"x-api-key": api_key}
    )

    if response.status != 200:
        raise Exception("Upload failed")
    return True


@app.post("/upload")
def upload_handler(request: UploadRequest):
    if not shotstack_api_key:
        raise HTTPException(status_code=500, detail="Missing SHOTSTACK_API_KEY in environment")

    try:
        video_path = download_small_video(request.youtube_url)
        upload_url, asset_id = get_shotstack_upload_url(shotstack_api_key)
        upload_video(upload_url, video_path, shotstack_api_key)
        os.remove(video_path)
        return {"success": True, "asset_id": asset_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
