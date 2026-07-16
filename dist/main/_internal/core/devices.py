from dataclasses import dataclass

@dataclass
class Device:
    name: str
    ip: str
    port: int
    connected: bool

    tizen_version: str
    kernel: str
    cpu: str
    ram: str
    storage: str
    battery: str