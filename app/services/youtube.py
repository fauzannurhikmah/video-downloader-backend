import asyncio
from fastapi import HTTPException
import yt_dlp
from pathlib import Path
import logging
import os
import re
from app.utils.format import format_size, format_smart_duration

logger = logging.getLogger(__name__)

DOWNLOAD_DIR = Path("downloads")
DOWNLOAD_DIR.mkdir(exist_ok=True)
COOKIES_PATH = Path("cookies/youtube.txt")

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

# GET QUALITIES
async def get_available_qualities(url: str):
    def _get():

        ydl_opts = {
            "quiet": True,
            "cookiefile": str(COOKIES_PATH) if COOKIES_PATH.exists() else None,
            'skip_download': True,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0',
                'Accept-Language': 'en-US,en;q=0.9',
            },
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            formats = info.get("formats", [])
            duration = info.get("duration") or 0
            best_audio = None
            audio_streams = [
                f
                for f in formats
                if f.get("vcodec") == "none" and f.get("acodec") != "none"
            ]
            if audio_streams:
                best_audio = max(audio_streams, key=lambda x: x.get("tbr") or 0)

            audio_size = 0
            if best_audio:
                audio_size = best_audio.get("filesize") or best_audio.get(
                    "filesize_approx"
                )
                if not audio_size and best_audio.get("tbr"):
                    audio_size = (best_audio["tbr"] * 1000 / 8) * duration

            result_map = {}
            for f in formats:
                if f.get("vcodec") == "none" or not f.get("height"):
                    continue

                height = f["height"]
                v_size = f.get("filesize") or f.get("filesize_approx")
                if not v_size and f.get("tbr"):
                    v_size = (f["tbr"] * 1000 / 8) * duration
                if not v_size:
                    continue
                total_estimated_size = v_size + audio_size
                if height not in result_map:
                    result_map[height] = []
                result_map[height].append(total_estimated_size)
            qualities_keys = sorted(result_map.keys())
            qualities_keys = [q for q in qualities_keys if q <= 1080]
            result = []
            max_q = max(qualities_keys) if qualities_keys else 0
            for q in qualities_keys:
                sizes = sorted(result_map[q])
                chosen = sizes[-1]
                label = f"{q}p"
                if q == 360:
                    label += " (fast)"
                elif q == 720:
                    label += " (recommended)"
                elif q == max_q:
                    label += " (best)"
                result.append(
                    {
                        "quality": q,
                        "label": label,
                        "filesize": f"~{format_size(chosen)}",
                        "bytes": int(chosen),
                    }
                )

            return result

    return await asyncio.to_thread(_get)



