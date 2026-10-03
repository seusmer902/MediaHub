"""Páginas: Descargador e Historial."""
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLineEdit, QComboBox, QCheckBox,
    QProgressBar, QFileDialog, QMessageBox, QFrame, QTextEdit, QScrollArea, QApplication,
)

from config import AUDIO_FORMATS, BROWSERS, COLORS, DEFAULT_DOWNLOAD_DIR, QUALITIES
from services import history
from services.downloader import DownloadRequest
from services.metadata import format_duration
from services.platform import (
    detect_platform, has_playlist_param, is_playlist_url, is_url, supports_watermark_removal,
)
from .widgets import (
    Card, HistoryRow, SegmentedControl, ThumbnailView, make_button, make_label, open_path,
)

META_FIELDS = [
    ("title", "Título"), ("artist", "Artista / cantante"), ("album", "Álbum"),
    ("genre", "Género"), ("year", "Año"), ("track", "N.º de pista"),
]


def _scroll_page():
    """Devuelve (widget raíz, layout interior) con scroll vertical."""
    root = QWidget()
    outer = QVBoxLayout(root)
    outer.setContentsMargins(0, 0, 0, 0)
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setFrameShape(QFrame.Shape.NoFrame)
    outer.addWidget(scroll)
    page = QWidget()
    lay = QVBoxLayout(page)
    lay.setContentsMargins(32, 28, 32, 28)
    lay.setSpacing(18)
    scroll.setWidget(page)
    return root, lay


