from __future__ import annotations

import json
import re
import time
from collections import OrderedDict
from html import unescape
from typing import Optional
from xml.etree import ElementTree

import requests
from youtube_transcript_api import YouTubeTranscriptApi


# ============================================================
# CONFIGURATION
# ============================================================

REQUEST_TIMEOUT = 20

# Successful transcripts kept in memory.
# This prevents repeatedly fetching the same video.
CACHE_SIZE = 100


# ============================================================
# SIMPLE SUCCESS CACHE
# ============================================================

_transcript_cache: OrderedDict[str, str] = OrderedDict()


def _get_cached(video_id: str) -> Optional[str]:
    """
    Return cached transcript if available.
    Moves the item to the end so the cache behaves like LRU.
    """

    if video_id not in _transcript_cache:
        return None

    transcript = _transcript_cache.pop(video_id)

    _transcript_cache[video_id] = transcript

    print(f"[TRANSCRIPT] Cache HIT: {video_id}")

    return transcript


def _set_cached(video_id: str, transcript: str) -> None:
    """
    Store a successful transcript in the cache.
    """

    if video_id in _transcript_cache:
        _transcript_cache.pop(video_id)

    _transcript_cache[video_id] = transcript

    while len(_transcript_cache) > CACHE_SIZE:
        _transcript_cache.popitem(last=False)

    print(
        f"[TRANSCRIPT] Cached: {video_id} "
        f"({len(transcript):,} characters)"
    )


# ============================================================
# TRANSCRIPT NORMALIZATION
# ============================================================

def _normalize_transcript(fetched) -> str:
    """
    Convert youtube-transcript-api output into plain text.

    Supports current FetchedTranscript objects as well as
    older list/dict-style responses.
    """

    try:

        # Current youtube-transcript-api
        if hasattr(fetched, "to_raw_data"):
            items = fetched.to_raw_data()

        elif isinstance(fetched, list):
            items = fetched

        else:
            items = list(fetched)

    except Exception as e:

        print(
            "[TRANSCRIPT] Failed to convert transcript:",
            type(e).__name__,
            str(e)
        )

        return ""

    text_chunks = []

    for item in items:

        text = ""

        if isinstance(item, dict):

            text = item.get("text", "")

        else:

            text = getattr(
                item,
                "text",
                ""
            )

        if text is None:
            continue

        text = str(text).strip()

        if not text:
            continue

        text_chunks.append(text)

    transcript = " ".join(text_chunks)

    # Normalize excessive whitespace
    transcript = re.sub(
        r"\s+",
        " ",
        transcript
    ).strip()

    return transcript


# ============================================================
# JSON3 PARSER
# ============================================================

def _parse_json3(data: dict) -> str:
    """
    Parse YouTube JSON3 subtitle format.
    """

    events = data.get("events", [])

    text_chunks = []

    for event in events:

        segments = event.get(
            "segs",
            []
        )

        for segment in segments:

            text = segment.get(
                "utf8",
                ""
            )

            if not text:
                continue

            # JSON3 sometimes contains newline markers
            if text == "\n":
                continue

            text = text.replace(
                "\n",
                " "
            )

            text = text.strip()

            if text:
                text_chunks.append(text)

    return " ".join(text_chunks).strip()


# ============================================================
# VTT PARSER
# ============================================================

def _parse_vtt(text: str) -> str:
    """
    Parse WebVTT subtitle text.
    """

    lines = text.splitlines()

    output = []

    for line in lines:

        line = line.strip()

        if not line:
            continue

        # Skip WEBVTT header
        if line.upper().startswith("WEBVTT"):
            continue

        # Skip timestamps
        if "-->" in line:
            continue

        # Skip common VTT metadata
        if line.startswith(("NOTE", "STYLE", "REGION")):
            continue

        # Skip numeric cue indexes
        if line.isdigit():
            continue

        # Remove basic HTML/VTT tags
        line = re.sub(
            r"<[^>]+>",
            "",
            line
        )

        line = unescape(line)

        line = line.strip()

        if line:
            output.append(line)

    return " ".join(output).strip()


# ============================================================
# SRV3 / XML PARSER
# ============================================================

