import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFileDialog, QMessageBox, QFrame, QProgressBar
)
from PySide6.QtCore import Qt
from core.sdb import SDBManager
from core.workers import SideloadWorker

class SideloadPage(QWidget):
    def __init__(self, sdb_manager: SDBManager = None):
        super().__init__()
        self.sdb = sdb_manager if sdb_manager else SDBManager()
        self.selected_tpk = None
        self.worker = None

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        # 1. Header
        title = QLabel("Sideload Tizen Applications")
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: #ffffff;")
        subtitle = QLabel("Install custom widget and watch face packages (.tpk) directly onto your Gear S3.")
        subtitle.setStyleSheet("font-size: 13px; color: #b3b3b3;")
        
        layout.addWidget(title)
        layout.addWidget(subtitle)

        # 2. File Selection Zone (Visual Box)
        self.drop_zone = QFrame()
        self.drop_zone.setFrameShape(QFrame.StyledPanel)
        self.drop_zone.setStyleSheet("""
            QFrame {
                background-color: #1e1e24;
                border: 2px dashed #3a75b5;
                border-radius: 8px;
                min-height: 180px;
            }
        """)
        
        zone_layout = QVBoxLayout(self.drop_zone)
        zone_layout.setAlignment(Qt.AlignCenter)
        
        self.icon_lbl = QLabel("📦")
        self.icon_lbl.setStyleSheet("font-size: 48px; background: transparent;")
        self.icon_lbl.setAlignment(Qt.AlignCenter)
        
        self.info_lbl = QLabel("No .tpk file selected")
        self.info_lbl.setStyleSheet("font-size: 14px; font-weight: bold; color: #b3b3b3; background: transparent;")
        self.info_lbl.setAlignment(Qt.AlignCenter)

        self.btn_browse = QPushButton("Browse Files")
        self.btn_browse.setFixedWidth(120)
        self.btn_browse.setStyleSheet("""
            QPushButton {
                background-color: #2b5c8f;
                color: white;
                font-weight: bold;
                border-radius: 4px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: #3a75b5;
            }
        """)
        self.btn_browse.clicked.connect(self.browse_tpk)

        zone_layout.addWidget(self.icon_lbl)
        zone_layout.addWidget(self.info_lbl)
        zone_layout.addWidget(self.btn_browse)
        
        layout.addWidget(self.drop_zone)

        # 3. Bottom Controls & Feedback Area
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #2d2d35;
                border-radius: 4px;
                text-align: center;
                background-color: #16161a;
                color: white;
            }
            QProgressBar::chunk {
                background-color: #1b8a5a;
            }
        """)
        layout.addWidget(self.progress_bar)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.btn_install = QPushButton("⚡ Start Install")
        self.btn_install.setEnabled(False) # Wait for file selection
        self.btn_install.setFixedWidth(140)
        self.btn_install.setStyleSheet("""
            QPushButton {
                background-color: #1b8a5a;
                color: white;
                font-weight: bold;
                border-radius: 4px;
                padding: 10px;
            }
            QPushButton:disabled {
                background-color: #2d2d35;
                color: #555555;
            }
            QPushButton:hover:enabled {
                background-color: #23aa70;
            }
        """)
        self.btn_install.clicked.connect(self.start_install)
        
        btn_layout.addWidget(self.btn_install)
        layout.addLayout(btn_layout)
        layout.addStretch()

    def browse_tpk(self):
        """Opens file selection dialog supporting both .tpk and .wgt files."""
        filepath, _ = QFileDialog.getOpenFileName(
            self, 
            "Select Tizen App Package", 
            "", 
            "Tizen Packages (*.tpk *.wgt);;Native Packages (*.tpk);;Web Packages (*.wgt)"
        )
        if filepath:
            self.selected_tpk = filepath
            filename = os.path.basename(filepath)
            self.info_lbl.setText(f"Ready to install:\n{filename}")
            self.info_lbl.setStyleSheet("font-size: 14px; font-weight: bold; color: #ffffff; background: transparent;")
            self.btn_install.setEnabled(True)

    def start_install(self):
        """Begins sideload task on a background thread."""
        if not self.selected_tpk:
            return

        # Double check that we actually have a device connected first
        if not self.sdb.devices():
            QMessageBox.critical(self, "No Device", "Please connect to your Gear S3 on the Devices page first!")
            return

        self.btn_browse.setEnabled(False)
        self.btn_install.setEnabled(False)
        
        # Setup Progress UI
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0) # Smooth loading indicator (marquee)
        self.info_lbl.setText("Installing app onto your Gear S3...\nPlease check your watch face for installation prompts.")

        # Fire off Background Thread
        self.worker = SideloadWorker(self.selected_tpk, self.sdb)
        self.worker.finished.connect(self.on_install_completed)
        self.worker.start()

    def on_install_completed(self, success: bool, message: str):
        """Executes once the installation background task completes."""
        self.btn_browse.setEnabled(True)
        self.btn_install.setEnabled(True)
        self.progress_bar.setVisible(False)

        if success:
            QMessageBox.information(self, "Success!", f"The application was successfully installed!\n\nDetails:\n{message}")
            self.info_lbl.setText("No .tpk file selected")
            self.info_lbl.setStyleSheet("font-size: 14px; font-weight: bold; color: #b3b3b3; background: transparent;")
            self.selected_tpk = None
            self.btn_install.setEnabled(False)
        else:
            QMessageBox.critical(self, "Sideload Failed", f"Installation failed.\n\nError output:\n{message}")
            self.info_lbl.setText("Installation failed. Try again.")
            self.info_lbl.setStyleSheet("font-size: 14px; font-weight: bold; color: #ff3333; background: transparent;")