# ============================================================
# DESCARGADOR
# ============================================================
class DownloaderPage(QWidget):
    analyze_requested = Signal(str, bool, str)
    download_requested = Signal(object)
    cancel_requested = Signal()

    PRESETS = {
        "home": ("Descarga tu contenido", "Pega un enlace y MediaHub se encarga del resto.", None, None),
        "audio": ("Descarga música", "Canciones con portada y etiquetas editables.", "audio", None),
        "video": ("Descarga videos", "Elige calidad y carpeta. TikTok sin marca de agua.", "video", None),
        "playlist": ("Playlists completas", "Pega el enlace de una playlist y baja todo de una vez.", None, True),
    }

    def __init__(self):
        super().__init__()
        self.analysis = None
        self._analyzing = False
        self._downloading = False
        self._build()
        self._on_mode_changed("video")
        self.apply_preset("home")

    # ---------------------------------------------------- construcción
    def _build(self):
        root, lay = _scroll_page()
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(root)

        # Header
        header = QHBoxLayout()
        col = QVBoxLayout()
        self.title = make_label("", "title")
        self.subtitle = make_label("", "subtitle")
        col.addWidget(self.title)
        col.addWidget(self.subtitle)
        header.addLayout(col)
        header.addStretch()
        self.badge = make_label("LISTO", "badge")
        header.addWidget(self.badge)
        lay.addLayout(header)

        # Enlace
        url_card = Card("ENLACE")
        row = QHBoxLayout()
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://www.youtube.com/watch?v=...")
        self.url_input.returnPressed.connect(self._on_analyze_clicked)
        self.url_input.textChanged.connect(self._on_url_changed)
        self.paste_btn = make_button("Pegar")
        self.paste_btn.clicked.connect(self._on_paste)
        self.analyze_btn = make_button("Analizar", "analyze")
        self.analyze_btn.clicked.connect(self._on_analyze_clicked)
        row.addWidget(self.url_input, 1)
        row.addWidget(self.paste_btn)
        row.addWidget(self.analyze_btn)
        url_card.body.addLayout(row)
        self.status = make_label("Esperando un enlace...", "hint", True)
        url_card.body.addWidget(self.status)
        lay.addWidget(url_card)

        # Vista previa
        preview = Card(margins=(20, 20, 20, 20))
        prow = QHBoxLayout()
        prow.setSpacing(18)
        self.thumb = ThumbnailView()
        prow.addWidget(self.thumb)
        pcol = QVBoxLayout()
        self.media_title = make_label("Sin analizar", "section", True)
        self.media_info = make_label("Título, autor y duración aparecerán aquí.", "hint", True)
        chips = QHBoxLayout()
        self.chip_platform = make_label("", "chip")
        self.chip_kind = make_label("", "chip")
        self.chip_music = make_label("♫ Música detectada", "chip")
        for c in (self.chip_platform, self.chip_kind, self.chip_music):
            c.hide()
            chips.addWidget(c)
        chips.addStretch()
        self.entries_label = make_label("", "hint", True)
        self.entries_label.hide()
        pcol.addWidget(self.media_title)
        pcol.addWidget(self.media_info)
        pcol.addLayout(chips)
        pcol.addWidget(self.entries_label)
        pcol.addStretch()
        prow.addLayout(pcol, 1)
        preview.body.addLayout(prow)
        lay.addWidget(preview)

        # Opciones
        opts = Card("OPCIONES DE DESCARGA")
        grid = QGridLayout()
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(12)
        grid.setColumnStretch(1, 1)

        grid.addWidget(make_label("Formato", "field"), 0, 0)
        self.mode = SegmentedControl([("video", "▣  Video"), ("audio", "♫  Audio")])
        self.mode.changed.connect(self._on_mode_changed)
        grid.addWidget(self.mode, 0, 1, 1, 2)

        self.quality_label = make_label("Calidad", "field")
        grid.addWidget(self.quality_label, 1, 0)
        self.video_combo = QComboBox()
        self.video_combo.addItems(QUALITIES)
        self.audio_combo = QComboBox()
        self.audio_combo.addItems(list(AUDIO_FORMATS))
        grid.addWidget(self.video_combo, 1, 1, 1, 2)
        grid.addWidget(self.audio_combo, 1, 1, 1, 2)

        checks = QHBoxLayout()
        self.check_playlist = QCheckBox("Playlist completa")
        self.check_playlist.toggled.connect(self._on_playlist_toggled)
        self.check_wm = QCheckBox("Quitar marca de agua")
        self.check_wm.setToolTip("Disponible para TikTok. Instagram, YouTube y otros ya se descargan sin marca.")
        checks.addWidget(self.check_playlist)
        checks.addSpacing(20)
        checks.addWidget(self.check_wm)
        checks.addStretch()
        grid.addLayout(checks, 2, 1, 1, 2)

        grid.addWidget(make_label("Carpeta", "field"), 3, 0)
        self.folder_input = QLineEdit(str(DEFAULT_DOWNLOAD_DIR))
        browse = make_button("Examinar")
        browse.clicked.connect(self._pick_folder)
        grid.addWidget(self.folder_input, 3, 1)
        grid.addWidget(browse, 3, 2)
        cookies_label = make_label("Cookies", "field")
        cookies_label.setToolTip("Si YouTube dice «confirma que no eres un bot», elige el navegador con tu sesión iniciada.")
        self.cookies_combo = QComboBox()
        self.cookies_combo.addItems(BROWSERS)
        self.cookies_combo.setToolTip(cookies_label.toolTip())
        grid.addWidget(cookies_label, 4, 0)
        grid.addWidget(self.cookies_combo, 4, 1, 1, 2)
        opts.body.addLayout(grid)
        lay.addWidget(opts)

        # Metadatos
        self.meta_card = Card(
            "METADATOS DEL AUDIO",
            "Se detectan automáticamente. Puedes corregirlos antes de descargar.",
        )
        mgrid = QGridLayout()
        mgrid.setHorizontalSpacing(12)
        mgrid.setVerticalSpacing(10)
        mgrid.setColumnStretch(1, 1)
        mgrid.setColumnStretch(3, 1)
        self.meta = {}
        for i, (key, name) in enumerate(META_FIELDS):
            edit = QLineEdit()
            self.meta[key] = edit
            r, c = i // 2, (i % 2) * 2
            mgrid.addWidget(make_label(name, "field"), r, c)
            mgrid.addWidget(edit, r, c + 1)
        self.meta_card.body.addLayout(mgrid)
        self.meta_hint = make_label("", "hint", True)
        self.meta_hint.hide()
        self.meta_card.body.addWidget(self.meta_hint)
        lay.addWidget(self.meta_card)

        # Progreso
        prog = Card()
        srow = QHBoxLayout()
        self.progress_status = make_label("Preparado", "hint")
        self.progress_pct = make_label("0%", "hint")
        srow.addWidget(self.progress_status)
        srow.addStretch()
        srow.addWidget(self.progress_pct)
        prog.body.addLayout(srow)
        self.bar = QProgressBar()
        self.bar.setRange(0, 100)
        self.bar.setTextVisible(False)
        prog.body.addWidget(self.bar)
        self.console = QTextEdit()
        self.console.setObjectName("console")
        self.console.setReadOnly(True)
        self.console.setFixedHeight(96)
        prog.body.addWidget(self.console)
        lay.addWidget(prog)

        # Acciones
        actions = QHBoxLayout()
        actions.addWidget(make_label("Usa contenido que tengas derecho a descargar.", "hint"))
        actions.addStretch()
        self.cancel_btn = make_button("Cancelar", "danger")
        self.cancel_btn.clicked.connect(self._on_cancel)
        self.cancel_btn.hide()
        self.download_btn = make_button("⬇  Descargar", "primary")
        self.download_btn.setMinimumWidth(190)
        self.download_btn.clicked.connect(self._on_download_clicked)
        actions.addWidget(self.cancel_btn)
        actions.addWidget(self.download_btn)
        lay.addLayout(actions)
        lay.addStretch()

    # ---------------------------------------------------- API pública
    def apply_preset(self, key: str):
        title, sub, mode, playlist = self.PRESETS[key]
        self.title.setText(title)
        self.subtitle.setText(sub)
        if mode:
            self.mode.set_value(mode)
        if playlist is not None:
            self.check_playlist.setChecked(playlist)

    def set_url(self, url: str):
        self.url_input.setText(url)

    def show_analysis(self, a: dict):
        self.analysis = a
        is_pl = a["kind"] == "playlist"

        self.media_title.setText(a["title"])
        second = f"{a['count']} elementos" if is_pl else (format_duration(a["duration"]) or "Duración desconocida")
        self.media_info.setText("  •  ".join([a["uploader"] or "Autor desconocido", second]))

        self.chip_platform.setText(a["platform"])
        self.chip_kind.setText("Playlist" if is_pl else "Individual")
        self.chip_music.setVisible(a["is_music"])
        self.chip_platform.show()
        self.chip_kind.show()

        if is_pl:
            if not self.check_playlist.isChecked():
                self.check_playlist.setChecked(True)
            lines = [f"{i}. {e['title']}" for i, e in enumerate(a["entries"][:4], 1)]
            if a["count"] > 4:
                lines.append(f"… y {a['count'] - 4} más")
            self.entries_label.setText("\n".join(lines))
            self.entries_label.show()
        else:
            self.entries_label.hide()

        # metadatos
        for key, edit in self.meta.items():
            edit.setText(a["metadata"].get(key, ""))
        self.meta["title"].setEnabled(not is_pl)
        self.meta["track"].setEnabled(not is_pl)
        self.meta["title"].setPlaceholderText("Se toma de cada canción" if is_pl else "")
        self.meta_hint.setVisible(is_pl)
        self.meta_hint.setText("En playlists, artista/álbum/género/año se aplican a todas las pistas "
                               "(déjalos vacíos para conservar los de cada canción).")

        msg = "✓ Información detectada correctamente."
        if a["is_music"] and self.mode.value() != "audio":
            self.mode.set_value("audio")
            msg += " Parece música: activé el modo Audio."
        self._set_status(msg, COLORS["ok"])

    def show_thumbnail(self, data: bytes):
        self.thumb.set_image(data)

    def analysis_failed(self, message: str):
        self._set_status("No se pudo analizar el enlace.", COLORS["err"])
        self.log(f"✖ {message}")

    def analysis_finished(self):
        self._analyzing = False
        self._refresh_buttons()

    def set_progress(self, pct: float, text: str):
        pct = max(0, min(100, int(pct)))
        self.bar.setValue(pct)
        self.progress_pct.setText(f"{pct}%")
        self.progress_status.setText(text or "Procesando...")

    def log(self, message: str):
        self.console.append(message)

    def download_completed(self, files: list):
        self.set_progress(100, "Completado ✓")

    def download_failed(self, message: str):
        self.progress_status.setText("Error")
        self.log(f"✖ {message}")
        QMessageBox.critical(self, "MediaHub", f"No se pudo completar la descarga:\n\n{message}")

    def download_cancelled(self):
        self.progress_status.setText("Descarga cancelada")
        self.log("Descarga cancelada por el usuario.")

    def download_finished(self):
        self._downloading = False
        self._refresh_buttons()

    # ---------------------------------------------------- eventos internos
    def _set_status(self, text: str, color: str = None):
        self.status.setText(text)
        self.status.setStyleSheet(f"color: {color or COLORS['muted']};")

    def _refresh_buttons(self):
        idle = not self._analyzing and not self._downloading
        self.analyze_btn.setEnabled(idle)
        self.download_btn.setEnabled(idle)
        self.cancel_btn.setVisible(self._downloading)
        self.cancel_btn.setEnabled(True)

    def _reset_analysis(self):
        self.analysis = None
        self.thumb.reset()
        self.media_title.setText("Sin analizar")
        self.media_info.setText("Título, autor y duración aparecerán aquí.")
        for c in (self.chip_platform, self.chip_kind, self.chip_music, self.entries_label, self.meta_hint):
            c.hide()
        for edit in self.meta.values():
            edit.clear()
            edit.setEnabled(True)

    def _on_url_changed(self, text: str):
        text = text.strip()
        platform = detect_platform(text) if text else None
        self.badge.setText(platform.upper() if platform else "LISTO")
        if self.analysis:
            self._reset_analysis()

        wm = bool(platform) and supports_watermark_removal(platform)
        self.check_wm.setEnabled(wm)
        self.check_wm.setChecked(wm)

        if is_playlist_url(text):
            self.check_playlist.setChecked(True)
        if not text:
            self._set_status("Esperando un enlace...")
        elif has_playlist_param(text) and not self.check_playlist.isChecked():
            self._set_status("Este video pertenece a una playlist. Marca «Playlist completa» si quieres bajarla toda.")
        else:
            self._set_status("Pulsa Analizar para detectar la información.")

    def _on_playlist_toggled(self, checked: bool):
        if self.analysis and (self.analysis["kind"] == "playlist") != checked:
            self._reset_analysis()
            self._set_status("Cambiaste el modo playlist: vuelve a pulsar Analizar.")

    def _on_mode_changed(self, mode: str):
        audio = mode == "audio"
        self.meta_card.setVisible(audio)
        self.audio_combo.setVisible(audio)
        self.video_combo.setVisible(not audio)
        self.quality_label.setText("Formato de audio" if audio else "Calidad")

    def _on_paste(self):
        text = QApplication.clipboard().text().strip()
        if text:
            self.url_input.setText(text)
            if is_url(text) and not self._analyzing and not self._downloading:
                self._on_analyze_clicked()

    def _pick_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Seleccionar carpeta", self.folder_input.text())
        if folder:
            self.folder_input.setText(folder)

    def _on_analyze_clicked(self):
        if self._analyzing or self._downloading:
            return
        url = self.url_input.text().strip()
        if not is_url(url):
            QMessageBox.warning(self, "Enlace inválido", "Pega una URL completa (que empiece con https://).")
            return
        self._analyzing = True
        self._refresh_buttons()
        self._set_status("Analizando enlace...", COLORS["periwinkle"])
        self.analyze_requested.emit(url, self.check_playlist.isChecked(), self.cookies_combo.currentText())

    def _collect_metadata(self, is_playlist: bool) -> dict:
        data = {k: e.text().strip() for k, e in self.meta.items()}
        if is_playlist:
            data["title"] = ""
            data["track"] = ""
        return {k: v for k, v in data.items() if v}

    def _on_download_clicked(self):
        if self._analyzing or self._downloading:
            return
        url = self.url_input.text().strip()
        if not is_url(url):
            QMessageBox.warning(self, "Enlace inválido", "Pega una URL completa.")
            return
        if not self.analysis:
            QMessageBox.information(self, "Primero analiza", "Pulsa «Analizar» antes de descargar.")
            return

        audio = self.mode.value() == "audio"
        is_pl = self.analysis["kind"] == "playlist"
        folder = self.folder_input.text().strip() or str(DEFAULT_DOWNLOAD_DIR)

        request = DownloadRequest(
            url=url,
            title=self.analysis["title"],
            mode=self.mode.value(),
            quality=self.video_combo.currentText(),
            audio_format=self.audio_combo.currentText(),
            folder=folder,
            metadata=self._collect_metadata(is_pl) if audio else {},
            playlist=is_pl,
            platform=self.analysis["platform"],
            remove_watermark=self.check_wm.isEnabled() and self.check_wm.isChecked(),
            cookies_browser=self.cookies_combo.currentText(),
        )

        self._downloading = True
        self._refresh_buttons()
        self.console.clear()
        self.set_progress(0, "Iniciando...")
        self.download_requested.emit(request)

    def _on_cancel(self):
        self.cancel_btn.setEnabled(False)
        self.progress_status.setText("Cancelando...")
        self.cancel_requested.emit()


