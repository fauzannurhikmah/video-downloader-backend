def format_size(size):
    if not size:
        return "Unknown"
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024
    return f"{size:.2f} TB"


def format_smart_duration(seconds):
    if seconds is None or seconds <= 0:
        return "0s"
    
    seconds = int(seconds)
    
    # Di bawah 1 menit
    if seconds < 60:
        return f"{seconds}s"
    
    # Di bawah 1 jam (Menit + Detik)
    elif seconds < 3600:
        minutes = seconds // 60
        rem_seconds = seconds % 60
        if rem_seconds > 0:
            return f"{minutes}m {rem_seconds}s"
        return f"{minutes}m"
    
    # 1 jam ke atas (Jam + Menit)
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        if minutes > 0:
            return f"{hours}h {minutes}m"
        return f"{hours}h"