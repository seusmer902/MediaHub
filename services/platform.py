"""Detección de plataforma y tipo de enlace."""
from urllib.parse import urlparse, parse_qs

_PLATFORMS = [
    ("YouTube", ("youtube.com", "youtu.be", "youtube-nocookie.com")),
    ("TikTok", ("tiktok.com",)),
    ("Instagram", ("instagram.com",)),
    ("Facebook", ("facebook.com", "fb.watch")),
    ("X / Twitter", ("twitter.com", "x.com")),
    ("Vimeo", ("vimeo.com",)),
    ("SoundCloud", ("soundcloud.com",)),
    ("Twitch", ("twitch.tv",)),
    ("Reddit", ("reddit.com", "redd.it")),
]

# Plataformas donde existe un formato "con marca" que se puede evitar.
WATERMARK_PLATFORMS = {"TikTok"}


def is_url(text: str) -> bool:
    return text.startswith(("http://", "https://")) and "." in text


def _host(url: str) -> str:
    return urlparse(url).netloc.lower().split(":")[0]


def detect_platform(url: str) -> str:
    host = _host(url)
    for name, domains in _PLATFORMS:
        if any(host == d or host.endswith("." + d) for d in domains):
            return name
    return "Web / Otra"


def is_playlist_url(url: str) -> bool:
    """Enlace que es SOLO una playlist (no un video suelto)."""
    parsed = urlparse(url)
    return parsed.path.lower().rstrip("/") == "/playlist" or "/sets/" in parsed.path.lower()


def has_playlist_param(url: str) -> bool:
    """Video que además viene dentro de una playlist (watch?v=..&list=..)."""
    return "list" in parse_qs(urlparse(url).query) and not is_playlist_url(url)


def supports_watermark_removal(platform: str) -> bool:
    return platform in WATERMARK_PLATFORMS
