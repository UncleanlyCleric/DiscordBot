from utils.config import config
from utils.db import db
from utils.storage import storage
from music.manager import music_manager
from utils.logger import logger


class Services:
    """
    CENTRAL SERVICE REGISTRY

    Prevents circular imports forever by centralizing access.
    """

    def __init__(self):
        self.config = config
        self.db = db
        self.storage = storage
        self.music = music_manager
        self.logger = logger


services = Services()