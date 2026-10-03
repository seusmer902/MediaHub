"""Configuración global: rutas, paleta y estilo (QSS)."""
import sys
from pathlib import Path

APP_NAME = "MediaHub"
VERSION = "V0.2"

# Si está empaquetado (.exe) los datos viven junto al ejecutable.
if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys.executable).resolve().parent
else:
    BASE_DIR = Path(__file__).resolve().parent

DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
HISTORY_FILE = DATA_DIR / "history.json"
MAX_HISTORY = 200
COOKIES_FILE = DATA_DIR / "cookies.txt"   # opcional: cookies exportadas de YouTube
BROWSERS = ["Ninguno", "Firefox", "Edge", "Chrome", "Brave", "Opera"]

DEFAULT_DOWNLOAD_DIR = Path.home() / "Downloads" / "MediaHub"

QUALITIES = ["Mejor disponible", "2160p", "1440p", "1080p", "720p", "480p", "360p"]

# nombre visible -> (códec, calidad)
AUDIO_FORMATS = {
    "MP3 · 320 kbps": ("mp3", "320"),
    "MP3 · 192 kbps": ("mp3", "192"),
    "M4A · AAC": ("m4a", "192"),
}

COLORS = {
    "periwinkle": "#E3D9FC",
    "magenta": "#BF40FA",
    "blue": "#4928C2",
    "blue2": "#5B38D8",
    "velvet": "#5B2A62",
    "black": "#040607",
    "white": "#F7F4FF",
    "muted": "#A99FC0",
    "panel": "#100B16",
    "panel2": "#171020",
    "border": "#2B2036",
    "ok": "#3DDC97",
    "err": "#FF5C7A",
}

_STYLE = """
* { font-family: "Segoe UI", "Inter", "Helvetica Neue", sans-serif; }

QWidget { background: transparent; color: @white; }
QMainWindow, QWidget#root { background: @black; }
QMessageBox, QDialog { background: @panel2; }
QToolTip { background: @panel2; color: @white; border: 1px solid @border; padding: 5px; }

QScrollArea { background: transparent; border: none; }

/* ---------- Sidebar ---------- */
QFrame#sidebar { background: #09060C; border-right: 1px solid @border; }
QLabel#brand { color: @periwinkle; font-size: 27px; font-weight: 800; }
QLabel#sidebarSubtitle { color: @muted; font-size: 10px; font-weight: 600; letter-spacing: 1px; }

QPushButton#nav {
    text-align: left; padding: 12px 14px; color: @muted; background: transparent;
    border: none; border-left: 3px solid transparent; border-radius: 10px;
    font-size: 13px; font-weight: 600;
}
QPushButton#nav:hover { color: @periwinkle; background: #140D1C; }
QPushButton#nav:checked { color: @white; background: #241533; border-left: 3px solid @magenta; }

/* ---------- Textos ---------- */
QLabel#title { font-size: 26px; font-weight: 800; }
QLabel#subtitle { color: @muted; font-size: 13px; }
QLabel#section { color: @periwinkle; font-size: 16px; font-weight: 700; }
QLabel#hint { color: @muted; font-size: 12px; }
QLabel#field { color: @muted; font-size: 12px; font-weight: 600; }
QLabel#rowTitle { font-size: 14px; font-weight: 700; }

QLabel#badge {
    background: @velvet; color: @periwinkle; padding: 8px 14px;
    border-radius: 12px; font-weight: 700; font-size: 12px;
}
QLabel#chip {
    background: #24153A; color: @periwinkle; padding: 4px 11px;
    border-radius: 10px; font-size: 11px; font-weight: 700;
}
QLabel#thumb { background: #0A0710; border-radius: 12px; color: #5B4B67; font-size: 38px; font-weight: 800; }
QLabel#historyIcon { background: @velvet; color: @periwinkle; border-radius: 12px; font-size: 18px; }

/* ---------- Tarjetas ---------- */
QFrame#card {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #16101D, stop:0.55 @panel, stop:1 #181020);
    border: 1px solid @border; border-radius: 18px;
}
QFrame#historyRow { background: #120C18; border: 1px solid @border; border-radius: 14px; }
QFrame#historyRow:hover { border-color: #5B2A62; }

/* ---------- Inputs ---------- */
QLineEdit, QComboBox, QTextEdit {
    background: #0C0910; color: @white; border: 1px solid #32253E;
    border-radius: 10px; padding: 10px 12px; selection-background-color: @blue;
}
QLineEdit:focus, QComboBox:focus, QTextEdit:focus { border: 1px solid @magenta; }
QLineEdit:disabled { color: #6F6480; background: #09070C; }
QComboBox QAbstractItemView {
    background: #120C18; color: white; border: 1px solid @border;
    selection-background-color: @blue; outline: 0;
}
QTextEdit#console { font-family: "Cascadia Mono", "Consolas", monospace; font-size: 11px; color: @muted; }

/* ---------- Botones ---------- */
QPushButton {
    background: #1A1222; color: @white; border: 1px solid #3B2A48;
    border-radius: 11px; padding: 10px 16px; font-weight: 700;
}
QPushButton:hover { background: #26152F; border-color: @magenta; }
QPushButton:pressed { background: #31193D; }
QPushButton:disabled { color: #6F6480; border-color: #241B2E; background: #120C18; }

QPushButton#small { padding: 6px 12px; border-radius: 9px; font-size: 12px; }

QPushButton#analyze { background: @blue; border: none; padding: 10px 22px; }
QPushButton#analyze:hover { background: @blue2; }
QPushButton#analyze:disabled { background: #251A4A; color: #6F6480; }

QPushButton#primary {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 @magenta, stop:1 @blue);
    color: white; border: none; border-radius: 14px; padding: 14px 32px;
    font-size: 15px; font-weight: 800;
}
QPushButton#primary:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #D15BFF, stop:1 @blue2);
}
QPushButton#primary:disabled { background: #2A2033; color: #6F6480; }

QPushButton#danger { color: @err; border: 1px solid #5A2535; background: #1A0F15; }
QPushButton#danger:hover { background: #2A1420; border-color: @err; }

QPushButton#segment {
    background: #120C18; border: 1px solid #32253E; border-radius: 10px;
    padding: 9px 24px; color: @muted;
}
QPushButton#segment:hover { color: @periwinkle; border-color: #5B2A62; }
QPushButton#segment:checked { background: @blue; color: white; border: 1px solid @magenta; }

/* ---------- Check ---------- */
QCheckBox { spacing: 9px; }
QCheckBox::indicator { width: 18px; height: 18px; border-radius: 5px; border: 1px solid #4A3560; background: #0C0910; }
QCheckBox::indicator:checked { background: @magenta; border-color: @magenta; }
QCheckBox:disabled { color: #6F6480; }

/* ---------- Progreso ---------- */
QProgressBar {
    background: #0B0810; border: 1px solid @border; border-radius: 8px;
    height: 14px; text-align: center; color: white;
}
QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 @blue, stop:1 @magenta);
    border-radius: 7px;
}

/* ---------- Scroll ---------- */
QScrollBar:vertical { background: transparent; width: 10px; margin: 2px; }
QScrollBar::handle:vertical { background: #34233F; border-radius: 4px; min-height: 30px; }
QScrollBar::handle:vertical:hover { background: #4A3160; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar:horizontal { height: 0; }
"""

STYLE = _STYLE
for _k in sorted(COLORS, key=len, reverse=True):
    STYLE = STYLE.replace(f"@{_k}", COLORS[_k])
