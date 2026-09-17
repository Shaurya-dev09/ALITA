# =========================================================
# main.py
# FRIDAY X - Complete Final Version
# =========================================================

import sys

from PySide6.QtWidgets import QApplication

from ui.main_window import MainWindow
from ui.styles import get_stylesheet


def main():
    app = QApplication(sys.argv)

    app.setApplicationName("FRIDAY X")
    app.setOrganizationName("FRIDAY X")

    # Global futuristic HUD style
    app.setStyleSheet(get_stylesheet())

    app.setQuitOnLastWindowClosed(True)

    # Main Window
    window = MainWindow()
    window.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())