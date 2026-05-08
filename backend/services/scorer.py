import re
import json
import os
from config import MIN_CLIP_DURATION, MAX_CLIP_DURATION

# ─── LLM-based scoring (primary) ─────────────────────────────────────────────

_groq_client = None


def _get_client():
    global _groq_client
    if _groq_client is None:
        from groq import Groq
        _groq_client = Groq(api_key=os.environ["GROQ_API_KEY"])
    return _groq_client


def _llm_score(transcript: dict, top_n: int) -> list[dict]:
    segments = transcript.get("segments", [])
    if not segments:
        return []

    full_text = transcript.get("text", "")
    total_duration = segments[-1]["end"]

    seg_list = [
        {"id": s["id"], "start": round(s["start"], 1), "end": round(s["end"], 1), "text": s["text"]}
        for s in segments
    ]

    prompt = f"""Analizza questa trascrizione video e seleziona i {top_n} migliori momenti
da tagliare come short verticale (30-90 secondi).

Criteri di selezione (in ordine di priorità):
1. Clip autonoma: hook chiaro + sviluppo + conclusione (arco narrativo completo)
2. Valore standalone: comprensibile senza contesto esterno
3. Energia: variazioni di ritmo, enfasi, domande retoriche
4. Posizione: preferisci 10-70% del video (evita intro/outro generici)

Durata video: {total_duration:.0f} secondi

TRASCRIZIONE COMPLETA:
{full_text}

SEGMENTI CON TIMESTAMP:
{json.dumps(seg_list, ensure_ascii=False)}

Rispondi SOLO con JSON valido, nessun testo extra prima o dopo:
[
  {{
    "start": 12.3,
    "end": 67.8,
    "score": 0.92,
    "title": "Titolo breve del clip (max 60 char)",
    "reason": "Perché questo clip funziona come short (1-2 frasi)"
  }}
]

Regole:
- start/end devono corrispondere esattamente ai valori "start"/"end" dei segmenti
- Durata tra {MIN_CLIP_DURATION} e {MAX_CLIP_DURATION} secondi
- Nessuna sovrapposizione tra clip
- score tra 0.0 e 1.0"""

    resp = _get_client().chat.completions.create(
        model="llama-3.3-70b-versatile",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = resp.choices[0].message.content.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    clips_raw = json.loads(raw.strip())

    result = []
    for c in clips_raw[:top_n]:
        matching = [
            s for s in segments
            if s["start"] >= c["start"] - 1.0 and s["end"] <= c["end"] + 1.0
        ]
        result.append({
            "start": c["start"],
            "end": c["end"],
            "score": float(c["score"]),
            "title": c["title"],
            "reason": c["reason"],
            "segments": matching,
            "file_path": "",
        })
    return result


# ─── Regex-based scoring (fallback) ──────────────────────────────────────────

_HOOK_PATTERNS = re.compile(
    r"\b(segreto|trucco|errore|scoperto|mai|sempre|incredibile|importante|attenzione"
    r"|secret|trick|mistake|never|always|incredible|important|warning|how to|come fare"
    r"|scopri|impara|guarda|ascolta|listen|watch|learn|tip|hack|best|worst|top)\b",
    re.IGNORECASE,
)
_QUESTION_MARK = re.compile(r"\?")
_EXCLAMATION = re.compile(r"!")


def _score_window(segments: list[dict]) -> tuple[float, int, int, int, float]:
    if not segments:
        return 0.0, 0, 0, 0, 0.0
    full_text = " ".join(s["text"] for s in segments)
    duration = segments[-1]["end"] - segments[0]["start"]
    if duration <= 0:
        return 0.0, 0, 0, 0, 0.0
    wps = len(full_text.split()) / duration
    hooks = len(_HOOK_PATTERNS.findall(full_text))
    questions = len(_QUESTION_MARK.findall(full_text))
    exclamations = len(_EXCLAMATION.findall(full_text))
    rhythm = max(0, 1 - (duration / len(segments)) / 5)
    score = wps * 2.0 + hooks * 3.0 + questions * 2.0 + exclamations * 1.5 + rhythm * 2.0
    return score, hooks, questions, exclamations, wps


def _build_reason(hooks, questions, exclamations, wps, position_boost) -> str:
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


def _regex_score_fallback(transcript: dict, top_n: int) -> list[dict]:
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
            "file_path": "",
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


# ─── Public entry point ───────────────────────────────────────────────────────

def score_segments(transcript: dict, top_n: int = 5) -> list[dict]:
    """LLM clip selection with regex fallback."""
    try:
        return _llm_score(transcript, top_n)
    except Exception:
        return _regex_score_fallback(transcript, top_n)
