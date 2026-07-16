from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, 
    QTableWidgetItem, QPushButton, QGroupBox, QLabel, 
    QFormLayout, QHeaderView, QLineEdit, QMessageBox
)
from PySide6.QtCore import Qt
from core.sdb import SDBManager
from core.workers import NetworkScanWorker

class DevicePage(QWidget):
    def __init__(self, sdb_manager: SDBManager = None):
        super().__init__()
        self.sdb = sdb_manager if sdb_manager else SDBManager()
        self.scan_worker = None # Track the active network scanner background task
        
        self.init_ui()
        self.scan_devices()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        # 1. Title and Header Row
        header_layout = QHBoxLayout()
        title = QLabel("Connected Devices")
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        
        self.btn_scan = QPushButton("🔄 Refresh List")
        self.btn_scan.setFixedWidth(120)
        self.btn_scan.clicked.connect(self.scan_devices)
        
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(self.btn_scan)
        layout.addLayout(header_layout)

        # 2. Wi-Fi Manual & Auto-Discovery Connection Bar
        conn_box = QGroupBox("Connect to Watch via Wi-Fi")
        conn_layout = QHBoxLayout(conn_box)
        
        self.ip_input = QLineEdit()
        self.ip_input.setPlaceholderText("Enter Watch IP Address (e.g., 192.168.1.15)")
        self.ip_input.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border: 1px solid #2d2d35;
                border-radius: 4px;
                background-color: #1e1e24;
                color: white;
            }
        """)
        self.ip_input.returnPressed.connect(self.connect_to_watch)

        self.btn_connect = QPushButton("⚡ Connect")
        self.btn_connect.setFixedWidth(100)
        self.btn_connect.setStyleSheet("""
            QPushButton {
                background-color: #2b5c8f;
                color: white;
                font-weight: bold;
                border-radius: 4px;
                padding: 7px;
            }
            QPushButton:hover {
                background-color: #3a75b5;
            }
        """)
        self.btn_connect.clicked.connect(self.connect_to_watch)

        # NEW: Auto-Scan / Discover Button
        self.btn_auto_discover = QPushButton("🔍 Auto-Discover")
        self.btn_auto_discover.setFixedWidth(130)
        self.btn_auto_discover.setStyleSheet("""
            QPushButton {
                background-color: #1b8a5a;
                color: white;
                font-weight: bold;
                border-radius: 4px;
                padding: 7px;
            }
            QPushButton:hover {
                background-color: #23aa70;
            }
        """)
        self.btn_auto_discover.clicked.connect(self.start_auto_discovery)

        conn_layout.addWidget(self.ip_input)
        conn_layout.addWidget(self.btn_connect)
        conn_layout.addWidget(self.btn_auto_discover)
        layout.addWidget(conn_box)

        # 3. Main Content Split
        content_layout = QHBoxLayout()
        
        # Device Table
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["IP Address", "Port", "Status"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.cellClicked.connect(self.on_device_selected)
        content_layout.addWidget(self.table, stretch=3)

        # Details Panel
        self.details_box = QGroupBox("Device Information")
        details_layout = QFormLayout(self.details_box)
        
        self.lbl_name = QLabel("N/A")
        self.lbl_tizen = QLabel("N/A")
        self.lbl_kernel = QLabel("N/A")
        self.lbl_battery = QLabel("N/A")
        
        details_layout.addRow("Model Name:", self.lbl_name)
        details_layout.addRow("Tizen OS Version:", self.lbl_tizen)
        details_layout.addRow("Kernel Version:", self.lbl_kernel)
        details_layout.addRow("Battery Status:", self.lbl_battery)
        
        content_layout.addWidget(self.details_box, stretch=2)
        layout.addLayout(content_layout)

    def connect_to_watch(self):
        """Attempts to connect to the IP input manually."""
        ip = self.ip_input.text().strip()
        if not ip:
            QMessageBox.warning(self, "Input Required", "Please enter your watch's IP address first.")
            return

        self.btn_connect.setText("Connecting...")
        self.btn_connect.setEnabled(False)

        success, message = self.sdb.connect(ip)

        self.btn_connect.setText("⚡ Connect")
        self.btn_connect.setEnabled(True)

        if success:
            QMessageBox.information(self, "Success", f"Successfully connected to the watch!\n\n{message}")
            self.scan_devices()
        else:
            QMessageBox.critical(self, "Connection Failed", f"Failed to connect to watch.\n\nError/Output:\n{message}")

    # --- Auto-Discovery Logic ---

    def start_auto_discovery(self):
        """Spawns the fast concurrent background thread to find the watch."""
        self.btn_auto_discover.setText("Scanning...")
        self.btn_auto_discover.setEnabled(False)
        self.ip_input.setPlaceholderText("Scanning network for your watch...")

        self.scan_worker = NetworkScanWorker(self.sdb)
        self.scan_worker.finished.connect(self.on_discovery_finished)
        self.scan_worker.start()

    def on_discovery_finished(self, found_ips: list):
        """Fires when the scan worker thread finishes."""
        self.btn_auto_discover.setText("🔍 Auto-Discover")
        self.btn_auto_discover.setEnabled(True)
        self.ip_input.setPlaceholderText("Enter Watch IP Address (e.g., 192.168.1.15)")

        if not found_ips:
            QMessageBox.warning(
                self, 
                "No Devices Found", 
                "Could not find any Gear S3 on your local network.\n\n"
                "Please make sure SDB Debugging is turned ON on your watch, and that "
                "both your PC and watch are on the same Wi-Fi network."
            )
            return

        # If we found at least one device, try to connect to it automatically
        target_ip = found_ips[0]
        self.ip_input.setText(target_ip)
        
        # Connect to the discovered IP
        success, message = self.sdb.connect(target_ip)
        if success:
            QMessageBox.information(
                self, 
                "Watch Found!", 
                f"Discovered and successfully connected to the watch at:\nIP: {target_ip}\n\nMake sure to allow debugging on your watch display if prompted."
            )
            self.scan_devices()
        else:
            QMessageBox.critical(
                self, 
                "Connection Error", 
                f"Discovered watch at {target_ip}, but failed to connect.\n\nOutput: {message}"
            )

    def scan_devices(self):
        """Scans for active SDB connections and updates the table."""
        self.table.setRowCount(0)
        self.clear_details()
        
        devices = self.sdb.devices()
        
        for device in devices:
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            ip_item = QTableWidgetItem(device.ip)
            port_item = QTableWidgetItem(str(device.port))
            status_item = QTableWidgetItem("🟢 Connected" if device.connected else "🔴 Disconnected")
            
            ip_item.setData(Qt.UserRole, device)
            
            self.table.setItem(row, 0, ip_item)
            self.table.setItem(row, 1, port_item)
            self.table.setItem(row, 2, status_item)

    def on_device_selected(self):
        row = self.table.currentRow()
        if row < 0:
            self.clear_details()
            return
            
        ip_item = self.table.item(row, 0)
        if ip_item:
            device = ip_item.data(Qt.UserRole)
            if device:
                self.lbl_name.setText(str(device.name))
                self.lbl_tizen.setText(str(device.tizen_version))
                self.lbl_kernel.setText(str(device.kernel))
                self.lbl_battery.setText(str(device.battery))

    def clear_details(self):
        self.lbl_name.setText("N/A")
        self.lbl_tizen.setText("N/A")
        self.lbl_kernel.setText("N/A")
        self.lbl_battery.setText("N/A")