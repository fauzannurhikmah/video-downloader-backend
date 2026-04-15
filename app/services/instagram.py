import asyncio
import yt_dlp
import logging
import base64
from pathlib import Path
from app.utils.config import BASE_URL
from app.utils.format import format_size, format_smart_duration

logger = logging.getLogger(__name__)

DOWNLOAD_DIR = Path("downloads")
DOWNLOAD_DIR.mkdir(exist_ok=True)
COOKIES_PATH = Path("cookies/instagram.txt")

# GET INFO
async def get_info(url: str):
    def _get_info():
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)

                # THUMBNAIL
                thumbnail = info.get('thumbnail')

                if not thumbnail and info.get('thumbnails'):
                    thumbnail = info['thumbnails'][0].get('url')

                if not thumbnail:
                    thumbnail = info.get('url')

                # optional fallback
                if not thumbnail:
                    thumbnail = "https://via.placeholder.com/300x300?text=No+Preview"

                return {
                    'title': info.get('title', 'Instagram Media'),
                    'thumbnail': thumbnail,
                    'duration': f"{info.get('duration', 0)}s",
                    'uploader': info.get('uploader', 'Unknown'),
                }

        except Exception as e:
            logger.error(f"Instagram info error: {str(e)}")
            raise

    return await asyncio.to_thread(_get_info)

# DOWNLOAD
async def download(url: str, download_type: str = "video"):

    if not COOKIES_PATH.exists():
        logger.error("Instagram cookies have not been uploaded yet")
        raise Exception(f"Failed to load Instagram cookies")

    def _download():
        try:
            ydl_opts = {
                'outtmpl': str(DOWNLOAD_DIR / '%(title).70s_%(id)s.%(ext)s'),
                'format': 'bestvideo+bestaudio/best',
                'cookiefile': str(COOKIES_PATH),
                'merge_output_format': 'mp4',
                'quiet': True,
                'no_warnings': True,
                'restrictfilenames': True,
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0',
                    'Accept-Language': 'en-US,en;q=0.9',
                },
            }

            # AUDIO MODE
            if download_type == "audio":
                ydl_opts['format'] = 'bestaudio/best'
                ydl_opts['postprocessors'] = [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }]

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)

                if not info:
                    raise Exception("Failed to extract Instagram media")

                video_id = info.get('id')

                # FIND FILE
                files = [
                    f for f in DOWNLOAD_DIR.iterdir()
                    if video_id in f.name and f.suffix in ['.mp4', '.mp3', '.webm', '.m4a']
                ]

                if not files:
                    raise Exception("Downloaded file not found")

                # PRIORITAS MP4
                file_path = sorted(files, key=lambda x: x.suffix != '.mp4')[0]
                actual_size = file_path.stat().st_size

                # THUMBNAIL 
                thumbnail = info.get('thumbnail')

                if not thumbnail and info.get('thumbnails'):
                    thumbnail = info['thumbnails'][0].get('url')

                if not thumbnail:
                    thumbnail = info.get('url')

                if not thumbnail:
                    thumbnail = "https://via.placeholder.com/300x300?text=No+Preview"


                encoded_thumb = base64.urlsafe_b64encode(thumbnail.encode()).decode()
                return {
                    'title': info.get('title', 'Instagram Media'),
                    'type': download_type,
                    'filesize': format_size(actual_size),
                    'thumbnail': f"{BASE_URL}/api/thumbnail/{encoded_thumb}",
                    'duration': format_smart_duration(info.get('duration', 0)),
                    'download_url': f"/api/download/{video_id}",
                }

        except Exception as e:
            logger.error(f"Instagram download error: {str(e)}")
            raise Exception(f"Failed to download Instagram media: {str(e)}")

    return await asyncio.to_thread(_download)