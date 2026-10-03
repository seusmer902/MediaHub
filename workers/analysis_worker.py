from PySide6.QtCore import QObject, Signal, Slot

from services.ytopts import BOT_HINT
from services.analyzer import analyze, clean_error, fetch_thumbnail


class AnalysisWorker(QObject):
    analyzed = Signal(dict)
    thumbnail = Signal(bytes)
    failed = Signal(str)
    done = Signal()

    def __init__(self, url: str, playlist: bool, cookies_browser: str = ""):
        super().__init__()
        self.url = url
        self.playlist = playlist
        self.cookies_browser = cookies_browser

    @Slot()
    def run(self):
        try:
            result = analyze(self.url, self.playlist, self.cookies_browser)
            self.analyzed.emit(result)
            if result.get("thumbnail"):
                data = fetch_thumbnail(result["thumbnail"])
                if data:
                    self.thumbnail.emit(data)
        except Exception as e:
            msg = clean_error(e)
            if "not a bot" in msg or "Sign in to confirm" in msg:
                msg = BOT_HINT
            self.failed.emit(msg)
        finally:
            self.done.emit()
