import asyncio
import yt_dlp
from pathlib import Path
import logging
import os

logger = logging.getLogger(__name__)

DOWNLOAD_DIR = Path("downloads")
DOWNLOAD_DIR.mkdir(exist_ok=True)

# GET VIDEO INFO
async def get_info(url: str):
    def _get_info():
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'noplaylist': True,

            'js_runtimes': {
                'node': {}
            },
            'remote_components': ['ejs:github'],

            'http_headers': {
                'User-Agent': 'Mozilla/5.0',
            },
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)

                return {
                    'title': info.get('title', 'Unknown'),
                    'thumbnail': info.get('thumbnail'),
                    'duration': str(info.get('duration', 0)) + 's',
                    'uploader': info.get('uploader', 'Unknown'),
                }

        except Exception as e:
            logger.error(f"YouTube info error: {str(e)}")
            raise

    return await asyncio.to_thread(_get_info)

# DOWNLOAD VIDEO / AUDIO
async def download(url: str, download_type: str = "video"):
    def _download():
        try:
            logger.info(f"Downloading: {url}")

            ydl_opts = {
                'quiet': False,
                'no_warnings': False,

                'outtmpl': str(DOWNLOAD_DIR / '%(title).70s_%(id)s.%(ext)s'),
                'restrictfilenames': True,

                'format': 'bv*+ba/b',
                'merge_output_format': 'mp4',

                'noplaylist': True,
                'nocheckcertificate': True,
                'ignoreerrors': False,

                'js_runtimes': {
                    'node': {}
                },
                'remote_components': ['ejs:github'],

                'http_headers': {
                    'User-Agent': 'Mozilla/5.0',
                    'Accept-Language': 'en-US,en;q=0.9',
                },

                'socket_timeout': 30,
                'retries': 5,
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

                possible_files = [
                    f for f in DOWNLOAD_DIR.glob(f"*{video_id}*")
                    if f.suffix.lower() in ['.mp4', '.mkv', '.webm', '.mp3', '.m4a']
                ]
                
                if not possible_files:
                    raise Exception("Downloaded file not found")

                possible_files = sorted(
                    possible_files,
                    key=lambda x: x.suffix != '.mp4'
                )

                file_path = possible_files[0]

                logger.info(f"Final file selected: {file_path}")

                if file_path.suffix.lower() in ['.htm', '.html']:
                    logger.error(f"Invalid file detected: {file_path}")
                    os.remove(file_path)
                    raise Exception("Invalid file (HTML instead of video)")

                return {
                    'title': info.get('title', 'Unknown'),
                    'thumbnail': info.get('thumbnail'),
                    'duration': f"{info.get('duration', 0) // 60}m",
                    'download_url': f"/api/download/{file_path.name}",
                }

        except Exception as e:
            logger.error(f"YouTube download error: {str(e)}")
            raise Exception(f"Failed to download YouTube video: {str(e)}")

    return await asyncio.to_thread(_download)