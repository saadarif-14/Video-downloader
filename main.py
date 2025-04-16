
import os
import yt_dlp
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pyngrok import ngrok
import uvicorn
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

NGROK_AUTH_TOKEN = os.getenv("NGROK_AUTH_TOKEN")
if not NGROK_AUTH_TOKEN:
    raise RuntimeError("Missing ngrok auth token. Please set it in .env or environment variable.")

ngrok.set_auth_token(NGROK_AUTH_TOKEN)

SAVE_PATH = os.path.join(os.getcwd(), "downloads")
os.makedirs(SAVE_PATH, exist_ok=True)

@app.get("/download_video/")
async def download_video(video_url: str):
    ydl_opts = {
        'format': 'best',
        'outtmpl': f'{SAVE_PATH}/%(title)s.%(ext)s',
        'noplaylist': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(video_url, download=True)
            filepath = ydl.prepare_filename(info_dict)

        def file_stream():
            with open(filepath, mode="rb") as f:
                yield from f
            os.remove(filepath)

        filename = Path(filepath).name
        return StreamingResponse(file_stream(), media_type="application/octet-stream", headers={
            "Content-Disposition": f"attachment; filename={filename}"
        })

    except yt_dlp.utils.DownloadError as e:
        raise HTTPException(status_code=400, detail=f"Download error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")

public_url = ngrok.connect(8000)
print(f"Public URL: {public_url}")

uvicorn.run(app, host="0.0.0.0", port=8000)
# import os
# import yt_dlp
# import urllib3
# import ssl
# import requests
# from fastapi import FastAPI, HTTPException
# from fastapi.responses import StreamingResponse
# from pyngrok import ngrok
# import uvicorn
# from pathlib import Path
# from dotenv import load_dotenv

# load_dotenv()

# app = FastAPI()

# NGROK_AUTH_TOKEN = os.getenv("NGROK_AUTH_TOKEN")
# SHOTSTACK_API_KEY = os.getenv("SHOTSTACK_API_KEY")

# if not NGROK_AUTH_TOKEN or not SHOTSTACK_API_KEY:
#     raise RuntimeError("Missing required environment variables.")

# ngrok.set_auth_token(NGROK_AUTH_TOKEN)

# SAVE_PATH = os.path.join(os.getcwd(), "downloads")
# os.makedirs(SAVE_PATH, exist_ok=True)

# def get_shotstack_upload_url(api_key):
#     headers = {
#         "Accept": "application/json",
#         "x-api-key": api_key
#     }
#     res = requests.post("https://api.shotstack.io/ingest/stage/upload", headers=headers)
#     if res.status_code != 200:
#         raise Exception("Failed to get Shotstack upload URL")

#     data = res.json()
#     upload_url = data.get("data", {}).get("attributes", {}).get("url")
#     asset_id = data.get("data", {}).get("id")
#     if upload_url: 
#         print("Upload URl is get successfully")

#     if not upload_url or not asset_id:
#         raise Exception("Incomplete response from Shotstack")

#     return upload_url, asset_id

# def upload_video(upload_url, path):
#     ssl_context = ssl.create_default_context()
#     http = urllib3.PoolManager(ssl_context=ssl_context)

#     with open(path, "rb") as video_file:
#         video_bytes = video_file.read()

#     response = http.request(
#         "PUT", upload_url,
#         body=video_bytes,
#         headers={"x-api-key": SHOTSTACK_API_KEY}
#     )

#     if response.status != 200:
#         print("Upload failed:", response.status, response.data.decode())
#         raise Exception("Upload failed")
#     return True

# @app.get("/download_video/")
# async def download_video(video_url: str):
#     ydl_opts = {
#         'format': 'best',
#         'outtmpl': f'{SAVE_PATH}/%(title)s.%(ext)s',
#         'noplaylist': True,
#     }

#     try:
#         with yt_dlp.YoutubeDL(ydl_opts) as ydl:
#             info_dict = ydl.extract_info(video_url, download=True)
#             filepath = ydl.prepare_filename(info_dict)

#         upload_url, asset_id = get_shotstack_upload_url(SHOTSTACK_API_KEY)
#         upload_video(upload_url, filepath)

#         os.remove(filepath)

#         return {"asset_id": asset_id}

#     except yt_dlp.utils.DownloadError as e:
#         raise HTTPException(status_code=400, detail=f"Download error: {str(e)}")
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")

# # public_url = ngrok.connect(8000)
# # print(f"Public URL: {public_url}")

# # uvicorn.run(app, host="0.0.0.0", port=8000)
# if __name__ == "__main__":
#     public_url = ngrok.connect(80)
#     print(f"Public URL: {public_url}")
#     uvicorn.run(app, host="0.0.0.0", port=80)