def _parse_xml_subtitles(text: str) -> str:
    """
    Parse XML/SRV3 style subtitle formats.
    """

    try:

        root = ElementTree.fromstring(text)

    except Exception:

        return ""

    chunks = []

    for element in root.iter():

        if element.tag.lower().endswith("text"):

            value = "".join(
                element.itertext()
            )

            value = unescape(value)

            value = value.replace(
                "\n",
                " "
            )

            value = re.sub(
                r"\s+",
                " ",
                value
            ).strip()

            if value:
                chunks.append(value)

    return " ".join(chunks).strip()


# ============================================================
# DOWNLOAD SUBTITLE URL
# ============================================================

def _download_subtitle(
    subtitle_url: str,
    extension: Optional[str] = None
) -> Optional[str]:

    try:

        response = requests.get(
            subtitle_url,
            timeout=REQUEST_TIMEOUT,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 "
                    "(Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 "
                    "(KHTML, like Gecko) "
                    "Chrome/142.0.0.0 Safari/537.36"
                )
            }
        )

        response.raise_for_status()

        content = response.text

        if not content:
            return None

        # ----------------------------------------------------
        # JSON3
        # ----------------------------------------------------

        if (
            extension
            and extension.lower() == "json3"
        ):

            try:

                data = response.json()

                result = _parse_json3(
                    data
                )

                if result:
                    return result

            except Exception:

                pass

        # ----------------------------------------------------
        # Try to detect JSON automatically
        # ----------------------------------------------------

        content_stripped = content.lstrip()

        if (
            content_stripped.startswith("{")
            and '"events"' in content_stripped
        ):

            try:

                data = json.loads(
                    content_stripped
                )

                result = _parse_json3(
                    data
                )

                if result:
                    return result

            except Exception:

                pass

        # ----------------------------------------------------
        # VTT
        # ----------------------------------------------------

        if (
            extension
            and extension.lower() in {
                "vtt",
                "webvtt"
            }
        ):

            result = _parse_vtt(
                content
            )

            if result:
                return result

        # ----------------------------------------------------
        # XML / SRV3
        # ----------------------------------------------------

        if (
            extension
            and extension.lower() in {
                "srv3",
                "srv2",
                "srv1",
                "ttml",
                "xml"
            }
        ):

            result = _parse_xml_subtitles(
                content
            )

            if result:
                return result

        # ----------------------------------------------------
        # Generic detection
        # ----------------------------------------------------

        if "WEBVTT" in content[:100]:

            result = _parse_vtt(
                content
            )

            if result:
                return result

        if (
            content_stripped.startswith("<")
            and "<text" in content_stripped
        ):

            result = _parse_xml_subtitles(
                content
            )

            if result:
                return result

        # ----------------------------------------------------
        # Last fallback
        # ----------------------------------------------------

        return re.sub(
            r"\s+",
            " ",
            content
        ).strip()

    except requests.RequestException as e:

        print(
            "[YT-DLP] Subtitle HTTP request failed:",
            type(e).__name__,
            str(e)
        )

        return None

    except Exception as e:

        print(
            "[YT-DLP] Subtitle parsing failed:",
            type(e).__name__,
            str(e)
        )

        return None


# ============================================================
# YT-DLP FALLBACK
# ============================================================

