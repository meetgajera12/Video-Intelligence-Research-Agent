from youtube_transcript_api import YouTubeTranscriptApi

def yt_transcript(video_id: str) -> str | None:
    if not video_id:
        return None
    try:
        api = YouTubeTranscriptApi()
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
        return transcript.strip() if transcript else None
    except Exception as e:
        print(f"Error fetching transcript for {video_id}: {e}")
        return None



