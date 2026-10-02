import os
import time
import logging
from collections import OrderedDict
from typing import Optional

import requests

from youtube_transcript_api import YouTubeTranscriptApi


# ============================================================
# CONFIG
# ============================================================

logger = logging.getLogger(__name__)

SUPADATA_API_KEY = os.getenv("SUPADATA_API_KEY")

SUPADATA_URL = "https://api.supadata.ai/v1/transcript"

CACHE_SIZE = 100
REQUEST_TIMEOUT = 30


# ============================================================
# SIMPLE IN-MEMORY CACHE
# ============================================================

_transcript_cache = OrderedDict()


def _cache_get(video_id: str) -> Optional[str]:

    if video_id not in _transcript_cache:
        return None

    value = _transcript_cache.pop(video_id)

    # Move recently used item to the end
    _transcript_cache[video_id] = value

    logger.info(
        f"[TRANSCRIPT CACHE] HIT: {video_id}"
    )

    return value


def _cache_set(video_id: str, transcript: str):

    if not transcript:
        return

    if video_id in _transcript_cache:
        _transcript_cache.pop(video_id)

    _transcript_cache[video_id] = transcript

    while len(_transcript_cache) > CACHE_SIZE:
        _transcript_cache.popitem(last=False)

    logger.info(
        f"[TRANSCRIPT CACHE] STORED: {video_id}"
    )


# ============================================================
# NORMALIZE TRANSCRIPT
# ============================================================

def _normalize_transcript(data) -> str:

    if not data:
        return ""

    texts = []

    # --------------------------------------------------------
    # Supadata format
    #
    # {
    #   "lang": "en",
    #   "content": [
    #       {
    #           "text": "...",
    #           "offset": 0,
    #           "duration": 1000
    #       }
    #   ]
    # }
    # --------------------------------------------------------

    if isinstance(data, dict):

        content = data.get("content")

        if isinstance(content, list):

            for item in content:

                if isinstance(item, dict):

                    text = item.get("text")

                    if text:
                        texts.append(str(text))

                elif isinstance(item, str):

                    texts.append(item)

            return " ".join(texts).strip()

        # Sometimes APIs return text directly

        text = data.get("text")

        if isinstance(text, str):

            return text.strip()

    # --------------------------------------------------------
    # List format
    # --------------------------------------------------------

    if isinstance(data, list):

        for item in data:

            if isinstance(item, dict):

                text = item.get("text")

                if text:
                    texts.append(str(text))

            elif isinstance(item, str):

                texts.append(item)

        return " ".join(texts).strip()

    # --------------------------------------------------------
    # Raw string
    # --------------------------------------------------------

    if isinstance(data, str):

        return data.strip()

    return ""


# ============================================================
# SUPADATA
# ============================================================

def _fetch_supadata(
    video_url: str,
    video_id: str
) -> Optional[str]:

    if not SUPADATA_API_KEY:

        logger.warning(
            "[SUPADATA] SUPADATA_API_KEY not configured"
        )

        return None

    logger.info(
        f"[SUPADATA] Fetching transcript for {video_id}"
    )

    try:

        response = requests.get(
            SUPADATA_URL,
            params={
                "url": video_url
            },
            headers={
                "x-api-key": SUPADATA_API_KEY
            },
            timeout=REQUEST_TIMEOUT
        )

        logger.info(
            f"[SUPADATA] HTTP {response.status_code}"
        )

        # ----------------------------------------------------
        # Success
        # ----------------------------------------------------

        if response.status_code == 200:

            data = response.json()

            transcript = _normalize_transcript(data)

            if transcript:

                logger.info(
                    f"[SUPADATA] SUCCESS: {video_id} "
                    f"({len(transcript)} chars)"
                )

                return transcript

            logger.warning(
                f"[SUPADATA] Empty transcript: {video_id}"
            )

            return None

        # ----------------------------------------------------
        # Not found
        # ----------------------------------------------------

        if response.status_code == 404:

            logger.warning(
                f"[SUPADATA] Transcript unavailable: {video_id}"
            )

            return None

        # ----------------------------------------------------
        # Rate limit
        # ----------------------------------------------------

        if response.status_code == 429:

            logger.warning(
                "[SUPADATA] Rate limit reached"
            )

            return None

        # ----------------------------------------------------
        # Other errors
        # ----------------------------------------------------

        logger.error(
            f"[SUPADATA] Error {response.status_code}: "
            f"{response.text[:500]}"
        )

        return None

    except requests.Timeout:

        logger.error(
            f"[SUPADATA] Timeout for {video_id}"
        )

        return None

    except requests.RequestException as e:

        logger.error(
            f"[SUPADATA] Request failed: {e}"
        )

        return None

    except Exception as e:

        logger.exception(
            f"[SUPADATA] Unexpected error: {e}"
        )

        return None


