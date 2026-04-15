import asyncio
import yt_dlp
import logging
from pathlib import Path

from app.utils.format import format_size, format_smart_duration

logger = logging.getLogger(__name__)

DOWNLOAD_DIR = Path("downloads")
DOWNLOAD_DIR.mkdir(exist_ok=True)
COOKIES_PATH = Path("cookies/tiktok.txt")


async def download(url: str, download_type: str = "video"):
    if not COOKIES_PATH.exists():
        logger.error("Tiktok cookies have not been uploaded yet")
        raise Exception(f"Failed to load Tiktok cookies")

    def _download():
        try:
            ydl_opts = {
                'cookiefile': str(COOKIES_PATH),
                'outtmpl': str(DOWNLOAD_DIR / '%(title).70s_%(id)s.%(ext)s'),
                'format': 'bestvideo+bestaudio/best',
                'merge_output_format': 'mp4',
                'quiet': True,
                'no_warnings': True,
                'restrictfilenames': True,
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0',
                    'Accept-Language': 'en-US,en;q=0.9',
                },

            }

            if download_type == "audio":
                ydl_opts['format'] = 'bestaudio/best'
                ydl_opts['postprocessors'] = [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                }]

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)

                video_id = info.get('id')

                files = [
                    f for f in DOWNLOAD_DIR.iterdir()
                    if video_id in f.name and f.suffix in ['.mp4', '.mp3', '.webm', '.m4a']
                ]

                if not files:
                    raise Exception("Downloaded file not found")

                file_path = sorted(files, key=lambda x: x.suffix != '.mp4')[0]
                actual_size = file_path.stat().st_size

                return {
                    'title': info.get('title', 'TikTok Video'),
                    'type': download_type,
                    'thumbnail': info.get('thumbnail'),
                    'filesize': format_size(actual_size),
                    'duration': format_smart_duration(info.get('duration', 0)),
                    'download_url': f"/api/download/{video_id}", 
                }

        except Exception as e:
            logger.error(f"TikTok error: {e}")
            raise

    return await asyncio.to_thread(_download)