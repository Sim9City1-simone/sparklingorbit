import requests
from config import INSTAGRAM_ACCESS_TOKEN, INSTAGRAM_USER_ID, BACKEND_URL


def upload_to_instagram(file_path: str, caption: str) -> dict:
    """
    Uses Instagram Graph API to upload a Reel.
    Requires the video to be accessible via a public URL.
    The backend serves clips via /clips/{path}, so we build the URL from BACKEND_URL.
    """
    from pathlib import Path
    from config import TEMP_DIR

    relative = Path(file_path).relative_to(TEMP_DIR)
    video_url = f"{BACKEND_URL}/clips/{relative}"

    # Step 1: Create media container
    container_resp = requests.post(
        f"https://graph.facebook.com/v19.0/{INSTAGRAM_USER_ID}/media",
        params={
            "media_type": "REELS",
            "video_url": video_url,
            "caption": caption,
            "share_to_feed": "true",
            "access_token": INSTAGRAM_ACCESS_TOKEN,
        },
    )
    container_resp.raise_for_status()
    container_id = container_resp.json()["id"]

    # Step 2: Poll until ready
    import time
    for _ in range(30):
        status_resp = requests.get(
            f"https://graph.facebook.com/v19.0/{container_id}",
            params={"fields": "status_code", "access_token": INSTAGRAM_ACCESS_TOKEN},
        )
        status = status_resp.json().get("status_code")
        if status == "FINISHED":
            break
        if status == "ERROR":
            raise RuntimeError("Instagram media processing failed")
        time.sleep(5)
    else:
        raise RuntimeError("Instagram media processing timed out")

    # Step 3: Publish
    publish_resp = requests.post(
        f"https://graph.facebook.com/v19.0/{INSTAGRAM_USER_ID}/media_publish",
        params={
            "creation_id": container_id,
            "access_token": INSTAGRAM_ACCESS_TOKEN,
        },
    )
    publish_resp.raise_for_status()
    media_id = publish_resp.json()["id"]

    return {
        "platform": "instagram",
        "media_id": media_id,
        "url": f"https://www.instagram.com/reels/{media_id}/",
    }
