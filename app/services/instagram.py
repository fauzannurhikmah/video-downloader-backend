import asyncio
import yt_dlp
import logging

logger = logging.getLogger(__name__)

async def download(url: str, download_type: str = "video"):
    """Download from Instagram"""
    def _download():
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'format': 'best',
            'outtmpl': 'downloads/%(id)s',
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            return {
                'title': info.get('title', 'Instagram Media'),
                'thumbnail': info.get('thumbnail'),
                'download_url': f"/downloads/{info['id']}.mp4",
            }
    
    return await asyncio.to_thread(_download)