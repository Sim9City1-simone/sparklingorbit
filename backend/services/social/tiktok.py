import requests
from config import TIKTOK_ACCESS_TOKEN


def upload_to_tiktok(file_path: str, title: str) -> dict:
    """
    Uses TikTok Content Posting API (Direct Post).
    Docs: https://developers.tiktok.com/doc/content-posting-api-reference-direct-post
    """
    # Step 1: Init upload
    init_resp = requests.post(
        "https://open.tiktokapis.com/v2/post/publish/video/init/",
        headers={
            "Authorization": f"Bearer {TIKTOK_ACCESS_TOKEN}",
            "Content-Type": "application/json; charset=UTF-8",
        },
        json={
            "post_info": {
                "title": title,
                "privacy_level": "PUBLIC_TO_EVERYONE",
                "disable_duet": False,
                "disable_comment": False,
                "disable_stitch": False,
            },
            "source_info": {
                "source": "FILE_UPLOAD",
                "video_size": _get_file_size(file_path),
                "chunk_size": _get_file_size(file_path),
                "total_chunk_count": 1,
            },
        },
    )
    init_resp.raise_for_status()
    data = init_resp.json()["data"]
    publish_id = data["publish_id"]
    upload_url = data["upload_url"]

    # Step 2: Upload video
    with open(file_path, "rb") as f:
        video_bytes = f.read()

    upload_resp = requests.put(
        upload_url,
        headers={
            "Content-Type": "video/mp4",
            "Content-Range": f"bytes 0-{len(video_bytes) - 1}/{len(video_bytes)}",
        },
        data=video_bytes,
    )
    upload_resp.raise_for_status()

    return {
        "platform": "tiktok",
        "publish_id": publish_id,
    }


def _get_file_size(file_path: str) -> int:
    import os
    return os.path.getsize(file_path)
