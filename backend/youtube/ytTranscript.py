from youtube_transcript_api import YouTubeTranscriptApi
import requests

def _fetch_yt_dlp(video_id: str) -> str | None:
    try:
        import yt_dlp
        url = f"https://www.youtube.com/watch?v={video_id}"
        ydl_opts = {
            'skip_download': True,
            'writesubtitles': True,
            'writeautomaticsub': True,
            'quiet': True,
            'no_warnings': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            subtitles = info.get('subtitles') or info.get('automatic_captions') or {}
            
            selected_track = None
            for lang in ['en', 'en-US', 'en-GB']:
                if lang in subtitles:
                    selected_track = subtitles[lang]
                    break
            if not selected_track and subtitles:
                selected_track = next(iter(subtitles.values()))
                
            if not selected_track:
                return None
                
            json3_url = None
            for fmt in selected_track:
                if fmt.get('ext') == 'json3':
                    json3_url = fmt.get('url')
                    break
            if not json3_url and selected_track:
                json3_url = selected_track[0].get('url')
                
            if json3_url:
                resp = requests.get(json3_url, timeout=10)
                data = resp.json()
                events = data.get('events', [])
                text_chunks = []
                for event in events:
                    segs = event.get('segs', [])
                    for seg in segs:
                        t = seg.get('utf8', '').strip()
                        if t and t != '\n':
                            text_chunks.append(t)
                res = " ".join(text_chunks).strip()
                if res:
                    return res
    except Exception as e:
        print(f"yt-dlp transcript fetch failed for {video_id}: {e}")
    return None

def yt_transcript(video_id: str) -> str | None:
    if not video_id:
        return None

    api = YouTubeTranscriptApi()

    # 1. Try direct fetch with youtube-transcript-api
    try:
        fetched = api.fetch(video_id)
        if hasattr(fetched, "to_raw_data"):
            transcript_list = fetched.to_raw_data()
        elif isinstance(fetched, list):
            transcript_list = fetched
        else:
            transcript_list = list(fetched)

        transcript = " ".join(
            chunk["text"] if isinstance(chunk, dict) else getattr(chunk, "text", str(chunk))
            for chunk in transcript_list
        )
        if transcript.strip():
            return transcript.strip()
    except Exception as e:
        print(f"Direct transcript fetch failed for {video_id}: {e}")

    # 2. Fallback using list() to search for English, auto-generated, or any available transcript
    try:
        transcript_list_obj = api.list(video_id)
        try:
            transcript_obj = transcript_list_obj.find_transcript(['en', 'en-US', 'en-GB'])
        except Exception:
            # If English not found, pick the first available transcript
            transcript_obj = next(iter(transcript_list_obj))

        fetched = transcript_obj.fetch()
        if hasattr(fetched, "to_raw_data"):
            transcript_list = fetched.to_raw_data()
        elif isinstance(fetched, list):
            transcript_list = fetched
        else:
            transcript_list = list(fetched)

        transcript = " ".join(
            chunk["text"] if isinstance(chunk, dict) else getattr(chunk, "text", str(chunk))
            for chunk in transcript_list
        )
        if transcript.strip():
            return transcript.strip()
    except Exception as e:
        print(f"Fallback transcript fetch failed for {video_id}: {e}")

    # 3. Third-tier fallback using yt-dlp (handles cloud IP limits & auto-generated tracks)
    return _fetch_yt_dlp(video_id)





