from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, 
    QStackedWidget, QPushButton, QLabel, QFrame
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon

# Core SDB manager to share across all views
from core.sdb import SDBManager

# Import all page views
from ui.pages.home_page import HomePage
from ui.pages.device_page import DevicePage
from ui.pages.files_pages import FilesPage  # Matches files_pages.py
from ui.pages.terminal_page import TerminalPage
from ui.pages.sideload_page import SideloadPage


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gear S3 Explorer")
        self.resize(1000, 650)
        
        # Initialize the shared SDB manager
        self.manager = SDBManager()

        # Modern overall dark styling
        self.setStyleSheet("""
            QMainWindow {
                background-color: #0f0f12;
            }
            QWidget {
                color: #ffffff;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QLabel {
                color: #ffffff;
            }
        """)

        self.init_ui()

    def init_ui(self):
        # Main central widget with a horizontal layout (Sidebar on left, Pages on right)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ----------------------------------------------------
        # 1. SIDEBAR NAVIGATION
        # ----------------------------------------------------
        sidebar = QFrame()
        sidebar.setFixedWidth(220)
        sidebar.setStyleSheet("""
            QFrame {
                background-color: #16161a;
                border-right: 1px solid #25252b;
            }
        """)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(10, 20, 10, 20)
        sidebar_layout.setSpacing(8)

        # App Logo / Brand Title
        app_title = QLabel("⌚ Gear S3 Tool")
        app_title.setStyleSheet("""
            font-size: 18px; 
            font-weight: bold; 
            color: #3a75b5; 
            margin-bottom: 20px;
            padding-left: 10px;
        """)
        sidebar_layout.addWidget(app_title)

        # Sidebar Buttons Definition
        self.nav_buttons = []
        
        menu_items = [
            ("🏠 Home Dashboard", 0),
            ("⌚ Connected Devices", 1),
            ("📂 File Explorer", 2),
            ("💻 Shell Terminal", 3),
            ("📦 Sideload Apps", 4)  # Added sideloading navigation entry
        ]

        # Template style sheet for buttons
        self.btn_style_inactive = """
            QPushButton {
                background-color: transparent;
                border: none;
                border-radius: 5px;
                color: #a0a0a5;
                font-size: 13px;
                font-weight: 500;
                text-align: left;
                padding: 12px 15px;
            }
            QPushButton:hover {
                background-color: #202026;
                color: #ffffff;
            }
        """

        self.btn_style_active = """
            QPushButton {
                background-color: #2b5c8f;
                border: none;
                border-radius: 5px;
                color: #ffffff;
                font-size: 13px;
                font-weight: bold;
                text-align: left;
                padding: 12px 15px;
            }
        """

        for label, index in menu_items:
            btn = QPushButton(label)
            btn.setStyleSheet(self.btn_style_inactive)
            # Connect button click directly to page switcher
            btn.clicked.connect(lambda checked=False, idx=index: self.switch_page(idx))
            sidebar_layout.addWidget(btn)
            self.nav_buttons.append(btn)

        sidebar_layout.addStretch()

        # Footer Credit
        footer = QLabel("v1.2.0")
        footer.setStyleSheet("color: #44444a; font-size: 11px; padding-left: 10px;")
        sidebar_layout.addWidget(footer)

        # ----------------------------------------------------
        # 2. PAGE CONTROLLER (Stacked Widget)
        # ----------------------------------------------------
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.setStyleSheet("background-color: #0f0f12;")

        # Instantiate all pages passing our shared SDB session manager
        self.home_page = HomePage(self.manager)
        self.device_page = DevicePage(self.manager)
        self.files_page = FilesPage(self.manager)
        self.terminal_page = TerminalPage(self.manager)
        self.sideload_page = SideloadPage(self.manager)  # Instantiated SideloadPage

        # Register pages in stacked order (matching indices 0 to 4)
        self.stacked_widget.addWidget(self.home_page)      # Index 0
        self.stacked_widget.addWidget(self.device_page)    # Index 1
        self.stacked_widget.addWidget(self.files_page)     # Index 2
        self.stacked_widget.addWidget(self.terminal_page)  # Index 3
        self.stacked_widget.addWidget(self.sideload_page)  # Index 4

        # Connect Home Page dashboard card signals to jump tabs automatically
        self.home_page.request_page_change.connect(self.switch_page)

        # Assemble Sidebar and Pages inside the central window
        main_layout.addWidget(sidebar)
        main_layout.addWidget(self.stacked_widget, stretch=1)

        # Set default active page (Home)
        self.switch_page(0)

    def switch_page(self, index: int):
        """Switches the visible stacked page and updates sidebar button focus colors."""
        self.stacked_widget.setCurrentIndex(index)

        # Loop through sidebar navigation items to toggle visual focus indicators
        for i, btn in enumerate(self.nav_buttons):
            if i == index:
                btn.setStyleSheet(self.btn_style_active)
            else:
                btn.setStyleSheet(self.btn_style_inactive)