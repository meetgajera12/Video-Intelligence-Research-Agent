from __future__ import annotations

import time
from functools import lru_cache
from typing import Optional

import requests
from youtube_transcript_api import YouTubeTranscriptApi


# ============================================================
# Configuration
# ============================================================

MAX_TRANSCRIPT_CHARS = 200_000
REQUEST_TIMEOUT = 15

# Retry configuration
MAX_RETRIES = 3
INITIAL_BACKOFF = 1.5


# ============================================================
# Helpers
# ============================================================

def _limit_transcript(text: str) -> str:
    """
    Prevent extremely large transcripts from being passed
    further into the application / LLM.
    """
    text = text.strip()

    if len(text) > MAX_TRANSCRIPT_CHARS:
        print(
            f"Transcript truncated from "
            f"{len(text)} to {MAX_TRANSCRIPT_CHARS} characters."
        )
        return text[:MAX_TRANSCRIPT_CHARS]

    return text


def _normalize_transcript(fetched) -> str:
    """
    Convert different youtube-transcript-api response formats
    into a single plain string.
    """

    if hasattr(fetched, "to_raw_data"):
        transcript_list = fetched.to_raw_data()

    elif isinstance(fetched, list):
        transcript_list = fetched

    else:
        transcript_list = list(fetched)

    text_chunks = []

    for chunk in transcript_list:

        if isinstance(chunk, dict):
            text = chunk.get("text", "")

        else:
            text = getattr(chunk, "text", str(chunk))

        if text:
            text = str(text).strip()

            if text:
                text_chunks.append(text)

    return _limit_transcript(" ".join(text_chunks))


# ============================================================
# yt-dlp fallback
# ============================================================

def _fetch_yt_dlp(video_id: str) -> Optional[str]:
    """
    Fallback transcript extraction using yt-dlp.

    This is useful when youtube-transcript-api cannot retrieve
    the transcript.
    """

    try:
        import yt_dlp

    except ImportError:
        print("yt-dlp is not installed.")
        return None

    url = f"https://www.youtube.com/watch?v={video_id}"

    ydl_opts = {
        "skip_download": True,
        "writesubtitles": True,
        "writeautomaticsub": True,
        "quiet": True,
        "no_warnings": True,

        # Avoid unnecessary downloads
        "extract_flat": False,

        # Don't try to download the video itself
        "noplaylist": True,
    }

    try:

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:

            info = ydl.extract_info(
                url,
                download=False
            )

            if not info:
                return None

            # Prefer manually created subtitles,
            # then fall back to automatic captions.
            subtitles = (
                info.get("subtitles")
                or info.get("automatic_captions")
                or {}
            )

            if not subtitles:
                print(f"No subtitles found for {video_id}")
                return None

            # ------------------------------------------------
            # Select language
            # ------------------------------------------------

            selected_track = None

            preferred_languages = [
                "en",
                "en-US",
                "en-GB",
            ]

            for language in preferred_languages:

                if language in subtitles:
                    selected_track = subtitles[language]
                    break

            # If English isn't available,
            # use the first available language.
            if not selected_track:
                selected_track = next(
                    iter(subtitles.values()),
                    None
                )

            if not selected_track:
                return None

            # ------------------------------------------------
            # Select subtitle format
            # ------------------------------------------------

            json3_url = None

            for fmt in selected_track:

                if fmt.get("ext") == "json3":

                    json3_url = fmt.get("url")
                    break

            # Fall back to first available format
            if not json3_url and selected_track:

                json3_url = selected_track[0].get("url")

            if not json3_url:
                return None

            # ------------------------------------------------
            # Download subtitle data
            # ------------------------------------------------

            for attempt in range(1, MAX_RETRIES + 1):

                try:

                    response = requests.get(
                        json3_url,
                        timeout=REQUEST_TIMEOUT
                    )

                    response.raise_for_status()

                    data = response.json()

                    events = data.get("events", [])

                    text_chunks = []

                    for event in events:

                        segments = event.get("segs", [])

                        for segment in segments:

                            text = segment.get(
                                "utf8",
                                ""
                            )

                            if not text:
                                continue

                            text = text.strip()

                            if text and text != "\\n":
                                text_chunks.append(text)

                    transcript = " ".join(
                        text_chunks
                    ).strip()

                    if transcript:

                        return _limit_transcript(
                            transcript
                        )

                    return None

                except requests.RequestException as e:

                    print(
                        f"Subtitle request failed "
                        f"(attempt {attempt}/{MAX_RETRIES}): {e}"
                    )

                    if attempt < MAX_RETRIES:

                        sleep_time = (
                            INITIAL_BACKOFF
                            * (2 ** (attempt - 1))
                        )

                        time.sleep(sleep_time)

            return None

    except Exception as e:

        print(
            f"yt-dlp transcript fetch failed "
            f"for {video_id}: {e}"
        )

        return None


# ============================================================
# Main transcript function
# ============================================================

@lru_cache(maxsize=500)
def yt_transcript(video_id: str) -> Optional[str]:
    """
    Fetch YouTube transcript.

    Strategy:

    1. youtube-transcript-api direct fetch
    2. youtube-transcript-api transcript list
    3. yt-dlp fallback

    Results are cached in memory to prevent repeatedly
    requesting the same video.
    """

    # --------------------------------------------------------
    # Validate video ID
    # --------------------------------------------------------

    if not video_id:

        return None

    video_id = str(video_id).strip()

    if not video_id:

        return None

    print(f"Fetching transcript for video: {video_id}")

    # --------------------------------------------------------
    # Initialize API
    # --------------------------------------------------------

    try:

        api = YouTubeTranscriptApi()

    except Exception as e:

        print(
            f"Failed to initialize "
            f"YouTubeTranscriptApi: {e}"
        )

        api = None

    # ========================================================
    # 1. Direct fetch
    # ========================================================

    if api:

        try:

            fetched = api.fetch(video_id)

            transcript = _normalize_transcript(
                fetched
            )

            if transcript:

                print(
                    f"Transcript fetched successfully "
                    f"using direct API: {video_id}"
                )

                return transcript

        except Exception as e:

            print(
                f"Direct transcript fetch failed "
                f"for {video_id}: {e}"
            )

    # ========================================================
    # 2. Transcript list fallback
    # ========================================================

    if api:

        try:

            transcript_list_obj = api.list(
                video_id
            )

            # ----------------------------------------------
            # Try English first
            # ----------------------------------------------

            try:

                transcript_obj = (
                    transcript_list_obj.find_transcript(
                        [
                            "en",
                            "en-US",
                            "en-GB",
                        ]
                    )
                )

            except Exception:

                # ------------------------------------------
                # English unavailable.
                # Use first available transcript.
                # ------------------------------------------

                transcript_obj = next(
                    iter(transcript_list_obj)
                )

            fetched = transcript_obj.fetch()

            transcript = _normalize_transcript(
                fetched
            )

            if transcript:

                print(
                    f"Transcript fetched successfully "
                    f"using transcript list: {video_id}"
                )

                return transcript

        except Exception as e:

            print(
                f"Fallback transcript fetch failed "
                f"for {video_id}: {e}"
            )

    # ========================================================
    # 3. yt-dlp fallback
    # ========================================================

    print(
        f"Trying yt-dlp fallback for {video_id}..."
    )

    transcript = _fetch_yt_dlp(video_id)

    if transcript:

        print(
            f"Transcript fetched successfully "
            f"using yt-dlp: {video_id}"
        )

        return transcript

    # ========================================================
    # Nothing worked
    # ========================================================

    print(
        f"Unable to fetch transcript for {video_id}"
    )

    return None