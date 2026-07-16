from PySide6.QtWidgets import (
    QMainWindow,
    QLabel,
    QStatusBar,
)

from core.sdb import SDBManager


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Window Settings
        self.setWindowTitle("GearS3 Explorer")
        self.resize(1300, 800)

        # Create the SDB Manager
        self.manager = SDBManager()

        # Test a shell command
        success, output = self.manager.shell("uname -r")

        if success:
            text = (
                "🟢 Connected!\n\n"
                f"Kernel Version:\n{output}"
            )
        else:
            text = (
                "🔴 Failed to connect.\n\n"
                f"{output}"
            )

        # Main Label
        self.label = QLabel(text)
        self.label.setStyleSheet("""
            font-size:18px;
            padding:20px;
        """)

        self.setCentralWidget(self.label)

        # Status Bar
        self.status = QStatusBar()
        self.status.showMessage("Ready")
        self.setStatusBar(self.status)
