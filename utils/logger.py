import logging
import sys


class Logger:
    def __init__(self, name="bot", level=logging.INFO):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)

        if not self.logger.handlers:
            handler = logging.StreamHandler(sys.stdout)

            formatter = logging.Formatter(
                "[%(asctime)s] [%(levelname)s] %(name)s: %(message)s"
            )

            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

        self.logger.propagate = False

    def info(self, msg):
        self.logger.info(msg)

    def warning(self, msg):
        self.logger.warning(msg)

    def error(self, msg):
        self.logger.error(msg)

    def debug(self, msg):
        self.logger.debug(msg)


# ✅ singleton (safe global access)
logger = Logger()