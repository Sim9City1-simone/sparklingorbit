import re
from config import MIN_CLIP_DURATION, MAX_CLIP_DURATION

HOOK_PATTERNS = re.compile(
    r"\b(segreto|trucco|errore|scoperto|mai|sempre|incredibile|importante|attenzione"
    r"|secret|trick|mistake|never|always|incredible|important|warning|how to|come fare"
    r"|scopri|impara|guarda|ascolta|listen|watch|learn|tip|hack|best|worst|top)\b",
    re.IGNORECASE,
)

QUESTION_MARK = re.compile(r"\?")
EXCLAMATION = re.compile(r"!")


def _score_window(segments: list[dict]) -> tuple[float, int, int, int, float]:
    """Returns (score, hook_count, question_count, exclamation_count, words_per_second)."""
    if not segments:
        return 0.0, 0, 0, 0, 0.0

    full_text = " ".join(s["text"] for s in segments)
    duration = segments[-1]["end"] - segments[0]["start"]
    if duration <= 0:
        return 0.0, 0, 0, 0, 0.0

    word_count = len(full_text.split())
    wps = word_count / duration
    hooks = len(HOOK_PATTERNS.findall(full_text))
    questions = len(QUESTION_MARK.findall(full_text))
    exclamations = len(EXCLAMATION.findall(full_text))
    avg_seg_dur = duration / len(segments)
    rhythm = max(0, 1 - avg_seg_dur / 5)

    score = wps * 2.0 + hooks * 3.0 + questions * 2.0 + exclamations * 1.5 + rhythm * 2.0
    return score, hooks, questions, exclamations, wps


def _build_reason(hooks: int, questions: int, exclamations: int, wps: float, position_boost: bool) -> str:
    parts = []
    if hooks > 0:
        parts.append(f"{hooks} hook word{'s' if hooks > 1 else ''}")
    if questions > 0:
        parts.append("domanda diretta")
    if exclamations > 0:
        parts.append("esclamazione")
    if wps > 2.8:
        parts.append("ritmo molto alto")
    elif wps > 2.0:
        parts.append("ritmo alto")
    if position_boost:
        parts.append("hook iniziale")
    return " · ".join(parts) if parts else "flusso bilanciato"


def _extract_title(segments: list[dict]) -> str:
    text = " ".join(s["text"].strip() for s in segments[:3])
    sentences = re.split(r"[.!?]", text)
    title = sentences[0].strip() if sentences else text
    return title[:80] if title else "Clip"


def score_segments(transcript: dict, top_n: int = 5) -> list[dict]:
    segments = transcript.get("segments", [])
    if not segments:
        return []

    total_duration = segments[-1]["end"]
    results = []

    i = 0
    while i < len(segments):
        start_time = segments[i]["start"]

        window_segments = []
        end_time = start_time
        for k in range(i, len(segments)):
            if segments[k]["end"] - start_time > MAX_CLIP_DURATION:
                break
            window_segments.append(segments[k])
            end_time = segments[k]["end"]

        if end_time - start_time < MIN_CLIP_DURATION:
            i += 1
            continue

        is_hook = start_time < total_duration * 0.20
        score, hooks, questions, exclamations, wps = _score_window(window_segments)
        if is_hook:
            score *= 1.2

        results.append({
            "start": start_time,
            "end": end_time,
            "score": round(score, 2),
            "title": _extract_title(window_segments),
            "reason": _build_reason(hooks, questions, exclamations, wps, is_hook),
            "segments": window_segments,
        })

        i += max(1, len(window_segments) // 2)

    results.sort(key=lambda x: x["score"], reverse=True)
    selected = []
    for candidate in results:
        overlaps = any(
            not (candidate["end"] <= s["start"] or candidate["start"] >= s["end"])
            for s in selected
        )
        if not overlaps:
            selected.append(candidate)
        if len(selected) >= top_n:
            break

    return selected
