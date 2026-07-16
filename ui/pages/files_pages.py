import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, 
    QTableWidgetItem, QPushButton, QLineEdit, QHeaderView,
    QMenu, QFileDialog, QMessageBox
)
from PySide6.QtCore import Qt, QPoint
from core.sdb import SDBManager
from core.filesystem import FilesystemManager

class FilesPage(QWidget):
    def __init__(self, sdb_manager: SDBManager = None):
        super().__init__()
        
        self.sdb = sdb_manager if sdb_manager else SDBManager()
        self.fs = FilesystemManager(self.sdb)
        self.current_path = "/"

        self.init_ui()
        self.load_directory(self.current_path)

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        # 1. Navigation & Actions Header Row
        nav_layout = QHBoxLayout()
        
        self.btn_back = QPushButton("⬅ Up")
        self.btn_back.setFixedWidth(60)
        self.btn_back.clicked.connect(self.navigate_up)
        
        self.path_input = QLineEdit(self.current_path)
        self.path_input.returnPressed.connect(self.navigate_to_input_path)
        
        self.btn_refresh = QPushButton("🔄 Refresh")
        self.btn_refresh.setFixedWidth(80)
        self.btn_refresh.clicked.connect(lambda: self.load_directory(self.current_path))

        # NEW: Global Upload Button
        self.btn_upload = QPushButton("📤 Upload File")
        self.btn_upload.setFixedWidth(110)
        self.btn_upload.setStyleSheet("""
            QPushButton {
                background-color: #2b5c8f;
                color: white;
                font-weight: bold;
                border-radius: 4px;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #3a75b5;
            }
        """)
        self.btn_upload.clicked.connect(self.upload_file)

        nav_layout.addWidget(self.btn_back)
        nav_layout.addWidget(self.path_input)
        nav_layout.addWidget(self.btn_refresh)
        nav_layout.addWidget(self.btn_upload) # Add upload button to the header
        layout.addLayout(nav_layout)

        # 2. File Table
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Name", "Type", "Size (KB)", "Permissions"])
        
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.doubleClicked.connect(self.on_item_double_clicked)
        
        # Enable Right-Click Context Menu
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)
        
        layout.addWidget(self.table)

    def load_directory(self, path: str):
        """Fetches directory contents and populates the table."""
        self.current_path = path
        self.path_input.setText(path)
        self.table.setRowCount(0)
        
        items = self.fs.list_directory(path)
        
        for item in items:
            row = self.table.rowCount()
            self.table.insertRow(row)

            name_text = f"📁 {item['name']}" if item['is_dir'] else f"📄 {item['name']}"
            name_item = QTableWidgetItem(name_text)
            name_item.setData(Qt.UserRole, item) 

            type_text = "Folder" if item['is_dir'] else "File"
            size_kb = f"{round(item['size'] / 1024, 2)} KB" if not item['is_dir'] else ""
            
            self.table.setItem(row, 0, name_item)
            self.table.setItem(row, 1, QTableWidgetItem(type_text))
            self.table.setItem(row, 2, QTableWidgetItem(size_kb))
            self.table.setItem(row, 3, QTableWidgetItem(item['permissions']))

    def on_item_double_clicked(self, index):
        """Triggers on double-click; navigates deeper into folders."""
        name_item = self.table.item(index.row(), 0)
        item_data = name_item.data(Qt.UserRole)

        if item_data and item_data["is_dir"]:
            self.load_directory(item_data["path"])

    def navigate_up(self):
        parent = self.fs.get_parent_directory(self.current_path)
        self.load_directory(parent)

    def navigate_to_input_path(self):
        path = self.path_input.text().strip()
        self.load_directory(path)

    # --- File Upload & Download Logic ---

    def show_context_menu(self, position: QPoint):
        """Builds a right-click menu based on where the user clicks."""
        menu = QMenu(self)
        selected_item = self.table.itemAt(position)
        
        # You can always upload to the current folder
        upload_action = menu.addAction("📤 Upload File Here")
        download_action = None

        # If they right-clicked an actual row item, let them download it
        if selected_item:
            row = self.table.row(selected_item)
            name_item = self.table.item(row, 0)
            item_data = name_item.data(Qt.UserRole)
            
            if item_data and not item_data["is_dir"]:
                download_action = menu.addAction("📥 Download File")

        # Display the menu
        action = menu.exec(self.table.mapToGlobal(position))
        
        if action == upload_action:
            self.upload_file()
        elif download_action and action == download_action:
            self.download_file(item_data)

    def upload_file(self):
        """Pops open a file picker to select a local file, then pushes it to the watch."""
        local_filepath, _ = QFileDialog.getOpenFileName(self, "Select File to Upload")
        if not local_filepath:
            return  # User cancelled

        filename = os.path.basename(local_filepath)
        # Construct path: ensuring we don't double-slash the root directory
        if self.current_path == "/":
            remote_filepath = f"/{filename}"
        else:
            remote_filepath = f"{self.current_path}/{filename}"

        # Inform the user in the UI (this will pause UI, but keeps it simple)
        self.btn_upload.setText("Uploading...")
        self.btn_upload.setEnabled(False)
        
        # Execute push
        success, stdout, stderr = self.sdb.push(local_filepath, remote_filepath)
        
        self.btn_upload.setText("📤 Upload File")
        self.btn_upload.setEnabled(True)

        if success:
            QMessageBox.information(self, "Upload Successful", f"Uploaded:\n{filename}\n\nTo:\n{remote_filepath}")
            self.load_directory(self.current_path) # Refresh view
        else:
            QMessageBox.critical(self, "Upload Failed", f"Could not upload file.\n\nError:\n{stderr or stdout}")

    def download_file(self, item_data: dict):
        """Pops open a destination dialog to pull a file from the watch."""
        remote_filepath = item_data["path"]
        filename = item_data["name"]

        local_filepath, _ = QFileDialog.getSaveFileName(self, "Save File As", filename)
        if not local_filepath:
            return

        success, stdout, stderr = self.sdb.pull(remote_filepath, local_filepath)
        if success:
            QMessageBox.information(self, "Download Successful", f"Successfully saved file to:\n{local_filepath}")
        else:
            QMessageBox.critical(self, "Download Failed", f"Could not download file.\n\nError:\n{stderr or stdout}")