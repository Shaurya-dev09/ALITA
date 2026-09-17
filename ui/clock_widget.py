from PySide6.QtWidgets import QLabel
from PySide6.QtCore import Qt, QTimer, QTime

class ClockWidget(QLabel):
    def __init__(self):
        super().__init__()

        self.setAlignment(Qt.AlignCenter)

        self.setStyleSheet("""
            QLabel{
                color:#00E5FF;
                font-size:24px;
                font-weight:bold;
                background:transparent;
            }
        """)

        timer = QTimer(self)
        timer.timeout.connect(self.update_time)
        timer.start(1000)

        self.update_time()

    def update_time(self):
        self.setText(QTime.currentTime().toString("hh:mm:ss AP"))