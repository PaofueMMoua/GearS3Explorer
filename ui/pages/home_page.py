from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout


class HomePage(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout()

        title = QLabel("Welcome to GearS3 Explorer")
        title.setStyleSheet("""
            font-size: 28px;
            font-weight: bold;
        """)

        subtitle = QLabel(
            "Select a page from the sidebar to begin."
        )

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addStretch()

        self.setLayout(layout)