import subprocess
import json
from pathlib import Path
from config import TEMP_DIR

FORMATS = {
    "9:16": (1080, 1920),
    "1:1": (1080, 1080),
    "16:9": (1920, 1080),
}

DEFAULT_STYLE = {
    "highlight_color": "FFFF00",
    "text_color": "FFFFFF",
    "outline_color": "000000",
    "font_size": 52,
    "position": "bottom",  # bottom | center | top
}


def _get_video_dimensions(video_path: str) -> tuple[int, int]:
    cmd = [
        "ffprobe", "-v", "quiet", "-print_format", "json",
        "-show_streams", "-select_streams", "v:0", video_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    info = json.loads(result.stdout)
    stream = info["streams"][0]
    return stream["width"], stream["height"]


def _rgb_to_ass_style(rgb: str) -> str:
    """RGB hex → ASS &H00BBGGRR& (for style definitions)."""
    r, g, b = rgb[0:2], rgb[2:4], rgb[4:6]
    return f"&H00{b}{g}{r}&"


def _rgb_to_ass_inline(rgb: str) -> str:
    """RGB hex → ASS &HBBGGRR& (for inline \\c tags)."""
    r, g, b = rgb[0:2], rgb[2:4], rgb[4:6]
    return f"&H{b}{g}{r}&"


def _seconds_to_ass(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def _build_ass(words: list[dict], style: dict, res_x: int, res_y: int) -> str:
    """ASS subtitles with word-by-word color highlight."""
    pos = style.get("position", "bottom")
    alignment = {"bottom": 2, "center": 5, "top": 8}.get(pos, 2)
    margin_v = 80 if pos == "bottom" else (20 if pos == "top" else 0)
    font_size = style.get("font_size", 52)

    txt_style = _rgb_to_ass_style(style.get("text_color", "FFFFFF"))
    out_style = _rgb_to_ass_style(style.get("outline_color", "000000"))
    hl_inline = _rgb_to_ass_inline(style.get("highlight_color", "FFFF00"))
    txt_inline = _rgb_to_ass_inline(style.get("text_color", "FFFFFF"))

    header = (
        "[Script Info]\n"
        "ScriptType: v4.00+\n"
        f"PlayResX: {res_x}\n"
        f"PlayResY: {res_y}\n"
        "ScaledBorderAndShadow: yes\n\n"
        "[V4+ Styles]\n"
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, "
        "OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, "
        "ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, "
        "MarginL, MarginR, MarginV, Encoding\n"
        f"Style: Default,Arial,{font_size},{txt_style},&H000000FF&,{out_style},"
        f"&H80000000&,-1,0,0,0,100,100,0.5,0,1,3,0,{alignment},30,30,{margin_v},1\n\n"
        "[Events]\n"
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
    )

    LINE_SIZE = 6
    events = []
    for i in range(0, len(words), LINE_SIZE):
        line_words = words[i: i + LINE_SIZE]
        for wi, active in enumerate(line_words):
            w_start = max(0.0, active["start"])
            w_end = active["end"]
            if w_end <= w_start:
                w_end = w_start + 0.1

            parts = []
            for j, w in enumerate(line_words):
                text = w["word"].strip()
                if j == wi:
                    parts.append(f"{{\\c{hl_inline}}}{text}{{\\c{txt_inline}}}")
                else:
                    parts.append(text)

            line_text = " ".join(parts)
            events.append(
                f"Dialogue: 0,{_seconds_to_ass(w_start)},{_seconds_to_ass(w_end)},"
                f"Default,,0,0,0,,{line_text}"
            )

    return header + "\n".join(events) + "\n"


def _crop_filter(width: int, height: int, fmt: str) -> str:
    res_x, res_y = FORMATS.get(fmt, (1080, 1920))
    target_ratio = res_x / res_y
    current_ratio = width / height

    if current_ratio > target_ratio:
        new_w = int(height * target_ratio)
        x_offset = (width - new_w) // 2
        return f"crop={new_w}:{height}:{x_offset}:0,scale={res_x}:{res_y}"
    else:
        new_h = int(width / target_ratio)
        y_offset = (height - new_h) // 2
        return f"crop={width}:{new_h}:0:{y_offset},scale={res_x}:{res_y}"


def _extract_words(segments: list[dict], clip_start: float) -> list[dict]:
    """Flatten word-level timestamps from Whisper segments, offset to clip start."""
    words = []
    for seg in segments:
        for w in seg.get("words", []):
            words.append({
                "word": w.get("word", ""),
                "start": w["start"] - clip_start,
                "end": w["end"] - clip_start,
            })
    if not words:
        for seg in segments:
            text_words = seg["text"].strip().split()
            if not text_words:
                continue
            seg_dur = (seg["end"] - seg["start"]) / len(text_words)
            for j, w in enumerate(text_words):
                words.append({
                    "word": w,
                    "start": seg["start"] - clip_start + j * seg_dur,
                    "end": seg["start"] - clip_start + (j + 1) * seg_dur,
                })
    return words


# ─── Two-person split ─────────────────────────────────────────────────────────

def _detect_two_persons(video_path: str, duration: float) -> list[tuple] | None:
    """
    Sample 3 frames and return list of 2 face bboxes if 2 persons are consistently
    detected, otherwise None. Gracefully returns None if opencv is unavailable.
    """
    try:
        import cv2
    except ImportError:
        return None

    faces_per_frame: list[list] = []
    for t_pct in [0.2, 0.5, 0.7]:
        t = duration * t_pct
        frame_path = str(Path(video_path).parent / f"_face_{int(t * 1000)}.jpg")
        try:
            subprocess.run(
                ["ffmpeg", "-y", "-ss", str(t), "-i", video_path,
                 "-vframes", "1", "-q:v", "2", frame_path],
                check=True, capture_output=True, timeout=15,
            )
            img = cv2.imread(frame_path)
            if img is None:
                continue
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            cascade = cv2.CascadeClassifier(
                cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
            )
            faces = cascade.detectMultiScale(
                gray, scaleFactor=1.1, minNeighbors=4, minSize=(60, 60)
            )
            if len(faces) > 0:
                faces_per_frame.append(list(faces))
        except Exception:
            pass
        finally:
            Path(frame_path).unlink(missing_ok=True)

    if not faces_per_frame:
        return None

    two_face_frames = [f for f in faces_per_frame if len(f) == 2]
    # Require majority of sampled frames to agree on 2 faces
    if len(two_face_frames) < max(1, len(faces_per_frame) // 2):
        return None

    return [tuple(int(v) for v in face) for face in two_face_frames[0]]


def _build_dual_filter_complex(
    faces: list[tuple], src_w: int, src_h: int, ass_path: Path
) -> tuple[str, list[str]]:
    """
    Build ffmpeg -filter_complex string for 2-person vertical split → 1080×1920.
    Each half is 1080×960; faces sorted left→right become top→bottom.
    Returns (filter_complex_str, map_args).
    """
    target_w, half_h = 1080, 960
    crop_aspect = target_w / half_h  # 1.125

    sorted_faces = sorted(faces, key=lambda f: f[0])  # left face → top half
    parts: list[str] = []
    labels = ["[v0]", "[v1]"]

    for i, (fx, fy, fw, fh) in enumerate(sorted_faces[:2]):
        cx = fx + fw // 2
        cy = fy + fh // 2

        if src_w >= src_h * crop_aspect:
            ch = src_h
            cw = int(src_h * crop_aspect)
        else:
            cw = src_w
            ch = int(src_w / crop_aspect)

        cx0 = max(0, min(cx - cw // 2, src_w - cw))
        cy0 = max(0, min(cy - ch // 2, src_h - ch))

        parts.append(
            f"[0:v]crop={cw}:{ch}:{cx0}:{cy0},scale={target_w}:{half_h}{labels[i]}"
        )

    parts.append(f"{labels[0]}{labels[1]}vstack=inputs=2[stacked]")
    # Escape path for filter_complex (colons are special on Windows, safe on Unix)
    ass_str = str(ass_path).replace("\\", "/")
    parts.append(f"[stacked]ass='{ass_str}'[out]")

    filter_complex = ";".join(parts)
    map_args = ["-map", "[out]", "-map", "0:a?"]
    return filter_complex, map_args


# ─── Render ───────────────────────────────────────────────────────────────────

def render_clip(
    job_id: str,
    clip_idx: int,
    video_path: str,
    seg: dict,
    fmt: str = "9:16",
    style: dict | None = None,
    suffix: str = "",
) -> str:
    """Render a single clip. Returns the output file path."""
    if style is None:
        style = DEFAULT_STYLE

    res_x, res_y = FORMATS.get(fmt, (1080, 1920))
    output_dir = TEMP_DIR / job_id / f"clip_{clip_idx}"
    output_dir.mkdir(parents=True, exist_ok=True)

    width, height = _get_video_dimensions(video_path)
    duration = seg["end"] - seg["start"]

    words = _extract_words(seg["segments"], seg["start"])
    ass_path = output_dir / f"subs{suffix}.ass"
    ass_path.write_text(_build_ass(words, style, res_x, res_y), encoding="utf-8")

    output_path = output_dir / f"clip{suffix}.mp4"

    # Two-person split: only for 9:16 to keep 1:1 and 16:9 unaffected
    faces = None
    if fmt == "9:16":
        try:
            faces = _detect_two_persons(video_path, duration)
        except Exception:
            faces = None

    if faces:
        fc, map_args = _build_dual_filter_complex(faces, width, height, ass_path)
        cmd = [
            "ffmpeg", "-y",
            "-ss", str(seg["start"]),
            "-i", video_path,
            "-t", str(duration),
            "-filter_complex", fc,
            *map_args,
            "-c:v", "libx264", "-preset", "fast", "-crf", "23",
            "-c:a", "aac", "-b:a", "128k",
            "-movflags", "+faststart",
            str(output_path),
        ]
    else:
        crop = _crop_filter(width, height, fmt)
        vf = f"{crop},ass={ass_path}"
        cmd = [
            "ffmpeg", "-y",
            "-ss", str(seg["start"]),
            "-i", video_path,
            "-t", str(duration),
            "-vf", vf,
            "-c:v", "libx264", "-preset", "fast", "-crf", "23",
            "-c:a", "aac", "-b:a", "128k",
            "-movflags", "+faststart",
            str(output_path),
        ]

    subprocess.run(cmd, check=True, capture_output=True)
    return str(output_path)


def edit_clips(
    job_id: str,
    video_path: str,
    segments: list[dict],
    fmt: str = "9:16",
    style: dict | None = None,
) -> list[dict]:
    clips = []
    for idx, seg in enumerate(segments):
        file_path = render_clip(job_id, idx, video_path, seg, fmt=fmt, style=style)
        clips.append({
            "start": seg["start"],
            "end": seg["end"],
            "score": seg["score"],
            "title": seg["title"],
            "reason": seg.get("reason", ""),
            "file_path": file_path,
        })
    return clips


def edit_clips_from_url(
    job_id: str,
    url: str,
    segments: list[dict],
    fmt: str = "9:16",
    style: dict | None = None,
) -> list[dict]:
    """Download only the selected clip segments, render, then delete raw downloads."""
    from services.downloader import download_clip_segment

    clips = []
    for idx, seg in enumerate(segments):
        raw_path = download_clip_segment(job_id, url, idx, seg["start"], seg["end"])

        offset = seg["start"]
        local_seg = {
            **seg,
            "start": 0.0,
            "end": seg["end"] - offset,
            "segments": [
                {
                    **s,
                    "start": s["start"] - offset,
                    "end": s["end"] - offset,
                    "words": [
                        {**w, "start": w["start"] - offset, "end": w["end"] - offset}
                        for w in s.get("words", [])
                    ],
                }
                for s in seg["segments"]
            ],
        }

        file_path = render_clip(job_id, idx, raw_path, local_seg, fmt=fmt, style=style)
        Path(raw_path).unlink(missing_ok=True)

        clips.append({
            "start": seg["start"],
            "end": seg["end"],
            "score": seg["score"],
            "title": seg["title"],
            "reason": seg.get("reason", ""),
            "file_path": file_path,
        })
    return clips
