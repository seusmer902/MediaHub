"""Análisis de enlaces con yt-dlp (sin descargar)."""
import re

import requests
import yt_dlp

from .metadata import blank_metadata, clean_artist, extract_metadata, is_music
from .platform import detect_platform
from .ytopts import common_opts

_ANSI = re.compile(r"\x1b\[[0-9;]*m")


def clean_error(exc) -> str:
    text = _ANSI.sub("", str(exc)).strip()
    text = re.sub(r"^ERROR:\s*", "", text)
    return text or exc.__class__.__name__


def _pick_thumbnail(info: dict):
    if info.get("thumbnail"):
        return info["thumbnail"]
    for t in reversed(info.get("thumbnails") or []):
        if t.get("url"):
            return t["url"]
    for entry in info.get("entries") or []:
        if entry:
            found = _pick_thumbnail(entry)
            if found:
                return found
    return None


def fetch_thumbnail(url: str):
    try:
        r = requests.get(url, timeout=15)
        return r.content if r.ok else None
    except Exception:
        return None


def analyze(url: str, playlist: bool, cookies_browser: str = "") -> dict:
    opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "noplaylist": not playlist,
        "extract_flat": "in_playlist",
        "socket_timeout": 20,
        **common_opts(cookies_browser),
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.sanitize_info(ydl.extract_info(url, download=False))

    kind = "playlist" if info.get("_type") == "playlist" else "video"
    entries = [e for e in (info.get("entries") or []) if e]
    uploader = clean_artist(info.get("channel") or info.get("uploader") or info.get("creator") or "")

    if kind == "playlist":
        meta = blank_metadata()
        meta["album"] = info.get("title") or ""
        meta["artist"] = uploader
        music = "music.youtube" in url or any(e.get("artist") or e.get("track") for e in entries)
    else:
        meta = extract_metadata(info)
        music = is_music(info, url)

    return {
        "kind": kind,
        "url": url,
        "platform": detect_platform(url),
        "title": info.get("title") or "Sin título",
        "uploader": uploader,
        "duration": info.get("duration"),
        "thumbnail": _pick_thumbnail(info),
        "is_music": music,
        "metadata": meta,
        "count": len(entries),
        "entries": [
            {"title": e.get("title") or "Sin título", "duration": e.get("duration")}
            for e in entries[:50]
        ],
    }
