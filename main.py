
from fastapi import FastAPI
from pydantic import BaseModel
import os
import requests
# from pytube import YouTube
import yt_dlp
import urllib3
import ssl
from dotenv import load_dotenv
load_dotenv()

app = FastAPI()

class UploadRequest(BaseModel):
    youtube_url: str


def download_small_video(youtube_url, output_folder="/tmp"):
  

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    ydl_opts = {
        'format': 'mp4[height<=360][filesize<=10M]/mp4[height<=360]/best[ext=mp4]',
        'outtmpl': f"{output_folder}/%(title)s.%(ext)s",
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
     
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(youtube_url, download=True)
        filename = ydl.prepare_filename(info)
        if not filename.endswith(".mp4"):
            filename = filename.rsplit(".", 1)[0] + ".mp4"

    return filename

# def download_small_video(youtube_url, output_folder="/tmp"):
#     if not os.path.exists(output_folder):
#         os.makedirs(output_folder)

#     try:
#         yt = YouTube(youtube_url)
        
#         # Get stream with resolution <= 360p and progressive (audio+video)
#         stream = yt.streams.filter(progressive=True, file_extension='mp4', res="360p").order_by('filesize').first()
#         if not stream:
#             raise Exception("No suitable stream found (<=360p mp4)")
        
#         filename = stream.download(output_path=output_folder)
#         return filename
#     except Exception as e:
#         raise Exception(f"Video download failed: {str(e)}")

def get_shotstack_upload_url(api_key):
    headers = {
        "Accept": "application/json",
        "x-api-key": api_key
    }

    res = requests.post("https://api.shotstack.io/ingest/stage/upload", headers=headers)
    data = res.json()

    upload_url = data.get("data", {}).get("attributes", {}).get("url")
    asset_id = data.get("data", {}).get("id")
    return upload_url, asset_id

def upload_video(upload_url, path, SHOTSTACK_API_KEY):
    ssl_context = ssl.create_default_context()
    http = urllib3.PoolManager(ssl_context=ssl_context)

    with open(path, "rb") as video_file:
        video_bytes = video_file.read()

    response = http.request(
        "PUT", upload_url,
        body=video_bytes,
        headers={"x-api-key": SHOTSTACK_API_KEY}
    )

    if response.status != 200:
        raise Exception("Upload failed")
    return True

@app.post("/upload")
def upload_video_handler(payload: UploadRequest):
    api_key = os.getenv("SHOTSTACK_API_KEY")

    if not api_key:
        return {"success": False, "error": "Missing SHOTSTACK_API_KEY in environment"}

    try:
        video_path = download_small_video(payload.youtube_url)
        upload_url, asset_id = get_shotstack_upload_url(api_key)
        upload_video(upload_url, video_path, api_key)
        os.remove(video_path)
        return {"success": True, "asset_id": asset_id}
    except Exception as e:
        return {"success": False, "error": str(e)}

# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
