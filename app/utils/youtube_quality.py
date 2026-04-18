def get_fallback_qualities(url: str, info: dict):
    width = info.get("width")
    height = info.get("height")

    is_short = False
    if "/shorts/" in url:
        is_short = True
    elif width and height and height > width:
        is_short = True

    if is_short:
        return [
            {"quality": 256, "label": "256p", "filesize": "", "bytes": 0},
            {"quality": 426, "label": "426p", "filesize": "", "bytes": 0},
            {"quality": 640, "label": "640p", "filesize": "", "bytes": 0},
            {"quality": 854, "label": "854p", "filesize": "", "bytes": 0},
            {"quality": 1080, "label": "1080p (best)", "filesize": "", "bytes": 0},
        ]
    else:
        return [
            {"quality": 144, "label": "144p", "filesize": "", "bytes": 0},
            {"quality": 240, "label": "240p", "filesize": "", "bytes": 0},
            {"quality": 360, "label": "360p (fast)", "filesize": "", "bytes": 0},
            {"quality": 480, "label": "480p", "filesize": "", "bytes": 0},
            {"quality": 720, "label": "720p (recommended)", "filesize": "", "bytes": 0},
            {"quality": 1080, "label": "1080p (best)", "filesize": "B", "bytes": 0},
        ]