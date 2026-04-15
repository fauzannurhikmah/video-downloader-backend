import asyncio
import yt_dlp
from pathlib import Path
import logging

from app.utils.format import format_size, format_smart_duration

logger = logging.getLogger(__name__)

DOWNLOAD_DIR = Path("downloads")
DOWNLOAD_DIR.mkdir(exist_ok=True)
COOKIES_PATH = Path("cookies/twitter.txt")


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

                # thumbnail fallback
                thumbnail = info.get('thumbnail')

                if not thumbnail and info.get('thumbnails'):
                    thumbnail = info['thumbnails'][0].get('url')

                return {
                    'title': info.get('title', 'Twitter Video'),
                    'thumbnail': thumbnail,
                    'duration': f"{info.get('duration', 0)}s",
                    'uploader': info.get('uploader', 'Unknown'),
                }

        except Exception as e:
            logger.error(f"Twitter info error: {str(e)}")
            raise

    return await asyncio.to_thread(_get_info)

# DOWNLOAD
async def download(url: str, download_type: str = "video"):
    if not COOKIES_PATH.exists():
        logger.error("Twitter/X cookies have not been uploaded yet")
        raise Exception(f"Failed to load Twitter/X cookies")

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
                    raise Exception("Failed to extract video information")

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

                # thumbnail fallback
                thumbnail = info.get('thumbnail')

                if not thumbnail and info.get('thumbnails'):
                    thumbnail = info['thumbnails'][0].get('url')

                return {
                    'title': info.get('title', 'Twitter Video'),
                    'type': download_type,
                    'filesize': format_size(actual_size),
                    'thumbnail': thumbnail,
                    'duration': format_smart_duration(info.get('duration', 0)),
                    'download_url': f"/api/download/{video_id}",
                }

        except Exception as e:
            logger.error(f"Twitter download error: {str(e)}")
            raise Exception(f"Failed to download Twitter video: {str(e)}")

    return await asyncio.to_thread(_download)