# DOWNLOAD VIDEO / AUDIO
async def download(url: str, download_type: str = "video", quality: int | None = None):
    import socket
    logger.info("=== YOUTUBE DOWNLOAD DEBUG START ===")
    logger.info(f"URL: {url}")
    logger.info(f"Download type: {download_type}")
    logger.info(f"Quality: {quality}")

    logger.info(f"COOKIES_PATH: {COOKIES_PATH}")
    logger.info(f"COOKIES EXISTS: {COOKIES_PATH.exists()}")

    try:
        logger.info(f"COOKIES SIZE: {COOKIES_PATH.stat().st_size} bytes")
    except Exception as e:
        logger.warning(f"COOKIES SIZE ERROR: {e}")

    logger.info(f"CURRENT WORKDIR: {os.getcwd()}")
    logger.info(f"FILE LOCATION: {Path(__file__).resolve()}")

    try:
        logger.info(f"SERVER IP: {socket.gethostbyname(socket.gethostname())}")
    except:
        pass

    if not COOKIES_PATH.exists():
        logger.error("YouTube cookies have not been uploaded yet")
        raise Exception("Failed to load YouTube cookies")

    def _download():
        try:
            import uuid

            logger.info(f"Downloading: {url}")

            unique_id = uuid.uuid4().hex
            selected_format = 'bv*+ba/b'

            if download_type == "video" and quality:
                selected_format = f"best[height<={quality}]/bestvideo[height<={quality}]+bestaudio"

            logger.info(f"Selected format: {selected_format}")

            class YTDLPLogger:
                def debug(self, msg):
                    logger.info(f"[yt-dlp DEBUG] {msg}")

                def warning(self, msg):
                    logger.warning(f"[yt-dlp WARNING] {msg}")

                def error(self, msg):
                    logger.error(f"[yt-dlp ERROR] {msg}")

            ydl_opts = {
                'quiet': False,
                'no_warnings': False,

                'cookiefile': str(COOKIES_PATH),

                'outtmpl': str(DOWNLOAD_DIR / f'%(title).70s_{unique_id}_%(id)s.%(ext)s'),
                'restrictfilenames': True,

                'format': selected_format,
                'merge_output_format': 'mp4',

                'noplaylist': True,
                'nocheckcertificate': True,
                'ignoreerrors': False,

                'js_runtimes': ['node'],
                'remote_components': ['ejs:github'],

                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122.0.0.0 Safari/537.36',
                    'Accept-Language': 'en-US,en;q=0.9',
                },

                'socket_timeout': 30,
                'retries': 5,

                'logger': YTDLPLogger()
            }

            logger.info(f"YDL OPTIONS: {ydl_opts}")

            # AUDIO MODE
            if download_type == "audio":
                ydl_opts['format'] = 'bestaudio/best'
                ydl_opts['postprocessors'] = [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }]

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                try:
                    info = ydl.extract_info(url, download=True)
                except Exception as e:
                    logger.error("=== YT-DLP HARD ERROR ===")
                    logger.error(str(e))
                    raise

                if not info:
                    raise Exception("Failed to extract video information")

                logger.info(f"Extracted info keys: {list(info.keys())}")

                video_id = info.get('id')

                # FIND FILE
                pattern = f"*{unique_id}_{video_id}*"
                logger.info(f"Searching files with pattern: {pattern}")

                possible_files = [
                    f for f in DOWNLOAD_DIR.glob(pattern)
                    if f.suffix.lower() in ['.mp4', '.mkv', '.webm', '.mp3', '.m4a']
                ]

                logger.info(f"Files found: {[str(f) for f in possible_files]}")

                if not possible_files:
                    raise Exception("Downloaded file not found")

                possible_files = sorted(
                    possible_files,
                    key=lambda x: x.stat().st_mtime,
                    reverse=True
                )

                file_path = possible_files[0]

                logger.info(f"Final file selected: {file_path}")

                if file_path.suffix.lower() in ['.htm', '.html']:
                    logger.error(f"Invalid file detected (HTML): {file_path}")
                    file_path.unlink(missing_ok=True)
                    raise Exception("Invalid file (HTML instead of video)")

                # METADATA
                title = info.get('title', 'Unknown')
                description = info.get('description', '') or ""
                official_tags = info.get('tags') or []

                import re

                title_hashtags = re.findall(r'#([^\s#]+)', title)
                desc_hashtags = re.findall(r'#([^\s#]+)', description)

                all_sources = title_hashtags + official_tags + desc_hashtags

                seen = set()
                final_tags = []

                for t in all_sources:
                    tag = t.replace('#', '').strip('.,! ').lower()
                    if tag and tag not in seen:
                        seen.add(tag)
                        final_tags.append(tag)

                lines = [line.strip() for line in description.split('\n') if line.strip()]
                clean_lines = [l for l in lines if not l.startswith(('#', 'http'))]

                short_caption = " ".join(clean_lines[:3])
                if len(clean_lines) > 3:
                    short_caption += "..."

                actual_size = file_path.stat().st_size

                logger.info("=== YOUTUBE DOWNLOAD SUCCESS ===")

                return {
                    'title': title,
                    'type': download_type,
                    'filesize': format_size(actual_size),
                    'thumbnail': info.get('thumbnail'),
                    'duration': format_smart_duration(info.get('duration', 0)),
                    'download_url': f"/api/download/{video_id}",
                    'caption': short_caption if short_caption else "No description available.",
                    'tags': final_tags
                }

        except Exception as e:
            logger.error(f"YouTube download error: {str(e)}")
            raise Exception(f"Failed to download YouTube video: {str(e)}")

    return await asyncio.to_thread(_download)