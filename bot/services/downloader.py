import asyncio
import os
import re
from typing import Dict, Any, Optional
import yt_dlp
import config

YTDL_AUDIO_OPTIONS = {
    "format": "bestaudio/best",
    "outtmpl": os.path.join(str(config.DOWNLOAD_DIR), "%(id)s.%(ext)s"),
    "geo_bypass": True,
    "nocheckcertificate": True,
    "quiet": True,
    "no_warnings": True,
    "postprocessors": [
        {
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }
    ],
}

YTDL_VIDEO_OPTIONS = {
    "format": "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
    "outtmpl": os.path.join(str(config.DOWNLOAD_DIR), "%(id)s.%(ext)s"),
    "merge_output_format": "mp4",
    "geo_bypass": True,
    "nocheckcertificate": True,
    "quiet": True,
    "no_warnings": True,
}

def _format_duration(seconds: Optional[int]) -> str:
    if not seconds:
        return "Live / Unknown"
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    if h > 0:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"

def _extract_and_download(query: str, is_video: bool = False) -> Dict[str, Any]:
    # Check if query is a direct URL or search term
    is_url = re.match(r"^https?://", query.strip())
    search_query = query.strip() if is_url else f"ytsearch1:{query.strip()}"

    ydl_opts = YTDL_VIDEO_OPTIONS if is_video else YTDL_AUDIO_OPTIONS

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(search_query, download=True)
        if "entries" in info:
            info = info["entries"][0]

        video_id = info.get("id")
        title = info.get("title", "Unknown Title")
        duration = info.get("duration", 0)
        webpage_url = info.get("webpage_url", query)
        thumbnail = info.get("thumbnail")
        uploader = info.get("uploader", "YouTube")

        if is_video:
            target_file = os.path.join(str(config.DOWNLOAD_DIR), f"{video_id}.mp4")
            if not os.path.exists(target_file):
                found = list(config.DOWNLOAD_DIR.glob(f"{video_id}.*"))
                target_file = str(found[0]) if found else target_file
        else:
            target_file = os.path.join(str(config.DOWNLOAD_DIR), f"{video_id}.mp3")
            if not os.path.exists(target_file):
                found = list(config.DOWNLOAD_DIR.glob(f"{video_id}.*"))
                target_file = str(found[0]) if found else target_file

        return {
            "id": video_id,
            "title": title,
            "duration": duration,
            "duration_str": _format_duration(duration),
            "file_path": str(target_file),
            "url": webpage_url,
            "thumbnail": thumbnail,
            "uploader": uploader,
            "is_video": is_video,
        }

async def search_and_download(query: str, is_video: bool = False) -> Dict[str, Any]:
    """Runs yt-dlp extraction and audio/video conversion in an async executor thread."""
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, _extract_and_download, query, is_video)
