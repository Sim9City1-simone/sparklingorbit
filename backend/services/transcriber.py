import mlx_whisper
from config import WHISPER_MODEL

_MLX_MODELS = {
    "tiny":   "mlx-community/whisper-tiny-mlx",
    "base":   "mlx-community/whisper-base-mlx",
    "small":  "mlx-community/whisper-small-mlx",
    "medium": "mlx-community/whisper-medium-mlx",
    "large":  "mlx-community/whisper-large-v3-mlx",
}


def transcribe(video_path: str) -> dict:
    """
    Returns Whisper result dict with 'segments' list.
    Each segment: {id, start, end, text}
    Uses MLX for GPU acceleration on Apple Silicon.
    """
    model_repo = _MLX_MODELS.get(WHISPER_MODEL, _MLX_MODELS["base"])
    result = mlx_whisper.transcribe(
        video_path,
        path_or_hf_repo=model_repo,
        word_timestamps=True,
        verbose=False,
    )
    return result