def _fetch_yt_dlp(
    video_id: str
) -> Optional[str]:

    print(
        f"[YT-DLP] Starting fallback for {video_id}"
    )

    try:

        import yt_dlp

    except ImportError:

        print(
            "[YT-DLP] yt-dlp is not installed."
        )

        return None

    video_url = (
        f"https://www.youtube.com/watch?v={video_id}"
    )

    ydl_opts = {

        # Don't download the actual video
        "skip_download": True,

        # We need subtitles
        "writesubtitles": True,

        # We also want automatically generated subtitles
        "writeautomaticsub": True,

        # Don't download playlist
        "noplaylist": True,

        # Quiet logs
        "quiet": True,

        "no_warnings": True,

        # Don't try to process video formats
        "extract_flat": False,

        # Prefer English subtitles
        "subtitleslangs": [
            "en",
            "en-US",
            "en-GB",
        ],
    }

    try:

        with yt_dlp.YoutubeDL(
            ydl_opts
        ) as ydl:

            info = ydl.extract_info(
                video_url,
                download=False
            )

        if not info:

            print(
                "[YT-DLP] No video information returned."
            )

            return None

        # ====================================================
        # Get subtitle dictionaries
        # ====================================================

        subtitles = (
            info.get("subtitles")
            or {}
        )

        automatic_captions = (
            info.get("automatic_captions")
            or {}
        )

        print(
            "[YT-DLP] Manual subtitle languages:",
            list(subtitles.keys())[:20]
        )

        print(
            "[YT-DLP] Automatic subtitle languages:",
            list(automatic_captions.keys())[:20]
        )

        # Manual subtitles have priority
        subtitle_sources = [
            (
                "manual",
                subtitles
            ),
            (
                "automatic",
                automatic_captions
            ),
        ]

        # ====================================================
        # Language selection
        # ====================================================

        preferred_languages = [
            "en",
            "en-US",
            "en-GB",
        ]

        selected_track = None
        selected_language = None
        selected_type = None

        for source_type, source in subtitle_sources:

            if not source:
                continue

            # First try preferred languages
            for language in preferred_languages:

                if language in source:

                    selected_track = source[
                        language
                    ]

                    selected_language = language
                    selected_type = source_type

                    break

            if selected_track:
                break

            # ------------------------------------------------
            # Sometimes YouTube returns variants like:
            #
            # en-US
            # en-GB
            # en-orig
            # ------------------------------------------------

            for language, track in source.items():

                if language.lower().startswith(
                    "en"
                ):

                    selected_track = track
                    selected_language = language
                    selected_type = source_type

                    break

            if selected_track:
                break

        # ====================================================
        # If English doesn't exist, use first track
        # ====================================================

        if not selected_track:

            for source_type, source in subtitle_sources:

                if source:

                    selected_language = next(
                        iter(source)
                    )

                    selected_track = source[
                        selected_language
                    ]

                    selected_type = source_type

                    break

        if not selected_track:

            print(
                f"[YT-DLP] No subtitle tracks found "
                f"for {video_id}"
            )

            return None

        print(
            f"[YT-DLP] Selected "
            f"{selected_type} subtitle: "
            f"{selected_language}"
        )

        # ====================================================
        # Try subtitle formats
        # ====================================================

        # Prefer structured formats first
        preferred_formats = [
            "json3",
            "srv3",
            "vtt",
            "ttml",
            "xml",
        ]

        # Sort available formats according to preference
        formats = list(
            selected_track
        )

        formats.sort(
            key=lambda item: (
                preferred_formats.index(
                    item.get("ext", "").lower()
                )
                if item.get("ext", "").lower()
                in preferred_formats
                else 999
            )
        )

        for fmt in formats:

            subtitle_url = fmt.get(
                "url"
            )

            extension = fmt.get(
                "ext",
                ""
            )

            if not subtitle_url:
                continue

            print(
                f"[YT-DLP] Trying subtitle format: "
                f"{extension}"
            )

            transcript = _download_subtitle(
                subtitle_url,
                extension
            )

            if transcript:

                print(
                    f"[YT-DLP] SUCCESS "
                    f"({len(transcript):,} characters)"
                )

                return transcript

        print(
            f"[YT-DLP] All subtitle formats failed "
            f"for {video_id}"
        )

        return None

    except Exception as e:

        print(
            f"[YT-DLP] Extraction failed for {video_id}: "
            f"{type(e).__name__}: {e}"
        )

        return None


# ============================================================
# MAIN TRANSCRIPT FUNCTION
# ============================================================

