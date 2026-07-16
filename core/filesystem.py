import re
from core.sdb import SDBManager

class FilesystemManager:
    def __init__(self, sdb_manager: SDBManager):
        self.sdb = sdb_manager
        self.current_path = "/"

    def list_directory(self, path: str) -> list[dict]:
        """
        Runs 'ls -al' via SDB shell and parses the output.
        Returns a list of dictionaries representing files/folders.
        """
        # Ensure path is absolute and clean
        if not path.startswith("/"):
            path = "/" + path
        
        # We use -a to see hidden files, -l for details
        success, output = self.sdb.shell(f"ls -al {path}")
        if not success:
            return []

        items = []
        lines = output.splitlines()

        for line in lines:
            line = line.strip()
            if not line or line.startswith("total"):
                continue

            # Regex to parse standard Linux 'ls -l' output
            # Matches: permissions, links, owner, group, size, date, name
            match = re.match(
                r"^([d\-rwxstT\+]+)\s+(\d+)\s+(\w+)\s+(\w+)\s+(\d+)\s+([\w\s:-]+)\s+(.+)$", 
                line
            )
            if match:
                perms, _, owner, group, size, date, name = match.groups()
                
                # Skip current and parent directory pointers to keep UI navigation clean
                if name in [".", ".."]:
                    continue

                is_dir = perms.startswith("d")
                
                items.append({
                    "name": name,
                    "is_dir": is_dir,
                    "size": int(size) if not is_dir else 0,
                    "permissions": perms,
                    "owner": owner,
                    "date": date,
                    "path": f"{path.rstrip('/')}/{name}"
                })

        # Sort: directories first, then files alphabetically
        items.sort(key=lambda x: (not x["is_dir"], x["name"].lower()))
        return items

    def get_parent_directory(self, path: str) -> str:
        """Returns the parent directory path, stopping at '/'."""
        if path == "/":
            return "/"
        parts = path.rstrip("/").split("/")
        parts.pop()
        parent = "/".join(parts)
        return parent if parent else "/"