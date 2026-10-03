from PySide6.QtCore import QObject, Signal, Slot

from services.analyzer import clean_error
from services.downloader import DownloadCancelled, DownloadRequest, download


class DownloadWorker(QObject):
    progress = Signal(float, str)
    message = Signal(str)
    completed = Signal(list)
    failed = Signal(str)
    cancelled = Signal()
    done = Signal()

    def __init__(self, request: DownloadRequest):
        super().__init__()
        self.request = request
        self._cancel = False

    def cancel(self):
        self._cancel = True

    @Slot()
    def run(self):
        try:
            self.message.emit("Iniciando descarga...")
            files = download(
                self.request,
                on_progress=self.progress.emit,
                on_message=self.message.emit,
                is_cancelled=lambda: self._cancel,
            )
            self.progress.emit(100, "Completado")
            self.completed.emit(files)
        except DownloadCancelled:
            self.cancelled.emit()
        except Exception as e:
            self.failed.emit(clean_error(e))
        finally:
            self.done.emit()
