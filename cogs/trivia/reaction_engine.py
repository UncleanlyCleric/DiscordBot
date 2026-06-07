import time
import random
from .reactions import HOST_REACTIONS


class HostReactionEngine:
    def __init__(self, host_name: str):
        self.host_name = host_name

    def react(self, event: str, context=None):
        host = HOST_REACTIONS.get(self.host_name, HOST_REACTIONS["snark"])

        pool = host.get(event, host["wrong"])
        return random.choice(pool)

    def evaluate_timing(self, start_time: float, is_correct: bool):
        elapsed = time.time() - start_time

        if is_correct:
            if elapsed < 3:
                return "fast_correct"
            return "correct"

        if elapsed < 3:
            return "fast"

        return "wrong"