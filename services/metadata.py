"""Extracción, limpieza y escritura de metadatos de audio."""
import re

import mutagen

FIELDS = ("title", "artist", "album", "genre", "year", "track")

_NOISE = re.compile(
    r"\s*[\(\[]\s*(official|oficial|lyrics?|letra|audio|video|vídeo|music video|"
    r"visuali[sz]er|hd|4k|remaster)[^\)\]]*[\)\]]",
    re.IGNORECASE,
)
_ARTIST_SUFFIX = re.compile(r"\s*(-\s*topic|vevo)\s*$", re.IGNORECASE)


def blank_metadata() -> dict:
    return {k: "" for k in FIELDS}


def clean_title(text: str) -> str:
    text = _NOISE.sub("", text or "")
    return re.sub(r"\s{2,}", " ", text).strip(" -–|")


def clean_artist(text: str) -> str:
    return _ARTIST_SUFFIX.sub("", text or "").strip()


def is_music(info: dict, url: str = "") -> bool:
    if info.get("track") or info.get("artist") or info.get("artists") or info.get("album"):
        return True
    if any("music" in str(c).lower() for c in (info.get("categories") or [])):
        return True
    return "music.youtube" in (url or info.get("webpage_url") or "")


def extract_metadata(info: dict) -> dict:
    """Convierte la info de yt-dlp en etiquetas de canción."""
    meta = blank_metadata()

    track = info.get("track")
    artist = info.get("artist") or ", ".join(info.get("artists") or [])
    title = track or info.get("title") or ""

    # "Artista - Canción" en el título cuando no hay etiquetas reales
    if not track and not artist and " - " in title:
        artist, title = (p.strip() for p in title.split(" - ", 1))

    if not artist:
        artist = info.get("channel") or info.get("uploader") or info.get("creator") or ""

    meta["title"] = clean_title(title)
    meta["artist"] = clean_artist(artist)
    meta["album"] = info.get("album") or ""
    meta["genre"] = info.get("genre") or ""

    year = info.get("release_year")
    if not year:
        date = str(info.get("release_date") or info.get("upload_date") or "")
        year = date[:4] if len(date) >= 4 else ""
    meta["year"] = str(year or "")

    if info.get("track_number"):
        meta["track"] = str(info["track_number"])
    return meta


def format_duration(seconds) -> str:
    if not seconds:
        return ""
    minutes, secs = divmod(int(seconds), 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours}:{minutes:02d}:{secs:02d}" if hours else f"{minutes}:{secs:02d}"


def apply_tags(path, meta: dict) -> bool:
    """Escribe etiquetas en un MP3/M4A sin tocar la portada incrustada."""
    audio = mutagen.File(str(path), easy=True)
    if audio is None:
        return False
    if audio.tags is None:
        audio.add_tags()

    mapping = {
        "title": "title",
        "artist": "artist",
        "album": "album",
        "genre": "genre",
        "year": "date",
        "track": "tracknumber",
    }
    for key, tag in mapping.items():
        value = (meta.get(key) or "").strip()
        if value:
            audio[tag] = value

    artist = (meta.get("artist") or "").strip()
    if artist:
        audio["albumartist"] = artist

    audio.save()
    return True
