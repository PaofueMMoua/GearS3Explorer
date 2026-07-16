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
        Runs an SDB command and returns:
        (return_code, stdout, stderr)
        """
        result = subprocess.run(
            [str(self.sdb)] + args,
            capture_output=True,
            text=True,
        )

        return (
            result.returncode,
            result.stdout.strip(),
            result.stderr.strip(),
        )

    def devices(self):
        """
        Returns a list of connected Device objects.
        """
        code, stdout, stderr = self._run(["devices"])

        if code != 0:
            return []

        devices = []

        for line in stdout.splitlines():

            # Skip header line
            if line.startswith("List of devices"):
                continue

            if ":" not in line:
                continue

            ip_port = line.split()[0]
            ip, port = ip_port.split(":")

            devices.append(
                Device(
                    name="SM-R760",
                    ip=ip,
                    port=int(port),
                    connected=True,
                    tizen_version="Unknown",
                    kernel="Unknown",
                    cpu="Unknown",
                    ram="Unknown",
                    storage="Unknown",
                    battery="Unknown",
                )
            )

        return devices

    def shell(self, command: str):
        """
        Runs an SDB shell command.
        Returns:
            (success, output)
        """
        code, stdout, stderr = self._run(["shell", command])

        if code == 0:
            return True, stdout

        return False, stderr