from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QLineEdit, QPushButton, QLabel
from PySide6.QtCore import Qt
from core.sdb import SDBManager
from core.workers import SDBCommandWorker

class TerminalPage(QWidget):
    def __init__(self, sdb_manager: SDBManager = None):
        super().__init__()
        self.sdb = sdb_manager if sdb_manager else SDBManager()
        self.worker = None # To track active background task

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        # Title
        title = QLabel("SDB Interactive Terminal (Threaded)")
        title.setStyleSheet("font-size: 20px; font-weight: bold; margin-bottom: 5px;")
        layout.addWidget(title)

        # Command Output Box
        self.output_box = QTextEdit()
        self.output_box.setReadOnly(True)
        self.output_box.setStyleSheet("""
            QTextEdit {
                background-color: #121214;
                color: #00ff66;
                font-family: 'Courier New', monospace;
                font-size: 13px;
                border: 1px solid #2d2d35;
                border-radius: 4px;
                padding: 10px;
            }
        """)
        self.output_box.append("Welcome to GearS3 Terminal. Running commands in background threads...\n")
        layout.addWidget(self.output_box)

        # Command Input
        input_layout = QHBoxLayout()
        
        self.input_line = QLineEdit()
        self.input_line.setPlaceholderText("Enter shell command...")
        self.input_line.setStyleSheet("""
            QLineEdit {
                background-color: #1e1e24;
                color: #ffffff;
                font-family: 'Courier New', monospace;
                border: 1px solid #2d2d35;
                padding: 8px;
                border-radius: 4px;
            }
        """)
        self.input_line.returnPressed.connect(self.run_command)
        
        self.btn_send = QPushButton("Execute")
        self.btn_send.setFixedWidth(100)
        self.btn_send.clicked.connect(self.run_command)

        input_layout.addWidget(self.input_line)
        input_layout.addWidget(self.btn_send)
        layout.addLayout(input_layout)

    def run_command(self):
        command = self.input_line.text().strip()
        if not command:
            return

        # Show that we are executing
        self.output_box.append(f"\n$ {command}")
        self.input_line.clear()
        
        # Disable inputs so user doesn't spam commands while one is running
        self.set_controls_enabled(False)

        # Create and start the background thread
        self.worker = SDBCommandWorker(self.sdb, command)
        self.worker.finished.connect(self.on_command_finished)
        self.worker.start() # Runs the thread

    def on_command_finished(self, success, output):
        """Called automatically when the background thread finishes."""
        if output:
            self.output_box.append(output)
        else:
            self.output_box.append("[No Output]")
            
        self.output_box.ensureCursorVisible()
        
        # Re-enable inputs
        self.set_controls_enabled(True)
        self.worker = None

    def set_controls_enabled(self, enabled: bool):
        self.input_line.setEnabled(enabled)
        self.btn_send.setEnabled(enabled)
        if not enabled:
            self.btn_send.setText("Running...")
        else:
            self.btn_send.setText("Execute")