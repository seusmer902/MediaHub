"""Componentes visuales reutilizables."""
from pathlib import Path

from PySide6.QtCore import Qt, Signal, QRectF, QUrl
from PySide6.QtGui import QPixmap, QPainter, QPainterPath, QDesktopServices
from PySide6.QtWidgets import (
    QFrame, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QWidget, QButtonGroup,
)


def make_label(text="", name=None, wrap=False) -> QLabel:
    label = QLabel(text)
    if name:
        label.setObjectName(name)
    label.setWordWrap(wrap)
    return label


def make_button(text, name=None) -> QPushButton:
    button = QPushButton(text)
    if name:
        button.setObjectName(name)
    button.setCursor(Qt.CursorShape.PointingHandCursor)
    return button


def open_path(path) -> bool:
    p = Path(path)
    if p.is_file():
        p = p.parent
    if not p.exists():
        return False
    return QDesktopServices.openUrl(QUrl.fromLocalFile(str(p)))


class Card(QFrame):
    def __init__(self, title=None, subtitle=None, margins=(22, 18, 22, 20)):
        super().__init__()
        self.setObjectName("card")
        self.body = QVBoxLayout(self)
        self.body.setContentsMargins(*margins)
        self.body.setSpacing(12)
        if title:
            self.body.addWidget(make_label(title, "section"))
        if subtitle:
            self.body.addWidget(make_label(subtitle, "hint", True))


class NavButton(QPushButton):
    def __init__(self, text):
        super().__init__(text)
        self.setObjectName("nav")
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)


class SegmentedControl(QWidget):
    changed = Signal(str)

    def __init__(self, options):
        super().__init__()
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(8)
        self._group = QButtonGroup(self)
        self._group.setExclusive(True)
        self._buttons = {}
        for key, text in options:
            b = make_button(text, "segment")
            b.setCheckable(True)
            self._group.addButton(b)
            lay.addWidget(b)
            self._buttons[key] = b
            b.clicked.connect(lambda _=False, k=key: self.set_value(k))
        lay.addStretch()
        self._value = options[0][0]
        self._buttons[self._value].setChecked(True)

    def value(self) -> str:
        return self._value

    def set_value(self, key: str):
        self._buttons[key].setChecked(True)
        if key != self._value:
            self._value = key
            self.changed.emit(key)


class ThumbnailView(QLabel):
    W, H = 232, 130

    def __init__(self):
        super().__init__()
        self.setObjectName("thumb")
        self.setFixedSize(self.W, self.H)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.reset()

    def reset(self):
        self.clear()
        self.setText("♫")

    def set_image(self, data: bytes) -> bool:
        pm = QPixmap()
        if not pm.loadFromData(data):
            return False
        pm = pm.scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                       Qt.TransformationMode.SmoothTransformation)
        pm = pm.copy((pm.width() - self.W) // 2, (pm.height() - self.H) // 2, self.W, self.H)
        rounded = QPixmap(self.W, self.H)
        rounded.fill(Qt.GlobalColor.transparent)
        p = QPainter(rounded)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(QRectF(0, 0, self.W, self.H), 12, 12)
        p.setClipPath(path)
        p.drawPixmap(0, 0, pm)
        p.end()
        self.setPixmap(rounded)
        return True


class HistoryRow(QFrame):
    open_clicked = Signal(dict)
    copy_clicked = Signal(dict)
    reuse_clicked = Signal(dict)
    remove_clicked = Signal(dict)

    def __init__(self, entry: dict):
        super().__init__()
        self.entry = entry
        self.setObjectName("historyRow")

        lay = QHBoxLayout(self)
        lay.setContentsMargins(16, 12, 12, 12)
        lay.setSpacing(14)

        icon = make_label("♫" if entry.get("mode") == "audio" else "▣", "historyIcon")
        icon.setFixedSize(42, 42)
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(icon)

        col = QVBoxLayout()
        col.setSpacing(2)
        col.addWidget(make_label(entry.get("title") or entry.get("url", ""), "rowTitle", True))
        kind = "Audio" if entry.get("mode") == "audio" else "Video"
        extra = f" · {entry['count']} archivos" if entry.get("count", 1) > 1 else ""
        col.addWidget(make_label(
            f"{entry.get('platform', '')} · {kind}{extra} · {entry.get('date', '')}", "hint"))
        lay.addLayout(col, 1)

        for text, sig in (("Abrir carpeta", self.open_clicked), ("Copiar enlace", self.copy_clicked),
                          ("Reusar", self.reuse_clicked), ("✕", self.remove_clicked)):
            b = make_button(text, "small")
            b.clicked.connect(lambda _=False, s=sig: s.emit(self.entry))
            lay.addWidget(b)
