from core.sdb import SDBManager


class TerminalManager:
    def __init__(self):
        self.sdb = SDBManager()

    def execute(self, command: str):
        return self.sdb.shell(command)