# ============================================================
# DIRECT YOUTUBE TRANSCRIPT API
# ============================================================

def _fetch_youtube_transcript(
    video_id: str
) -> Optional[str]:

    logger.info(
        f"[YOUTUBE API] Trying direct transcript: {video_id}"
    )

    try:

        api = YouTubeTranscriptApi()

        # ----------------------------------------------------
        # Try English first
        # ----------------------------------------------------

        try:

            transcript = api.fetch(
                video_id,
                languages=[
                    "en",
                    "en-US",
                    "en-GB"
                ]
            )

            text = _normalize_transcript(
                transcript.to_raw_data()
                if hasattr(transcript, "to_raw_data")
                else transcript
            )

            if text:

                logger.info(
                    f"[YOUTUBE API] SUCCESS: {video_id}"
                )

                return text

        except Exception as e:

            logger.warning(
                f"[YOUTUBE API] English fetch failed: {e}"
            )

        # ----------------------------------------------------
        # Try available transcripts
        # ----------------------------------------------------

        try:

            transcript_list = api.list(video_id)

            selected = None

            # Prefer manually created transcript

            for transcript in transcript_list:

                if not transcript.is_generated:

                    selected = transcript
                    break

            # Otherwise generated transcript

            if selected is None:

                for transcript in transcript_list:

                    if transcript.is_generated:

                        selected = transcript
                        break

            if selected is None:

                logger.warning(
                    f"[YOUTUBE API] No transcript found: {video_id}"
                )

                return None

            fetched = selected.fetch()

            text = _normalize_transcript(
                fetched.to_raw_data()
                if hasattr(fetched, "to_raw_data")
                else fetched
            )

            if text:

                logger.info(
                    f"[YOUTUBE API] SUCCESS via available track: "
                    f"{video_id}"
                )

                return text

        except Exception as e:

            logger.warning(
                f"[YOUTUBE API] Track lookup failed: {e}"
            )

    except Exception as e:

        logger.warning(
            f"[YOUTUBE API] Failed: {e}"
        )

    return None


# ============================================================
# MAIN FUNCTION
# ============================================================

def yt_transcript(
    video_id: str,
    video_url: Optional[str] = None
) -> Optional[str]:

    """
    Fetch a YouTube transcript.

    Priority:

        1. Cache
        2. Supadata
        3. Direct YouTubeTranscriptApi
        4. Return None

    Supadata is intentionally first for production because
    Render/cloud IPs can be blocked by YouTube.
    """

    if not video_id:

        logger.error(
            "[TRANSCRIPT] Empty video ID"
        )

        return None

    video_id = str(video_id).strip()

    if not video_url:

        video_url = (
            f"https://www.youtube.com/watch?v={video_id}"
        )

    logger.info(
        f"[TRANSCRIPT] Starting for {video_id}"
    )

    # ========================================================
    # CACHE
    # ========================================================

    cached = _cache_get(video_id)

    if cached:

        return cached

    # ========================================================
    # METHOD 1 — SUPADATA
    # ========================================================

    if SUPADATA_API_KEY:

        transcript = _fetch_supadata(
            video_url=video_url,
            video_id=video_id
        )

        if transcript:

            _cache_set(
                video_id,
                transcript
            )

            return transcript

    else:

        logger.warning(
            "[TRANSCRIPT] SUPADATA_API_KEY missing"
        )

    # ========================================================
    # METHOD 2 — DIRECT YOUTUBE
    # ========================================================

    transcript = _fetch_youtube_transcript(
        video_id
    )

    if transcript:

        _cache_set(
            video_id,
            transcript
        )

        return transcript

    # ========================================================
    # ALL FAILED
    # ========================================================

    logger.error(
        f"[TRANSCRIPT] ALL METHODS FAILED: {video_id}"
    )

    return None