"""Descarga con yt-dlp: audio (con etiquetas y portada) y video."""
from dataclasses import dataclass, field
from pathlib import Path

import imageio_ffmpeg
import yt_dlp
from yt_dlp.utils import sanitize_filename

from config import AUDIO_FORMATS
from .analyzer import clean_error
from .metadata import apply_tags
from .ytopts import BOT_HINT, common_opts


@dataclass
class DownloadRequest:
    url: str
    title: str
    mode: str                      # "video" | "audio"
    quality: str
    audio_format: str
    folder: str
    metadata: dict = field(default_factory=dict)
    playlist: bool = False
    platform: str = ""
    remove_watermark: bool = False
    cookies_browser: str = ""


class DownloadCancelled(Exception):
    pass


class _Logger:
    def __init__(self, callback):
        self.cb = callback

    def debug(self, msg):
        if msg.startswith(("[debug]", "[download]")):
            return
        self.cb(msg)

    def info(self, msg):
        self.cb(msg)

    def warning(self, msg):
        self.cb("⚠ " + clean_error(msg))

    def error(self, msg):
        self.cb("✖ " + clean_error(msg))


def video_format(quality: str, remove_watermark: bool) -> str:
    wm = "[format_id!=download]" if remove_watermark else ""   # TikTok: formato "download" lleva marca
    h = "" if quality == "Mejor disponible" else f"[height<={quality.replace('p', '')}]"
    return f"bestvideo*{h}{wm}+bestaudio/best{h}{wm}"


def _build_options(req: DownloadRequest, hooks: dict) -> dict:
    folder = Path(req.folder).expanduser()
    if req.playlist:
        template = str(folder / "%(playlist_title|Playlist)s" / "%(playlist_index)02d - %(title)s.%(ext)s")
    else:
        template = str(folder / "%(title)s.%(ext)s")

    opts = {
        "outtmpl": template,
        "noplaylist": not req.playlist,
        "ffmpeg_location": imageio_ffmpeg.get_ffmpeg_exe(),
        "progress_hooks": [hooks["progress"]],
        "post_hooks": [hooks["post"]],
        "logger": hooks["logger"],
        "quiet": True,
        "no_warnings": True,
        "windowsfilenames": True,
        "retries": 5,
        "fragment_retries": 5,
        "concurrent_fragment_downloads": 4,
        "ignoreerrors": "only_download" if req.playlist else False,
        **common_opts(req.cookies_browser),
    }

    if req.mode == "audio":
        codec, quality = AUDIO_FORMATS.get(req.audio_format, ("mp3", "320"))
        opts.update({
            "format": "bestaudio/best",
            "writethumbnail": True,
            "postprocessors": [
                {"key": "FFmpegExtractAudio", "preferredcodec": codec, "preferredquality": quality},
                {"key": "FFmpegThumbnailsConvertor", "format": "jpg", "when": "before_dl"},
                {"key": "FFmpegMetadata", "add_metadata": True},
                {"key": "EmbedThumbnail"},
            ],
        })
    else:
        opts.update({
            "format": video_format(req.quality, req.remove_watermark),
            "merge_output_format": "mp4",
        })
    return opts


def download(req: DownloadRequest, on_progress, on_message, is_cancelled) -> list:
    """Descarga y devuelve la lista de archivos finales."""
    files: list = []
    last = {"pct": 0.0}
    errors: list = []

    def message(text):
        if text.startswith("✖"):
            errors.append(text)
        on_message(text)

    def progress_hook(d):
        if is_cancelled():
            raise DownloadCancelled()
        status = d.get("status")
        if status == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate")
            frac = (d.get("downloaded_bytes") or 0) / total if total else 0
            info = d.get("info_dict") or {}
            idx, n = info.get("playlist_index"), info.get("n_entries")
            if req.playlist and idx and n:
                pct, prefix = ((idx - 1) + frac) / n * 100, f"{idx}/{n}  ·  "
            else:
                pct, prefix = frac * 100, ""
            last["pct"] = pct
            parts = []
            if d.get("speed"):
                parts.append(f"{d['speed'] / 1024 / 1024:.2f} MB/s")
            if d.get("eta") is not None:
                parts.append(f"ETA {int(d['eta'])}s")
            on_progress(pct, prefix + "  ·  ".join(parts) if parts else prefix + "Descargando...")
        elif status == "finished":
            on_progress(last["pct"], "Procesando archivo...")

    def post_hook(filename):
        path = Path(filename)
        if req.mode == "audio":
            path = _tag_audio(path, req, on_message)
        files.append(str(path))

    opts = _build_options(req, {
        "progress": progress_hook,
        "post": post_hook,
        "logger": _Logger(message),
    })

    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([req.url])
    except DownloadCancelled:
        raise
    except Exception:
        if is_cancelled():
            raise DownloadCancelled()
        raise

    if is_cancelled():
        raise DownloadCancelled()
    if not files:
        if any("not a bot" in e or "Sign in to confirm" in e for e in errors):
            raise RuntimeError(BOT_HINT)
        raise RuntimeError("No se pudo descargar ningún archivo. Revisa el registro de arriba.")
    return files


def _tag_audio(path: Path, req: DownloadRequest, on_message) -> Path:
    meta = {k: v for k, v in req.metadata.items() if v}
    if req.playlist:
        meta.pop("title", None)
        meta.pop("track", None)
    if not meta:
        return path
    try:
        if not apply_tags(path, meta):
            return path
        if not req.playlist and meta.get("title"):
            base = f"{meta['artist']} - {meta['title']}" if meta.get("artist") else meta["title"]
            target = path.with_name(sanitize_filename(base) + path.suffix)
            if target != path and not target.exists():
                path.rename(target)
                path = target
    except Exception as e:
        on_message(f"⚠ No se pudieron aplicar las etiquetas: {e}")
    return path
