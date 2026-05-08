import re as _re
from faster_whisper import WhisperModel
from config import WHISPER_MODEL

try:
    from youtube_transcript_api import YouTubeTranscriptApi
    _YT_TRANSCRIPT_AVAILABLE = True
except ImportError:
    _YT_TRANSCRIPT_AVAILABLE = False

_YT_ID_RE = _re.compile(r'(?:v=|youtu\.be/|embed/)([a-zA-Z0-9_-]{11})')


def _video_id(url: str) -> str:
    m = _YT_ID_RE.search(url)
    if not m:
        raise ValueError(f"Cannot extract video ID from: {url}")
    return m.group(1)


def _snippets_to_whisper(snippets: list) -> dict:
    """Convert youtube-transcript-api snippets to Whisper-like dict with interpolated word timestamps."""
    segments = []
    full_text_parts = []
    for i, snip in enumerate(snippets):
        text = snip["text"].strip()
        start = float(snip["start"])
        duration = float(snip.get("duration", 3.0))
        end = start + duration
        words_raw = text.split()
        n = len(words_raw)
        word_dur = duration / n if n else duration
        words = [
            {"word": " " + w, "start": start + j * word_dur, "end": start + (j + 1) * word_dur}
            for j, w in enumerate(words_raw)
        ]
        segments.append({"id": i, "start": start, "end": end, "text": " " + text, "words": words})
        full_text_parts.append(text)
    return {"text": " ".join(full_text_parts), "segments": segments}


def transcribe_from_url(url: str) -> dict | None:
    """
    Fetch YouTube captions without downloading audio.
    Returns None if unavailable — caller falls back to Whisper.
    Uses youtube-transcript-api v1.x API.
    """
    if not _YT_TRANSCRIPT_AVAILABLE:
        return None
    try:
        video_id = _video_id(url)
        langs = ["it", "en", "it-IT", "en-US"]
        tlist = YouTubeTranscriptApi.list(video_id)
        t = tlist.find_transcript(langs)
        snippets = t.fetch()
        return _snippets_to_whisper(list(snippets))
    except Exception:
        return None

_model: WhisperModel | None = None

_MODEL_NAMES = {
    "tiny": "tiny",
    "base": "base",
    "small": "small",
    "medium": "medium",
    "large": "large-v3",
}


def _get_model() -> WhisperModel:
    global _model
    if _model is None:
        name = _MODEL_NAMES.get(WHISPER_MODEL, "base")
        _model = WhisperModel(name, device="cpu", compute_type="int8")
    return _model


def transcribe(audio_path: str) -> dict:
    """
    Returns Whisper result dict with 'segments' list.
    Each segment: {start, end, text, words: [{word, start, end}]}
    Uses faster-whisper (CPU, Linux-compatible).
    """
    model = _get_model()
    segments_iter, _ = model.transcribe(
        audio_path,
        word_timestamps=True,
        vad_filter=True,
    )

    segments = []
    full_text_parts = []

    for seg in segments_iter:
        words = [
            {"word": w.word, "start": w.start, "end": w.end}
            for w in (seg.words or [])
        ]
        segments.append({
            "id": seg.id,
            "start": seg.start,
            "end": seg.end,
            "text": seg.text,
            "words": words,
        })
        full_text_parts.append(seg.text.strip())

    return {
        "text": " ".join(full_text_parts),
        "segments": segments,
    }
