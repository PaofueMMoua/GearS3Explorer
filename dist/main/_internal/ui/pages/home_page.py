from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QGridLayout
)
from PySide6.QtCore import Qt, Signal
from core.sdb import SDBManager


class DashboardCard(QFrame):
    """A reusable, modern styled card for the home page dashboard."""
    clicked = Signal()

    def __init__(self, title: str, description: str, icon: str, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet("""
            QFrame {
                background-color: #16161a;
                border: 1px solid #25252b;
                border-radius: 8px;
                padding: 15px;
            }
            QFrame:hover {
                background-color: #1e1e24;
                border-color: #3a75b5;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # Header Row (Icon + Title)
        header_layout = QHBoxLayout()
        
        icon_lbl = QLabel(icon)
        icon_lbl.setStyleSheet("font-size: 24px; background: transparent;")
        
        title_lbl = QLabel(title)
        title_lbl.setStyleSheet("font-size: 16px; font-weight: bold; color: #ffffff; background: transparent;")
        
        header_layout.addWidget(icon_lbl)
        header_layout.addWidget(title_lbl)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        # Description
        desc_lbl = QLabel(description)
        desc_lbl.setWordWrap(True)
        desc_lbl.setStyleSheet("font-size: 12px; color: #a0a0a5; background: transparent;")
        layout.addWidget(desc_lbl)

        layout.addStretch()

        # Action Button
        self.btn = QPushButton("Open")
        self.btn.setFixedWidth(80)
        self.btn.setStyleSheet("""
            QPushButton {
                background-color: #2b5c8f;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3a75b5;
            }
        """)
        self.btn.clicked.connect(self.clicked.emit)
        
        # Align button to the right
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn)
        layout.addLayout(btn_layout)


class HomePage(QWidget):
    # Emits the index of the page we want MainWindow to switch to
    request_page_change = Signal(int)

    # FIX: Accepts the shared SDBManager instance to prevent compilation crashes
    def __init__(self, sdb_manager: SDBManager = None):
        super().__init__()
        self.sdb = sdb_manager if sdb_manager else SDBManager()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(25)

        # 1. Welcome Header
        header_layout = QVBoxLayout()
        welcome_title = QLabel("Welcome to Gear S3 Explorer")
        welcome_title.setStyleSheet("font-size: 26px; font-weight: bold; color: #ffffff;")
        
        welcome_subtitle = QLabel("Manage your Samsung Tizen smartwatch files, execute shell commands, and install apps.")
        welcome_subtitle.setStyleSheet("font-size: 14px; color: #a0a0a5;")
        
        header_layout.addWidget(welcome_title)
        header_layout.addWidget(welcome_subtitle)
        layout.addLayout(header_layout)

        # 2. Status Frame (Quick connection overview)
        self.status_frame = QFrame()
        self.status_frame.setStyleSheet("""
            QFrame {
                background-color: #111115;
                border: 1px solid #1e1e24;
                border-radius: 6px;
                padding: 15px;
            }
        """)
        status_layout = QHBoxLayout(self.status_frame)
        
        self.status_indicator = QLabel("⚪ Unknown Status")
        self.status_indicator.setStyleSheet("font-size: 14px; font-weight: bold; color: #a0a0a5;")
        status_layout.addWidget(self.status_indicator)
        
        status_layout.addStretch()
        
        btn_check = QPushButton("Check Connection")
        btn_check.setStyleSheet("""
            QPushButton {
                background-color: #1e1e24;
                color: #ffffff;
                border: 1px solid #2d2d35;
                border-radius: 4px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: #25252b;
            }
        """)
        btn_check.clicked.connect(self.update_connection_status)
        status_layout.addWidget(btn_check)
        
        layout.addWidget(self.status_frame)

        # 3. Grid of Feature Cards
        grid = QGridLayout()
        grid.setSpacing(20)

        # Card 1: Devices
        card_devices = DashboardCard(
            title="Connected Devices",
            description="Scan, pair, and connect your Gear S3 via Wi-Fi IP address. View real-time device battery, Tizen version, and kernel details.",
            icon="⌚"
        )
        card_devices.clicked.connect(lambda: self.request_page_change.emit(1)) # Switches to DevicePage (Index 1)

        # Card 2: File Explorer
        card_files = DashboardCard(
            title="File Explorer",
            description="Explore the directory tree of your watch. Upload files, download logs, and manage storage spaces effortlessly.",
            icon="📂"
        )
        card_files.clicked.connect(lambda: self.request_page_change.emit(2)) # Switches to FilesPage (Index 2)

        # Card 3: Shell Terminal
        card_terminal = DashboardCard(
            title="SDB Terminal",
            description="Directly execute SDB shell commands on Tizen OS. Ideal for advanced developers and custom debugging.",
            icon="💻"
        )
        card_terminal.clicked.connect(lambda: self.request_page_change.emit(3)) # Switches to TerminalPage (Index 3)

        # Card 4: Sideload Apps
        card_sideload = DashboardCard(
            title="Sideload TPKs",
            description="Easily install compiled Tizen application packages (.tpk) such as custom widgets or watch faces directly onto your Gear S3.",
            icon="📦"
        )
        card_sideload.clicked.connect(lambda: self.request_page_change.emit(4)) # Switches to SideloadPage (Index 4)

        # Put them in a 2x2 layout
        grid.addWidget(card_devices, 0, 0)
        grid.addWidget(card_files, 0, 1)
        grid.addWidget(card_terminal, 1, 0)
        grid.addWidget(card_sideload, 1, 1)

        layout.addLayout(grid)
        layout.addStretch()

        # Update the connection banner on startup
        self.update_connection_status()

    def update_connection_status(self):
        """Checks if a watch is currently connected and updates the status banner."""
        try:
            connected_devices = self.sdb.devices()
            if connected_devices:
                watch = connected_devices[0]
                self.status_indicator.setText(f"🟢 Connected: {watch.name} ({watch.ip}:{watch.port})")
                self.status_indicator.setStyleSheet("font-size: 14px; font-weight: bold; color: #1b8a5a;")
            else:
                self.status_indicator.setText("🔴 No Active Connections. Head to 'Connected Devices' to connect.")
                self.status_indicator.setStyleSheet("font-size: 14px; font-weight: bold; color: #ff3333;")
        except Exception:
            self.status_indicator.setText("🔴 SDB Connection Error. Is SDB running?")
            self.status_indicator.setStyleSheet("font-size: 14px; font-weight: bold; color: #ff3333;")