from youtube_transcript_api import YouTubeTranscriptApi

def yt_transcript(video_id: str) -> str | None:
    if not video_id:
        return None

    api = YouTubeTranscriptApi()

    # 1. Try direct fetch
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

    return None




