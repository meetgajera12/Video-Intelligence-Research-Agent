from urllib.parse import urlparse, parse_qs
import re

def extract_video_id(url: str) -> str | None:
    if not url:
        return None
    
    url = url.strip()
    
    # Standard 11-character video ID passed directly
    if re.fullmatch(r"[A-Za-z0-9_-]{11}", url):
        return url

    if not (url.startswith("http://") or url.startswith("https://")):
        url = "https://" + url

    try:
        parsed_url = urlparse(url)
        hostname = (parsed_url.hostname or "").lower()
        path = parsed_url.path

        if hostname in {"youtube.com", "www.youtube.com", "m.youtube.com", "music.youtube.com"}:
            if path.startswith("/shorts/"):
                parts = [p for p in path.split("/") if p]
                if len(parts) >= 2:
                    return parts[1]
            if path.startswith("/embed/"):
                parts = [p for p in path.split("/") if p]
                if len(parts) >= 2:
                    return parts[1]
            v_param = parse_qs(parsed_url.query).get("v")
            if v_param:
                return v_param[0]

        if hostname in {"youtu.be", "www.youtu.be"}:
            parts = [p for p in path.split("/") if p]
            if parts:
                return parts[0]

    except Exception:
        pass

    return None