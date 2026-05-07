from faster_whisper import WhisperModel
from config import WHISPER_MODEL

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
