import socket
from concurrent.futures import ThreadPoolExecutor
from PySide6.QtCore import QThread, Signal
from core.sdb import SDBManager

# --- FIX: Added the missing SDBCommandWorker class for terminal_page.py ---
class SDBCommandWorker(QThread):
    """
    Asynchronously runs an SDB shell command so the terminal UI doesn't hang.
    """
    finished = Signal(bool, str)  # Emits (success, output)

    def __init__(self, command: str, sdb_manager: SDBManager = None):
        super().__init__()
        self.command = command
        self.sdb = sdb_manager if sdb_manager else SDBManager()

    def run(self):
        success, output = self.sdb.shell(self.command)
        self.finished.emit(success, output)


class NetworkScanWorker(QThread):
    """
    Scans the local network subnet for any devices listening on port 26101 (SDB).
    Emits a list of discovered IP addresses when done.
    """
    progress = Signal(str)      
    finished = Signal(list)     

    def __init__(self, sdb_manager: SDBManager):
        super().__init__()
        self.sdb = sdb_manager
        self.port = 26101

    def get_local_ip(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(('10.255.255.255', 1))
            ip = s.getsockname()[0]
        except Exception:
            ip = '127.0.0.1'
        finally:
            s.close()
        return ip

    def check_ip_port(self, ip):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(0.3)
                result = s.connect_ex((ip, self.port))
                if result == 0:
                    return ip
        except Exception:
            pass
        return None

    def run(self):
        local_ip = self.get_local_ip()
        if local_ip == '127.0.0.1':
            self.finished.emit([])
            return

        parts = local_ip.split('.')
        subnet = ".".join(parts[:3]) + "."

        self.progress.emit(f"Scanning subnet {subnet}0/24...")

        discovered_ips = []
        ip_list = [f"{subnet}{i}" for i in range(1, 255)]

        with ThreadPoolExecutor(max_workers=50) as executor:
            results = executor.map(self.check_ip_port, ip_list)
            for res in results:
                if res:
                    discovered_ips.append(res)

        self.finished.emit(discovered_ips)

class SideloadWorker(QThread):
    """
    Handles .tpk installation in a background thread to prevent UI freezing.
    """
    finished = Signal(bool, str)  # Emits (success, message)

    def __init__(self, tpk_path: str, sdb_manager: SDBManager = None):
        super().__init__()
        self.tpk_path = tpk_path
        self.sdb = sdb_manager if sdb_manager else SDBManager()

    def run(self):
        success, message = self.sdb.install_app(self.tpk_path)
        self.finished.emit(success, message)