from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, HttpUrl
from typing import Literal
import logging
from pathlib import Path
from starlette.responses import FileResponse
import mimetypes

from app.services import youtube, tiktok, instagram, facebook, twitter
from app.utils.validators import is_valid_url

router = APIRouter()
logger = logging.getLogger(__name__)

DOWNLOAD_DIR = Path("downloads")
DOWNLOAD_DIR.mkdir(exist_ok=True)

class DownloadRequest(BaseModel):
    url: str
    type: Literal["video", "audio"] = "video"

class DownloadResponse(BaseModel):
    success: bool
    data: dict = None
    error: str = None

@router.post("/download", response_model=DownloadResponse)
async def download_video(request: DownloadRequest):
    """Download video from supported platforms"""
    
    try:
        url = request.url.strip()
        
        if not is_valid_url(url):
            raise HTTPException(status_code=400, detail="Invalid URL format")
        
        # Detect platform
        if "youtube.com" in url or "youtu.be" in url:
            result = await youtube.download(url, request.type)
        elif "tiktok.com" in url or "vm.tiktok.com" in url:
            result = await tiktok.download(url, request.type)
        elif "instagram.com" in url or "instagr.am" in url:
            result = await instagram.download(url, request.type)
        elif "facebook.com" in url or "fb.watch" in url:
            result = await facebook.download(url, request.type)  # ✅ Facebook
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


@router.get("/download/{filename}")
async def download_file(filename: str, background_tasks: BackgroundTasks):
    """Serve downloaded file"""
    try:
        # Security
        if ".." in filename or "/" in filename or "\\" in filename:
            raise HTTPException(status_code=400, detail="Invalid filename")
        
        file_path = DOWNLOAD_DIR / filename
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        # Valid extension
        valid_extensions = {'.mp4', '.mp3', '.webm', '.mkv', '.m4a', '.aac'}
        if file_path.suffix.lower() not in valid_extensions:
            raise HTTPException(status_code=400, detail="Invalid file type")
        
        # AUTO DETECT MIME TYPE
        mime_type, _ = mimetypes.guess_type(file_path)
        
        response = FileResponse(
            path=file_path,
            media_type=mime_type or 'application/octet-stream',
            filename=file_path.name
        )
        response.headers["Content-Disposition"] = f'attachment; filename="{file_path.name}"'
        
        return response
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Download file error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to serve file")
