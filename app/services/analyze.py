import logging
from .youtube import get_available_qualities

logger = logging.getLogger(__name__)


def detect_platform(url: str) -> str:
    url = url.lower()

    if "youtube.com" in url or "youtu.be" in url:
        return "youtube"
    elif "facebook.com" in url or "fb.watch" in url:
        return "facebook"
    elif "twitter.com" in url or "x.com" in url:
        return "twitter"
    elif "instagram.com" in url:
        return "instagram"
    elif "tiktok.com" in url:
        return "tiktok"

    return "unknown"


async def analyze(url: str, download_type: str = "video"):
    platform = detect_platform(url)

    result = {
        "platform": platform,
        "type": download_type,
        "has_quality_options": False,
        "qualities": [],
        "default_quality": None
    }

    # YOUTUBE ONLY
    if platform == "youtube" and download_type == "video":
        try:
            qualities = await get_available_qualities(url)

            if qualities:
                default_q = next(
                    (q["quality"] for q in qualities if q["quality"] == 720),
                    qualities[-1]["quality"]
                )

                result.update({
                    "has_quality_options": True,
                    "qualities": qualities,
                    "default_quality": default_q
                })

        except Exception as e:
            logger.error(f"Analyze error (YT): {str(e)}")

    return result