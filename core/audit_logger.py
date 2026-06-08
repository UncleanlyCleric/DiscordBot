import logging
import time


class AuditLogger:
    """
    Centralized audit logging for:
    - cog loading
    - command execution
    - system events
    """

    def __init__(self):
        self.logger = logging.getLogger("audit")

    # -------------------------
    # COG EVENTS
    # -------------------------

    def cog_loaded(self, name: str):
        self.logger.info(f"[COG] Loaded: {name}")

    def cog_failed(self, name: str, error: Exception):
        self.logger.error(f"[COG] Failed: {name} | {error}")

    # -------------------------
    # COMMAND EVENTS
    # -------------------------

    def command_called(self, user_id: int, guild_id: int, command: str):
        self.logger.info(
            f"[CMD] User:{user_id} Guild:{guild_id} Command:{command}"
        )

    def command_failed(self, command: str, error: Exception):
        self.logger.error(f"[CMD] Failed {command} | {error}")

    # -------------------------
    # PERFORMANCE (optional future use)
    # -------------------------

    def start_timer(self):
        return time.time()

    def end_timer(self, start: float, label: str):
        self.logger.info(f"[TIMER] {label}: {time.time() - start:.3f}s")


audit = AuditLogger()