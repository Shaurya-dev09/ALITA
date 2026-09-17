# =========================================================
# sidebar.py
# FRIDAY X - Complete Final (Serious Mode Support)
# =========================================================

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QPushButton,
    QVBoxLayout,
)


class Sidebar(QFrame):

    navigation_changed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setObjectName("sidebar")
        self.active_page = "Dashboard"
        self.serious_mode = False
        self.buttons = {}

        self.setup_ui()

    # =================================================
    # UI
    # =================================================

    def setup_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(16, 18, 16, 16)
        self.layout.setSpacing(8)

        # Brand
        self.brand_title = QLabel("FRIDAY X")
        self.brand_title.setObjectName("brand_title")

        self.brand_subtitle = QLabel("AI ASSISTANT")
        self.brand_subtitle.setObjectName("brand_subtitle")

        self.layout.addWidget(self.brand_title)
        self.layout.addWidget(self.brand_subtitle)
        self.layout.addSpacing(20)

        # Profile Card
        self.profile_card = QFrame()
        self.profile_card.setObjectName("profile_card")

        profile_layout = QVBoxLayout(self.profile_card)
        profile_layout.setContentsMargins(14, 14, 14, 14)
        profile_layout.setSpacing(5)

        self.profile_name = QLabel("Good Morning,\nBoss!")
        self.profile_name.setObjectName("profile_name")

        self.profile_status = QLabel("●  FRIDAY X ONLINE")
        self.profile_status.setObjectName("profile_status")

        profile_layout.addWidget(self.profile_name)
        profile_layout.addWidget(self.profile_status)

        self.layout.addWidget(self.profile_card)
        self.layout.addSpacing(14)

        # Navigation
        self._add_nav_button("Dashboard", "⌂")
        self._add_nav_button("System", "◈")
        self._add_nav_button("Applications", "▦")
        self._add_nav_button("Voice", "♬")
        self._add_nav_button("AI Chat", "◌")
        self._add_nav_button("Phone Link", "▯")
        self._add_nav_button("Settings", "⚙")

        self.layout.addStretch()

        # Weather Card
        self.weather_card = QFrame()
        self.weather_card.setObjectName("weather_card")

        weather_layout = QVBoxLayout(self.weather_card)
        weather_layout.setContentsMargins(14, 14, 14, 14)
        weather_layout.setSpacing(4)

        self.temperature = QLabel("29°C")
        self.temperature.setObjectName("temperature")

        self.weather_text = QLabel("Mostly Cloudy\nVadodara, GJ")
        self.weather_text.setObjectName("weather_text")

        weather_layout.addWidget(self.temperature)
        weather_layout.addWidget(self.weather_text)

        self.layout.addWidget(self.weather_card)

    # =================================================
    # NAV BUTTONS
    # =================================================

    def _add_nav_button(self, title: str, icon: str):
        button = QPushButton()
        button.setObjectName("nav_button")
        button.setCursor(Qt.PointingHandCursor)
        button.setText(f"{icon}   {title}")
        button.setProperty("page_name", title)

        button.clicked.connect(
            lambda checked=False, page=title: self.set_active_page(page)
        )

        self.layout.addWidget(button)
        self.buttons[title] = button

        if title == self.active_page:
            button.setProperty("selected", True)
            self._refresh_button(button)

    def set_active_page(self, page: str):
        page = str(page).strip()
        if not page:
            return

        self.active_page = page

        for name, button in self.buttons.items():
            selected = name == page
            button.setProperty("selected", selected)
            self._refresh_button(button)

        self.navigation_changed.emit(page)

    def _refresh_button(self, button):
        style = button.style()
        if style:
            style.unpolish(button)
            style.polish(button)
            button.update()

    # =================================================
    # SERIOUS MODE
    # =================================================

    def set_serious_mode(self, enabled: bool):
        self.serious_mode = bool(enabled)
        if self.serious_mode:
            self.profile_status.setText("●  SERIOUS MODE")
        else:
            self.profile_status.setText("●  FRIDAY X ONLINE")

    # =================================================
    # CONVENIENCE
    # =================================================

    def select_dashboard(self):
        self.set_active_page("Dashboard")

    def select_system(self):
        self.set_active_page("System")

    def select_applications(self):
        self.set_active_page("Applications")

    def select_voice(self):
        self.set_active_page("Voice")

    def select_ai_chat(self):
        self.set_active_page("AI Chat")

    def select_phone_link(self):
        self.set_active_page("Phone Link")

    def select_settings(self):
        self.set_active_page("Settings")

    def set_weather(self, temperature, description, location="Vadodara, GJ"):
        self.temperature.setText(str(temperature))
        self.weather_text.setText(f"{description}\n{location}")

    def set_online(self, online: bool = True):
        if self.serious_mode:
            self.profile_status.setText("●  SERIOUS MODE")
        elif online:
            self.profile_status.setText("●  FRIDAY X ONLINE")
        else:
            self.profile_status.setText("●  FRIDAY X OFFLINE")

    def refresh(self):
        pass

    def shutdown(self):
        pass

    def __repr__(self):
        return f"<FRIDAY X Sidebar serious={self.serious_mode}>"