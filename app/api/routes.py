from fastapi import APIRouter, HTTPException, BackgroundTasks, UploadFile, File, Form, Header, Body
from pydantic import BaseModel, HttpUrl
from typing import Literal
import logging
from pathlib import Path
from starlette.responses import FileResponse
import mimetypes
import time
from fastapi.responses import StreamingResponse
import httpx
import base64
import shutil
import os

from app.services import youtube, tiktok, instagram, facebook, twitter
from app.services.analyze import analyze
from app.utils.validators import is_valid_url
from typing import Optional


router = APIRouter()
logger = logging.getLogger(__name__)

DOWNLOAD_DIR = Path("downloads")
DOWNLOAD_DIR.mkdir(exist_ok=True)

BASE_COOKIES_DIR = Path("cookies")
BASE_COOKIES_DIR.mkdir(exist_ok=True)
ADMIN_KEY = os.getenv("ADMIN_KEY")

class DownloadRequest(BaseModel):
    url: str
    type: Literal["video", "audio"] = "video"
    quality: Optional[int] = None

class DownloadResponse(BaseModel):
    success: bool
    data: dict = None
    error: str = None

@router.get("/")
def root():
    return {"message": "API is running 🚀"}

@router.post("/analyze")
async def analyze_api(data: dict = Body(...)):
    url = data.get("url")
    download_type = data.get("type", "video")

    if not url:
        return {
            "success": False,
            "error": "URL is required"
        }
    try:
        result = await analyze(url, download_type)
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        logger.error(f"Analyze API error: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

@router.post("/download", response_model=DownloadResponse)
async def download_video(request: DownloadRequest):
    """Download video from supported platforms"""
    
    try:
        url = request.url.strip()
        
        if not is_valid_url(url):
            raise HTTPException(status_code=400, detail="Invalid URL format")
        
        # Detect platform
        if "youtube.com" in url or "youtu.be" in url:
            result = await youtube.download(url, request.type, request.quality)
        elif "tiktok.com" in url or "vm.tiktok.com" in url:
            result = await tiktok.download(url, request.type)
        elif "instagram.com" in url or "instagr.am" in url:
            result = await instagram.download(url, request.type)
        elif "facebook.com" in url or "fb.watch" in url:
            result = await facebook.download(url, request.type) 
        elif "twitter.com" in url or "x.com" in url or "t.co" in url:
            result = await twitter.download(url, request.type)
        else:
            raise HTTPException(status_code=400, detail="Platform not supported yet")
        
        return DownloadResponse(success=True, data=result)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Download error: {str(e)}")
        return DownloadResponse(
            success=False,
            error=str(e) or "Failed to download video"
        )

@router.get("/info")
async def get_video_info(url: str):
    """Get video info without downloading"""
    try:
        if not is_valid_url(url):
            raise HTTPException(status_code=400, detail="Invalid URL")
        
        # Get basic info using yt-dlp
        if "facebook.com" in url or "fb.watch" in url:
            result = await facebook.get_info(url)
        else:
            result = await youtube.get_info(url)
        
        return {"success": True, "data": result}
    
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/download/{video_id}")
async def download_file(video_id: str, background_tasks: BackgroundTasks):
    try:
        files = [
            f for f in DOWNLOAD_DIR.iterdir()
            if video_id in f.name
        ]

        if not files:
            raise HTTPException(status_code=404, detail="File not found")

        file_path = sorted(files, key=lambda x: x.suffix != '.mp4')[0]

        valid_extensions = {'.mp4', '.mp3', '.webm', '.mkv', '.m4a', '.aac'}
        if file_path.suffix.lower() not in valid_extensions:
            raise HTTPException(status_code=400, detail="Invalid file type")

        mime_type, _ = mimetypes.guess_type(file_path)

        response = FileResponse(
            path=file_path,
            media_type=mime_type or 'application/octet-stream',
            filename=file_path.name
        )

        response.headers["Content-Disposition"] = f'attachment; filename="{file_path.name}"'

        # AUTO DELETE FILE AFTER DOWNLOAD
        background_tasks.add_task(delete_file, file_path)

        return response

    except Exception as e:
        logger.error(f"Download file error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to serve file")


def delete_file(path: Path):
    import time

    for i in range(6):
        try:
            with open(path, "rb"):
                pass

            path.unlink()
            logger.info(f"Deleted file: {path}")
            return

        except Exception as e:
            logger.warning(f"Retry delete ({i+1}): {e}")
            time.sleep(2)

    logger.error(f"Failed to delete file after retries: {path}")


# PROXY THUMBNAIL INSTAGRAM
@router.get("/thumbnail/{encoded_url}")
async def proxy_thumbnail(encoded_url: str):
    try:
        real_url = base64.urlsafe_b64decode(encoded_url.encode()).decode()

        async with httpx.AsyncClient() as client:
            res = await client.get(real_url)

            return StreamingResponse(
                res.aiter_bytes(),
                media_type=res.headers.get("content-type", "image/jpeg")
            )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


ALLOWED_PLATFORMS = {
    "youtube",
    "tiktok",
    "facebook",
    "instagram",
    "twitter",
    "twitch",
}

# upload cookies to platforms
@router.post("/upload-cookies")
async def upload_cookies(
    file: UploadFile = File(...),
    platform: str = Form(...),
    x_api_key: str = Header(None)
):

    # simple auth
    if x_api_key != ADMIN_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")

    # platform validation
    if platform not in ALLOWED_PLATFORMS:
        raise HTTPException(status_code=400, detail="Invalid platform")

    # file validation
    if not file.filename.endswith(".txt"):
        raise HTTPException(status_code=400, detail="Only .txt allowed")

    # path per platform
    save_path = BASE_COOKIES_DIR / f"{platform}.txt"

    # save file
    with open(save_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return {"detail": f"{platform} cookies saved"}