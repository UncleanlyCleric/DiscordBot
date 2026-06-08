import os
import wavelink


class LavalinkClient:
    """
    Global Lavalink connection manager using Wavelink.
    """

    def __init__(self):
        self.node = None

    async def connect(self, bot):
        """
        Connect bot to Lavalink node.
        """

        host = os.getenv("LAVALINK_HOST", "localhost")
        port = int(os.getenv("LAVALINK_PORT", 2333))
        password = os.getenv("LAVALINK_PASSWORD", "youshallnotpass")

        nodes = [
            wavelink.Node(
                uri=f"http://{host}:{port}",
                password=password
            )
        ]

        await wavelink.Pool.connect(
            client=bot,
            nodes=nodes
        )

        self.node = nodes[0]

    def is_ready(self) -> bool:
        return self.node is not None


lava_client = LavalinkClient()