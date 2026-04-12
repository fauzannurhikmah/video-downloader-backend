import asyncio
import yt_dlp
import logging

logger = logging.getLogger(__name__)

async def download(url: str, download_type: str = "video"):
    """Download from TikTok"""
    def _download():
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'format': 'best' if download_type == 'video' else 'bestaudio',
            'outtmpl': 'downloads/%(id)s',
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            return {
                'title': info.get('title', 'TikTok Video'),
                'thumbnail': info.get('thumbnail'),
                'duration': f"{info.get('duration', 0) // 60}s",
                'download_url': f"/downloads/{info['id']}.mp4",
            }
    
    return await asyncio.to_thread(_download)