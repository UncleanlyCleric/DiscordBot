import logging
from pathlib import Path


def setup_logging() -> None:
    log_dir = Path("storage/logs")

    log_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    logging.basicConfig(
        level=logging.INFO,
        format=(
            "[%(asctime)s] "
            "[%(levelname)s] "
            "%(name)s: "
            "%(message)s"
        ),
        handlers=[
            logging.FileHandler(
                "storage/logs/bot.log",
                encoding="utf-8"
            ),
            logging.StreamHandler()
        ]
    )