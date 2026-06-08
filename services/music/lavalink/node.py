from dataclasses import dataclass


@dataclass
class LavalinkNodeConfig:
    host: str
    port: int
    password: str
    identifier: str = "main"
    secure: bool = False


class LavalinkNode:
    """
    Represents a single Lavalink node connection config.

    Actual websocket client will be plugged in later
    (e.g. wavelink / lavalink-py / erela.js equivalent).
    """

    def __init__(self, config: LavalinkNodeConfig):
        self.config = config
        self.connected = False

    async def connect(self):
        # Placeholder: real websocket connection later
        self.connected = True

    async def disconnect(self):
        self.connected = False

    def is_available(self) -> bool:
        return self.connected