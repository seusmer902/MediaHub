"""Ventana principal: navegación, hilos y conexión entre UI, workers e historial."""
from pathlib import Path

from PySide6.QtCore import QThread
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QFrame, QStackedWidget,
    QButtonGroup, QMessageBox,
)

from config import APP_NAME, VERSION
from services import history
from workers.analysis_worker import AnalysisWorker
from workers.download_worker import DownloadWorker
from .pages import DownloaderPage, HistoryPage
from .widgets import NavButton, make_label, open_path


class MainWindow(QMainWindow):
    NAV = [
        ("⌂   Descargador", "home"),
        ("♫   Audio", "audio"),
        ("▣   Video", "video"),
        ("▤   Playlists", "playlist"),
        ("◷   Historial", "history"),
    ]

    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} — Multimedia Downloader")
        self.resize(1180, 780)
        self.setMinimumSize(1000, 650)

        self._threads: set = set()
        self._analysis_worker = None
        self._download_worker = None
        self._current_request = None

        root = QWidget()
        root.setObjectName("root")
        self.setCentralWidget(root)
        layout = QHBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        layout.addWidget(self._build_sidebar())

        self.stack = QStackedWidget()
        self.downloader = DownloaderPage()
        self.history_page = HistoryPage()
        self.stack.addWidget(self.downloader)
        self.stack.addWidget(self.history_page)
        layout.addWidget(self.stack, 1)

        self.downloader.analyze_requested.connect(self._start_analysis)
        self.downloader.download_requested.connect(self._start_download)
        self.downloader.cancel_requested.connect(self._cancel_download)
        self.history_page.reuse_requested.connect(self._reuse_url)

        self._nav_buttons["home"].setChecked(True)

    # ---------------------------------------------------- sidebar
    def _build_sidebar(self) -> QFrame:
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(235)
        lay = QVBoxLayout(sidebar)
        lay.setContentsMargins(18, 28, 14, 22)
        lay.setSpacing(6)

        lay.addWidget(make_label('Media<font color="#BF40FA">Hub</font>', "brand"))
        lay.addWidget(make_label("MULTIMEDIA WORKSPACE", "sidebarSubtitle"))
        lay.addSpacing(24)

        self._nav_group = QButtonGroup(self)
        self._nav_group.setExclusive(True)
        self._nav_buttons = {}
        for text, key in self.NAV:
            btn = NavButton(text)
            btn.clicked.connect(lambda _=False, k=key: self._navigate(k))
            self._nav_group.addButton(btn)
            self._nav_buttons[key] = btn
            lay.addWidget(btn)

        lay.addStretch()
        lay.addWidget(make_label(f"{APP_NAME} {VERSION}\nPython • PySide6 • yt-dlp", "hint"))
        return sidebar

    def _navigate(self, key: str):
        if key == "history":
            self.history_page.refresh()
            self.stack.setCurrentWidget(self.history_page)
        else:
            self.downloader.apply_preset(key)
            self.stack.setCurrentWidget(self.downloader)

    def _reuse_url(self, url: str):
        self._nav_buttons["home"].setChecked(True)
        self._navigate("home")
        self.downloader.set_url(url)

    # ---------------------------------------------------- hilos
    def _start_thread(self, worker):
        self._threads = {t for t in self._threads if t.isRunning()}
        thread = QThread()
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.done.connect(thread.quit)
        thread.finished.connect(worker.deleteLater)
        self._threads.add(thread)
        thread.start()

    def _start_analysis(self, url: str, playlist: bool, cookies: str):
        worker = AnalysisWorker(url, playlist, cookies)
        worker.analyzed.connect(self.downloader.show_analysis)
        worker.thumbnail.connect(self.downloader.show_thumbnail)
        worker.failed.connect(self.downloader.analysis_failed)
        worker.done.connect(self.downloader.analysis_finished)
        self._analysis_worker = worker
        self._start_thread(worker)

    def _start_download(self, request):
        worker = DownloadWorker(request)
        worker.progress.connect(self.downloader.set_progress)
        worker.message.connect(self.downloader.log)
        worker.completed.connect(self._download_completed)
        worker.failed.connect(self.downloader.download_failed)
        worker.cancelled.connect(self.downloader.download_cancelled)
        worker.done.connect(self.downloader.download_finished)
        self._download_worker = worker
        self._current_request = request
        self._start_thread(worker)

    def _cancel_download(self):
        if self._download_worker is not None:
            try:
                self._download_worker.cancel()
            except RuntimeError:
                pass

    def _download_completed(self, files: list):
        req = self._current_request
        folder = Path(files[0]).parent if files else Path(req.folder)
        history.add(
            title=req.title, url=req.url, platform=req.platform, mode=req.mode,
            folder=str(folder), count=len(files),
        )
        self.downloader.download_completed(files)

        box = QMessageBox(self)
        box.setWindowTitle(APP_NAME)
        box.setIcon(QMessageBox.Icon.Information)
        box.setText("Descarga completada")
        box.setInformativeText(f"{len(files)} archivo(s) guardados en:\n{folder}")
        open_btn = box.addButton("Abrir carpeta", QMessageBox.ButtonRole.AcceptRole)
        box.addButton("Cerrar", QMessageBox.ButtonRole.RejectRole)
        box.exec()
        if box.clickedButton() is open_btn:
            open_path(folder)

    # ---------------------------------------------------- cierre
    def closeEvent(self, event):
        running = any(t.isRunning() for t in self._threads)
        if self.downloader._downloading:
            ans = QMessageBox.question(self, APP_NAME, "Hay una descarga en curso. ¿Cancelar y salir?")
            if ans != QMessageBox.StandardButton.Yes:
                event.ignore()
                return
            self._cancel_download()
        if running:
            for t in list(self._threads):
                t.quit()
                t.wait(5000)
        event.accept()
