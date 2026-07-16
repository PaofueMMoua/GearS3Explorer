from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QPushButton,
    QStackedWidget,
    QLabel,
    QStatusBar,
    QFrame
)
from PySide6.QtCore import Qt

from core.sdb import SDBManager
from ui.pages.home_page import HomePage

# Temporary skeleton imports for pages we are about to create
# (We will define these simple placeholders below so the app runs)
class FilesPage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("📂 File Explorer Page (Placeholder)"))

class DevicePage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("⌚ Device Manager Page (Placeholder)"))

class TerminalPage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("💻 SDB Terminal Page (Placeholder)"))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Window Settings
        self.setWindowTitle("GearS3 Explorer")
        self.resize(1300, 800)

        # Initialize SDB Manager
        self.manager = SDBManager()

        # Set up the UI layout
        self.init_ui()

    def init_ui(self):
        # Main central widget & layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. Create Sidebar
        sidebar = self.create_sidebar()
        main_layout.addWidget(sidebar)

        # 2. Create Stacked Widget (Page Container)
        self.page_container = QStackedWidget()
        main_layout.addWidget(self.page_container)

        # 3. Instantiate and Add Pages
        self.home_page = HomePage()
        self.device_page = DevicePage()
        self.files_page = FilesPage()
        self.terminal_page = TerminalPage()

        self.page_container.addWidget(self.home_page)      # Index 0
        self.page_container.addWidget(self.device_page)    # Index 1
        self.page_container.addWidget(self.files_page)     # Index 2
        self.page_container.addWidget(self.terminal_page)  # Index 3

        # Set Status Bar
        self.status = QStatusBar()
        self.status.showMessage("SDB initialized.")
        self.setStatusBar(self.status)

    def create_sidebar(self) -> QFrame:
        """Creates the navigation sidebar."""
        sidebar = QFrame()
        sidebar.setFixedWidth(220)
        sidebar.setStyleSheet("""
            QFrame {
                background-color: #1e1e24;
                border-right: 1px solid #2d2d35;
            }
            QPushButton {
                background-color: transparent;
                color: #b3b3b3;
                border: none;
                padding: 12px 20px;
                text-align: left;
                font-size: 14px;
                font-weight: 500;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #2d2d35;
                color: #ffffff;
            }
            QPushButton:pressed {
                background-color: #3d3d45;
            }
        """)

        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(10, 20, 10, 20)
        sidebar_layout.setSpacing(8)

        # Sidebar Title
        title = QLabel("GearS3 Explorer")
        title.setStyleSheet("""
            color: #ffffff;
            font-size: 18px;
            font-weight: bold;
            padding: 10px 10px 20px 10px;
        """)
        sidebar_layout.addWidget(title)

        # Navigation Buttons
        self.btn_home = QPushButton("🏠 Home")
        self.btn_devices = QPushButton("⌚ Connected Devices")
        self.btn_files = QPushButton("📂 File Explorer")
        self.btn_terminal = QPushButton("💻 Terminal Command")

        sidebar_layout.addWidget(self.btn_home)
        sidebar_layout.addWidget(self.btn_devices)
        sidebar_layout.addWidget(self.btn_files)
        sidebar_layout.addWidget(self.btn_terminal)

        # Push everything else up
        sidebar_layout.addStretch()

        # Connections to switch pages
        self.btn_home.clicked.connect(lambda: self.switch_page(0))
        self.btn_devices.clicked.connect(lambda: self.switch_page(1))
        self.btn_files.clicked.connect(lambda: self.switch_page(2))
        self.btn_terminal.clicked.connect(lambda: self.switch_page(3))

        return sidebar

    def switch_page(self, index: int):
        """Changes the active page in our stacked widget."""
        self.page_container.setCurrentIndex(index)
        
        # Update status bar just for visual feedback
        pages = ["Home", "Device Manager", "File Explorer", "Terminal"]
        self.status.showMessage(f"Viewing: {pages[index]}")