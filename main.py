import sys
from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow

def main():
    # Initialize the PySide6 Application
    app = QApplication(sys.argv)

    # Create and show the main UI window
    window = MainWindow()
    window.show()

    # Start the application event loop
    sys.exit(app.exec())

if __name__ == "__main__":
    main()