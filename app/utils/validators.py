from urllib.parse import urlparse
import re

def is_valid_url(url: str) -> bool:
    """Validate URL format"""
    try:
        result = urlparse(url)
        return all([result.scheme in ['http', 'https'], result.netloc])
    except:
        return False

def extract_video_id(url: str) -> str:
    """Extract video ID from URL"""
    patterns = {
        'youtube': r'(?:youtube\.com\/watch\?v=|youtu\.be\/)([a-zA-Z0-9_-]{11})',
        'tiktok': r'tiktok\.com\/@[\w.-]+\/video\/(\d+)',
    }
    
    for platform, pattern in patterns.items():
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None