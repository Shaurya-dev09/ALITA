# =========================================================
# conversation_panel.py
# FRIDAY X - Complete Final
# =========================================================

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,                               
    QScrollArea,
    QVBoxLayout,
    QWidget,
)


class ConversationPanel(QFrame):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("conversation_panel")
        self.setup_ui()

    def setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(14, 10, 14, 10)
        root.setSpacing(8)

        # Title
        self.title = QLabel("CONVERSATION")
        self.title.setObjectName("conversation_title")
        self.title.setAlignment(Qt.AlignCenter)
        root.addWidget(self.title)

        # Scroll area
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        self.container = QWidget()
        self.container.setStyleSheet("background: transparent;")
        self.messages_layout = QVBoxLayout(self.container)
        self.messages_layout.setContentsMargins(4, 4, 4, 4)
        self.messages_layout.setSpacing(8)
        self.messages_layout.addStretch()

        self.scroll.setWidget(self.container)
        root.addWidget(self.scroll, 1)

    # =================================================
    # ADD MESSAGES
    # =================================================

    def add_user_message(self, text: str):
        text = str(text or "").strip()
        if not text:
            return
        self._add_bubble(text, is_user=True)

    def add_friday_message(self, text: str):
        text = str(text or "").strip()
        if not text:
            return
        self._add_bubble(text, is_user=False)

    def add_message(self, text: str, sender: str = "friday"):
        if str(sender).lower() in ("user", "boss", "me"):
            self.add_user_message(text)
        else:
            self.add_friday_message(text)

    def _add_bubble(self, text: str, is_user: bool):
        # Remove bottom stretch temporarily
        if self.messages_layout.count() > 0:
            item = self.messages_layout.itemAt(self.messages_layout.count() - 1)
            if item and item.spacerItem():
                self.messages_layout.removeItem(item)

        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)

        bubble = QFrame()
        bubble.setObjectName("boss_message" if is_user else "friday_message")

        inner = QVBoxLayout(bubble)
        inner.setContentsMargins(12, 8, 12, 8)
        inner.setSpacing(2)

        who = QLabel("BOSS" if is_user else "FRIDAY")
        who.setStyleSheet(
            "color: #7adfff; font-size: 9px; font-weight: 700;"
            if not is_user
            else "color: #9ec4d6; font-size: 9px; font-weight: 700;"
        )

        msg = QLabel(text)
        msg.setWordWrap(True)
        msg.setStyleSheet("color: #e8f7ff; font-size: 12px;")
        msg.setTextInteractionFlags(Qt.TextSelectableByMouse)

        inner.addWidget(who)
        inner.addWidget(msg)

        if is_user:
            row.addStretch()
            row.addWidget(bubble, 0, Qt.AlignRight)
        else:
            row.addWidget(bubble, 0, Qt.AlignLeft)
            row.addStretch()

        wrap = QWidget()
        wrap.setLayout(row)
        self.messages_layout.addWidget(wrap)
        self.messages_layout.addStretch()

        # Auto scroll bottom
        self.scroll.verticalScrollBar().setValue(
            self.scroll.verticalScrollBar().maximum()
        )

    # =================================================
    # UTILS
    # =================================================

    def clear(self):
        while self.messages_layout.count():
            item = self.messages_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
        self.messages_layout.addStretch()

    def refresh(self):
        pass

    def shutdown(self):
        pass

    def __repr__(self):
        return "<FRIDAY X ConversationPanel>"