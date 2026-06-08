from typing import Dict, Optional

from services.music.lavalink.node import LavalinkNode, LavalinkNodeConfig


class LavalinkManager:
    """
    Manages multiple Lavalink nodes.

    Future-ready for:
    - load balancing
    - failover
    - regional nodes
    """

    def __init__(self):
        self.nodes: Dict[str, LavalinkNode] = {}
        self.active: Optional[str] = None

    def add_node(self, config: LavalinkNodeConfig):
        node = LavalinkNode(config)
        self.nodes[config.identifier] = node

        if not self.active:
            self.active = config.identifier

    async def connect_all(self):
        for node in self.nodes.values():
            await node.connect()

    def get_active(self) -> Optional[LavalinkNode]:
        if not self.active:
            return None
        return self.nodes.get(self.active)

    def switch_node(self, identifier: str):
        if identifier in self.nodes:
            self.active = identifier


lava_manager = LavalinkManager()