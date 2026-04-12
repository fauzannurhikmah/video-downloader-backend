import asyncio
import yt_dlp
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

DOWNLOAD_DIR = Path("downloads")
DOWNLOAD_DIR.mkdir(exist_ok=True)

async def get_info(url: str):
    """Extract video info dari Facebook"""
    def _get_info():
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                return {
                    'title': info.get('title', 'Facebook Video'),
                    'thumbnail': info.get('thumbnail'),
                    'duration': str(info.get('duration', 0)) + 's',
                    'uploader': info.get('uploader', 'Unknown'),
                }
        except Exception as e:
            logger.error(f"Facebook info error: {str(e)}")
            raise
    
    return await asyncio.to_thread(_get_info)

async def download(url: str, download_type: str = "video"):
    """Download video dari Facebook"""
    def _download():
        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'outtmpl': str(DOWNLOAD_DIR / '%(id)s'),
                'format': 'best[ext=mp4]' if download_type == 'video' else 'bestaudio/best',
            }
            
            if download_type == "audio":
                ydl_opts['postprocessors'] = [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }]
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                
                if not info:
                    raise Exception("Failed to extract video information")
                
                video_id = info.get('id', 'video')
                ext = 'mp3' if download_type == 'audio' else 'mp4'
                file_path = DOWNLOAD_DIR / f"{video_id}.{ext}"
                
                # Check if file exists, if not find it
                if not file_path.exists():
                    possible_files = list(DOWNLOAD_DIR.glob(f"{video_id}*"))
                    if possible_files:
                        file_path = possible_files[0]
                
                if not file_path.exists():
                    raise Exception("Downloaded file not found")
                
                return {
                    'title': info.get('title', 'Facebook Video'),
                    'thumbnail': info.get('thumbnail'),
                    'duration': f"{info.get('duration', 0) // 60}m",
                    'download_url': f"/api/download/{file_path.name}",
                }
        
        except Exception as e:
            logger.error(f"Facebook download error: {str(e)}")
            raise Exception(f"Failed to download Facebook video: {str(e)}")
    
    return await asyncio.to_thread(_download)