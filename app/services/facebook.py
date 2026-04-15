import asyncio
import re
import yt_dlp
from pathlib import Path
import logging
from app.utils.format import format_size, format_smart_duration

logger = logging.getLogger(__name__)

DOWNLOAD_DIR = Path("downloads")
DOWNLOAD_DIR.mkdir(exist_ok=True)
COOKIES_PATH = Path("cookies/facebook.txt")

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

    if not COOKIES_PATH.exists():
        logger.error("Facebook cookies have not been uploaded yet")
        raise Exception(f"Failed to load Facebook cookies")

    def _download():
        try:
            ydl_opts = {
                'outtmpl': str(DOWNLOAD_DIR / '%(title).70s_%(id)s.%(ext)s'),
                'cookiefile': str(COOKIES_PATH),
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
                description = info.get('description', '') or ""
                title_raw = info.get('title', '') or ""

                caption_source = description if description else title_raw

                # filter trash title
                if caption_source.lower() in ["video", "watch", "watch video"]:
                    caption_source = ""


                # get clean title
                clean_caption = re.sub(r'#\S+', '', caption_source)
                clean_caption = re.sub(r'http\S+', '', clean_caption)  

                clean_caption = " ".join(clean_caption.split())
                title = clean_caption[:80] if clean_caption else "Facebook Video"

                # TAGS (from caption)
                hashtags = re.findall(r'#([^\s#]+)', caption_source)

                seen = set()
                final_tags = []

                for t in hashtags:
                    tag = t.strip('.,! ').lower()
                    if tag and tag not in seen:
                        seen.add(tag)
                        final_tags.append(tag)

                # CAPTION CLEAN
                lines = [line.strip() for line in caption_source.split('\n') if line.strip()]
                clean_lines = [l for l in lines if not l.startswith(('http'))]

                short_caption = " ".join(clean_lines[:3])
                if len(clean_lines) > 3:
                    short_caption += "..."

                files = [
                    f for f in DOWNLOAD_DIR.iterdir()
                    if video_id in f.name and f.suffix in ['.mp4', '.mp3', '.webm', '.m4a']
                ]

                if not files:
                    raise Exception("Downloaded file not found")

                # PRIORITAS MP4
                file_path = sorted(files, key=lambda x: x.suffix != '.mp4')[0]

                actual_size = file_path.stat().st_size

                return {
                    'title': title,
                    'type': download_type,
                    'filesize': format_size(actual_size),
                    'thumbnail': info.get('thumbnail'),
                    'duration': format_smart_duration(info.get('duration', 0)),
                    'download_url': f"/api/download/{video_id}",
                    'caption': short_caption if short_caption else "No caption available.",
                    'tags': final_tags
                }

        except Exception as e:
            logger.error(f"Facebook download error: {str(e)}")
            raise Exception(f"Failed to download Facebook video: {str(e)}")

    return await asyncio.to_thread(_download)