# ============================================================
# HISTORIAL
# ============================================================
class HistoryPage(QWidget):
    reuse_requested = Signal(str)

    def __init__(self):
        super().__init__()
        root, lay = _scroll_page()
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(root)

        header = QHBoxLayout()
        col = QVBoxLayout()
        col.addWidget(make_label("Historial", "title"))
        col.addWidget(make_label("Tus últimas descargas.", "subtitle"))
        header.addLayout(col)
        header.addStretch()
        clear_btn = make_button("Limpiar historial", "danger")
        clear_btn.clicked.connect(self._clear)
        header.addWidget(clear_btn)
        lay.addLayout(header)

        self.list_layout = QVBoxLayout()
        self.list_layout.setSpacing(10)
        lay.addLayout(self.list_layout)
        self.empty = make_label("Aún no has descargado nada.", "hint")
        self.empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(self.empty)
        lay.addStretch()

    def refresh(self):
        while self.list_layout.count():
            item = self.list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        entries = history.load()
        self.empty.setVisible(not entries)
        for entry in entries:
            row = HistoryRow(entry)
            row.open_clicked.connect(self._open)
            row.copy_clicked.connect(self._copy)
            row.reuse_clicked.connect(lambda e: self.reuse_requested.emit(e.get("url", "")))
            row.remove_clicked.connect(self._remove)
            self.list_layout.addWidget(row)

    def _open(self, entry):
        if not open_path(entry.get("folder", "")):
            QMessageBox.information(self, "MediaHub", "La carpeta ya no existe.")

    def _copy(self, entry):
        QApplication.clipboard().setText(entry.get("url", ""))

    def _remove(self, entry):
        history.remove(entry["id"])
        self.refresh()

    def _clear(self):
        if QMessageBox.question(self, "MediaHub", "¿Borrar todo el historial?") == QMessageBox.StandardButton.Yes:
            history.clear()
            self.refresh()