def yt_transcript(
    video_id: str
) -> Optional[str]:

    """
    Fetch the full YouTube transcript.

    Order:

        1. Cache
        2. youtube-transcript-api direct fetch
        3. youtube-transcript-api transcript list
        4. yt-dlp fallback

    Returns:
        Full transcript string
        or None if no transcript could be fetched.
    """

    # ========================================================
    # Validate ID
    # ========================================================

    if not video_id:

        print(
            "[TRANSCRIPT] Empty video ID."
        )

        return None

    video_id = str(
        video_id
    ).strip()

    if not video_id:

        print(
            "[TRANSCRIPT] Empty video ID."
        )

        return None

    print("=" * 70)

    print(
        f"[TRANSCRIPT] Request: {video_id}"
    )

    print("=" * 70)

    # ========================================================
    # CACHE
    # ========================================================

    cached = _get_cached(
        video_id
    )

    if cached:

        return cached

    # ========================================================
    # Initialize youtube-transcript-api
    # ========================================================

    try:

        api = YouTubeTranscriptApi()

    except Exception as e:

        print(
            "[YOUTUBE-TRANSCRIPT-API] "
            "Initialization failed:",
            type(e).__name__,
            str(e)
        )

        api = None

    # ========================================================
    # METHOD 1
    # Direct fetch
    # ========================================================

    if api:

        print(
            "[YOUTUBE-TRANSCRIPT-API] "
            "Method 1: direct fetch"
        )

        try:

            fetched = api.fetch(
                video_id,
                languages=[
                    "en",
                    "en-US",
                    "en-GB",
                ]
            )

            transcript = _normalize_transcript(
                fetched
            )

            if transcript:

                print(
                    "[YOUTUBE-TRANSCRIPT-API] "
                    f"SUCCESS: {len(transcript):,} characters"
                )

                _set_cached(
                    video_id,
                    transcript
                )

                return transcript

            print(
                "[YOUTUBE-TRANSCRIPT-API] "
                "Direct fetch returned empty transcript."
            )

        except Exception as e:

            print(
                "[YOUTUBE-TRANSCRIPT-API] "
                f"Direct fetch FAILED: "
                f"{type(e).__name__}: {e}"
            )

    # ========================================================
    # METHOD 2
    # List available transcripts
    # ========================================================

    if api:

        print(
            "[YOUTUBE-TRANSCRIPT-API] "
            "Method 2: list available transcripts"
        )

        try:

            transcript_list = api.list(
                video_id
            )

            available = []

            try:

                for item in transcript_list:

                    available.append(
                        {
                            "language": getattr(
                                item,
                                "language",
                                None
                            ),
                            "language_code": getattr(
                                item,
                                "language_code",
                                None
                            ),
                            "is_generated": getattr(
                                item,
                                "is_generated",
                                None
                            ),
                        }
                    )

            except Exception:
                pass

            print(
                "[YOUTUBE-TRANSCRIPT-API] "
                f"Available transcripts: {available}"
            )

            # ------------------------------------------------
            # Try English
            # ------------------------------------------------

            transcript_obj = None

            try:

                transcript_obj = (
                    transcript_list.find_transcript(
                        [
                            "en",
                            "en-US",
                            "en-GB",
                        ]
                    )
                )

            except Exception as e:

                print(
                    "[YOUTUBE-TRANSCRIPT-API] "
                    "English transcript not found:",
                    type(e).__name__,
                    str(e)
                )

            # ------------------------------------------------
            # If English unavailable, use first transcript
            # ------------------------------------------------

            if transcript_obj is None:

                try:

                    transcript_obj = next(
                        iter(transcript_list)
                    )

                    print(
                        "[YOUTUBE-TRANSCRIPT-API] "
                        "Using first available language."
                    )

                except Exception as e:

                    print(
                        "[YOUTUBE-TRANSCRIPT-API] "
                        "No transcript tracks available:",
                        type(e).__name__,
                        str(e)
                    )

                    transcript_obj = None

            # ------------------------------------------------
            # Fetch selected transcript
            # ------------------------------------------------

            if transcript_obj is not None:

                fetched = transcript_obj.fetch()

                transcript = _normalize_transcript(
                    fetched
                )

                if transcript:

                    print(
                        "[YOUTUBE-TRANSCRIPT-API] "
                        f"LIST SUCCESS: "
                        f"{len(transcript):,} characters"
                    )

                    _set_cached(
                        video_id,
                        transcript
                    )

                    return transcript

        except Exception as e:

            print(
                "[YOUTUBE-TRANSCRIPT-API] "
                f"List/fetch FAILED: "
                f"{type(e).__name__}: {e}"
            )

    # ========================================================
    # METHOD 3
    # yt-dlp
    # ========================================================

    print(
        "[TRANSCRIPT] "
        "Trying yt-dlp fallback..."
    )

    transcript = _fetch_yt_dlp(
        video_id
    )

    if transcript:

        _set_cached(
            video_id,
            transcript
        )

        return transcript

    # ========================================================
    # ALL METHODS FAILED
    # ========================================================

    print("=" * 70)

    print(
        f"[TRANSCRIPT] ALL METHODS FAILED: {video_id}"
    )

    print(
        "[TRANSCRIPT] Possible causes:"
    )

    print(
        "  1. Video has no captions."
    )

    print(
        "  2. Video is private/unavailable."
    )

    print(
        "  3. YouTube is blocking the Render IP."
    )

    print(
        "  4. YouTube changed its transcript/caption behavior."
    )

    print(
        "  5. Video is age/location restricted."
    )

    print("=" * 70)

    return None