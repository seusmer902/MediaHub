"""MediaHub — punto de entrada."""
import sys
import ctypes

from PySide6.QtWidgets import QApplication

from config import APP_NAME, STYLE
from ui.main_window import MainWindow


def main():
    if sys.platform == "win32":
        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("MediaHub.App")
        except Exception:
            pass

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setStyle("Fusion")
    app.setStyleSheet(STYLE)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
