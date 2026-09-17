# =========================================================
# styles.py
# ALITA — Futuristic HUD themes (Normal + Focus)
# =========================================================

NORMAL_STYLE = """
QWidget {
    background: #030b14;
    color: #c8e8ff;
    font-family: "Segoe UI", "Consolas", sans-serif;
    font-size: 12px;
}
QMainWindow, QFrame#dashboard {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
        stop:0 #020810, stop:0.5 #041018, stop:1 #030b14);
}
QFrame { background: transparent; border: none; }
QLabel { background: transparent; color: #c8e8ff; }

QFrame#hud_panel {
    background: rgba(0, 28, 48, 160);
    border: 1px solid rgba(0, 180, 255, 90);
    border-radius: 10px;
}
QLabel#hud_title {
    color: #00d4ff;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 2px;
}
QLabel#hud_value {
    color: #e8f7ff;
    font-size: 22px;
    font-weight: 700;
}
QLabel#hud_sub { color: #5a9eb8; font-size: 10px; }
QLabel#brand_title {
    color: #00e5ff;
    font-size: 16px;
    font-weight: 700;
    letter-spacing: 3px;
}
QLabel#brand_sub { color: #4db8d9; font-size: 10px; letter-spacing: 2px; }
QLabel#status_ok { color: #00ff9d; font-size: 10px; font-weight: 700; }

QProgressBar {
    background: #031820;
    border: 1px solid #0a4a6a;
    border-radius: 3px;
    max-height: 6px;
}
QProgressBar::chunk {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 #0090c8, stop:1 #00e8b0);
    border-radius: 3px;
}
QLineEdit#command_input {
    background: rgba(0, 24, 40, 200);
    color: #e0f4ff;
    border: 1px solid rgba(0, 160, 220, 120);
    border-radius: 8px;
    padding: 10px 14px;
    font-size: 13px;
    selection-background-color: #0080a0;
}
QLineEdit#command_input:focus {
    border: 1px solid #00d4ff;
}
QPushButton#quick_btn {
    background: rgba(0, 36, 60, 180);
    color: #8ecde0;
    border: 1px solid rgba(0, 140, 200, 100);
    border-radius: 8px;
    padding: 8px 12px;
    font-weight: 600;
}
QPushButton#quick_btn:hover {
    background: rgba(0, 60, 100, 220);
    color: #ffffff;
    border: 1px solid #00d4ff;
}
QPushButton#quick_btn:pressed {
    background: rgba(0, 80, 120, 255);
}
"""

SERIOUS_STYLE = """
QWidget {
    background: #000000;
    color: #e8c8c8;
    font-family: "Segoe UI", "Consolas", sans-serif;
    font-size: 12px;
}
QMainWindow, QFrame#dashboard {
    background: #000000;
}
QFrame { background: transparent; border: none; }
QLabel { background: transparent; color: #e8c8c8; }

QFrame#hud_panel {
    background: rgba(12, 2, 6, 120);
    border: 1px solid rgba(255, 50, 80, 50);
    border-radius: 8px;
}
QLabel#hud_title {
    color: #ff3355;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 2px;
}
QLabel#hud_value {
    color: #ffd0d5;
    font-size: 26px;
    font-weight: 700;
}
QLabel#hud_sub { color: #7a3040; font-size: 10px; }
QLabel#brand_title {
    color: #ff4466;
    font-size: 15px;
    font-weight: 700;
    letter-spacing: 3px;
}
QLabel#brand_sub { color: #8a2030; font-size: 10px; letter-spacing: 2px; }
QLabel#status_ok { color: #ff5570; font-size: 10px; font-weight: 700; }

QProgressBar {
    background: #120408;
    border: none;
    border-radius: 2px;
    max-height: 4px;
}
QProgressBar::chunk {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 #5a0810, stop:1 #ff2040);
    border-radius: 2px;
}
QLineEdit#command_input {
    background: rgba(0, 0, 0, 160);
    color: #f0d0d5;
    border: none;
    border-bottom: 1px solid #5a1018;
    border-radius: 0px;
    padding: 10px 4px;
    font-size: 13px;
}
QLineEdit#command_input:focus {
    border-bottom: 1px solid #ff3355;
}
QPushButton#quick_btn {
    background: transparent;
    color: #a05060;
    border: 1px solid #3a1018;
    border-radius: 6px;
    padding: 8px 12px;
}
QPushButton#quick_btn:hover {
    background: rgba(40, 5, 10, 200);
    color: #ffffff;
    border: 1px solid #ff3355;
}
"""


def get_stylesheet(serious_mode: bool = False) -> str:
    return SERIOUS_STYLE if serious_mode else NORMAL_STYLE