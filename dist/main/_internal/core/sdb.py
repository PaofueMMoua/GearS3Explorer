import subprocess
from pathlib import Path
from core.devices import Device

class SDBManager:
    def __init__(self):
        self.sdb = (
            Path.home()
            / ".tizen-extension-platform"
            / "server"
            / "sdktools"
            / "data"
            / "tools"
            / "sdb.exe"
        )

    def _run(self, args: list[str]):
        """
        Runs an SDB command silently in the background without spawning console windows.
        """
        import sys
        
        # Windows-specific flag to completely hide the cmd window spawned by subprocess
        creationflags = 0
        if sys.platform == "win32":
            creationflags = subprocess.CREATE_NO_WINDOW  # Equivalent to 0x08000000

        result = subprocess.run(
            [str(self.sdb)] + args,
            capture_output=True,
            text=True,
            creationflags=creationflags  # Forces the command to run invisibly
        )
        return (
            result.returncode,
            result.stdout.strip(),
            result.stderr.strip(),
        )

    def connect(self, ip: str):
        """Connects to a Gear S3 device over Wi-Fi."""
        ip_address = ip.strip()
        if ":" not in ip_address:
            ip_address = f"{ip_address}:26101"

        code, stdout, stderr = self._run(["connect", ip_address])
        if code == 0 and ("connected to" in stdout.lower() or "already connected" in stdout.lower()):
            return True, stdout
        return False, stderr or stdout

    def shell(self, command: str):
        """Runs an SDB shell command. Returns: (success, output)"""
        code, stdout, stderr = self._run(["shell", command])
        if code == 0:
            return True, stdout
        return False, stderr

    def devices(self):
        """Returns a list of connected Device objects with actual Tizen shell stats."""
        code, stdout, stderr = self._run(["devices"])
        if code != 0:
            return []

        devices = []

        for line in stdout.splitlines():
            if line.startswith("List of devices") or ":" not in line:
                continue

            ip_port = line.split()[0]
            ip, port = ip_port.split(":")

            # --- Tizen Native Hardware Queries (Bypassing Android's getprop) ---

            # 1. Model Name
            model = "Gear S3 (SM-R760)"
            # Querying vconf directly avoids getprop issues
            success, val = self.shell("vconf-get db/system/model")
            if success and val.strip() and "error" not in val.lower() and "found" not in val.lower():
                model = val.strip()

            # 2. Tizen OS Version
            tizen_version = "Tizen 3.0.0"
            success, val = self.shell("cat /etc/tizen-release")
            if success and val.strip():
                for rline in val.splitlines():
                    if "VERSION" in rline or "Tizen" in rline:
                        tizen_version = rline.replace("VERSION =", "").strip()
                        break

            # 3. Kernel Version
            kernel = "Linux Kernel"
            success, val = self.shell("uname -r")
            if success and val.strip():
                kernel = val.strip()

            # 4. Battery Level
            battery = "100%"
            success, val = self.shell("vconf-get db/system/battery_level")
            if success and val.strip().isdigit():
                battery = f"{val.strip()}%"
            else:
                # Fallback to sysfs direct path
                success, val = self.shell("cat /sys/class/power_supply/battery/capacity")
                if success and val.strip().isdigit():
                    battery = f"{val.strip()}%"

            # Clean up carriage returns
            model = model.replace("\r", "")
            tizen_version = tizen_version.replace("\r", "")
            kernel = kernel.replace("\r", "")
            battery = battery.replace("\r", "")

            devices.append(
                Device(
                    name=model,
                    ip=ip,
                    port=int(port),
                    connected=True,
                    tizen_version=tizen_version,
                    kernel=kernel,
                    cpu="Exynos 7270",
                    ram="768 MB",
                    storage="4 GB",
                    battery=battery,
                )
            )

        return devices
    
    def install_app(self, local_path: str):
        """
        Installs a Tizen app package (.tpk or .wgt) onto the Gear S3.
        """
        local_path_str = str(local_path)
        
        # --- Handle .wgt (Web Widget/App) Files ---
        if local_path_str.lower().endswith(".wgt"):
            import os
            filename = os.path.basename(local_path_str)
            remote_path = f"/tmp/{filename}"
            
            # 1. Push the .wgt file to the watch's temp directory
            push_code, stdout_p, stderr_p = self._run(["push", local_path_str, remote_path])
            if push_code != 0:
                return False, f"Failed to push .wgt to watch:\n{stderr_p or stdout_p}"
                
            # 2. Run the native Tizen package manager to install it
            install_cmd = f"pkgcmd -i -t wgt -p {remote_path}"
            success, install_output = self.shell(install_cmd)
            
            # Clean up the pushed file from /tmp to save storage space
            self.shell(f"rm {remote_path}")
            
            # Robust verification check:
            # If sdb shell returned True (exit code 0) and the output does not contain 
            # explicit failure keywords, we count it as a success!
            out_lower = install_output.lower()
            has_error = "error" in out_lower or "failed" in out_lower or "fail" in out_lower
            
            if success and not has_error:
                return True, f"Web app installed successfully!\n\nShell Output:\n{install_output}"
            return False, f"Web app installation failed.\n\nShell Output:\n{install_output}"

        # --- Handle Standard .tpk Files ---
        code, stdout, stderr = self._run(["install", local_path_str])
        output = stdout.lower() + " " + stderr.lower()
        if code == 0 and ("installed" in output or "success" in output):
            return True, stdout
        return False, stderr or stdout