import asyncio
import yt_dlp
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

DOWNLOAD_DIR = Path("downloads")
DOWNLOAD_DIR.mkdir(exist_ok=True)


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

                return {
                    'title': info.get('title', 'Facebook Video'),
                    'thumbnail': info.get('thumbnail'),
                    'duration': f"{info.get('duration', 0)}s",
                    'uploader': info.get('uploader', 'Unknown'),
                }

        except Exception as e:
            logger.error(f"Facebook info error: {str(e)}")
            raise

    return await asyncio.to_thread(_get_info)


# DOWNLOAD
async def download(url: str, download_type: str = "video"):
    def _download():
        try:
            ydl_opts = {
                'outtmpl': str(DOWNLOAD_DIR / '%(title).70s_%(id)s.%(ext)s'),
                'format': 'bestvideo+bestaudio/best',
                'merge_output_format': 'mp4',
                'quiet': True,
                'no_warnings': True,
                'restrictfilenames': True,
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

                files = [
                    f for f in DOWNLOAD_DIR.iterdir()
                    if video_id in f.name and f.suffix in ['.mp4', '.mp3', '.webm', '.m4a']
                ]

                if not files:
                    raise Exception("Downloaded file not found")

                # PRIORITAS MP4
                file_path = sorted(files, key=lambda x: x.suffix != '.mp4')[0]

                return {
                    'title': info.get('title', 'Facebook Video'),
                    'thumbnail': info.get('thumbnail'),
                    'duration': f"{info.get('duration', 0) // 60}m",
                    'download_url': f"/api/download/{video_id}",
                }

        except Exception as e:
            logger.error(f"Facebook download error: {str(e)}")
            raise Exception(f"Failed to download Facebook video: {str(e)}")

    return await asyncio.to_thread(_download)