import sqlite3


class Database:
    def __init__(self, path="bot.db"):
        self.path = path
        self.conn = None

    # ---------------------------
    # CONNECTION
    # ---------------------------
    def connect(self):
        if self.conn:
            return self.conn

        self.conn = sqlite3.connect(self.path)
        self.conn.row_factory = sqlite3.Row  # enables dict-like access
        return self.conn

    # ---------------------------
    # CURSOR
    # ---------------------------
    def cursor(self):
        if not self.conn:
            self.connect()
        return self.conn.cursor()

    # ---------------------------
    # EXECUTE (WRITE)
    # ---------------------------
    def execute(self, query, params=()):
        cur = self.cursor()
        cur.execute(query, params)
        return cur

    # ---------------------------
    # FETCH ALL (READ MULTIPLE)
    # ---------------------------
    def fetch_all(self, query, params=()):
        cur = self.cursor()
        cur.execute(query, params)
        return cur.fetchall()

    # ---------------------------
    # FETCH ONE (READ SINGLE)
    # ---------------------------
    def fetch_one(self, query, params=()):
        cur = self.cursor()
        cur.execute(query, params)
        return cur.fetchone()

    # ---------------------------
    # COMMIT
    # ---------------------------
    def commit(self):
        if self.conn:
            self.conn.commit()

    # ---------------------------
    # INIT SCHEMA
    # ---------------------------
    def init_schema(self):
        cur = self.cursor()

        cur.execute("""
        CREATE TABLE IF NOT EXISTS quotes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id TEXT NOT NULL,
            category TEXT NOT NULL,
            quote TEXT NOT NULL,
            author TEXT,
            user_id TEXT
        )
        """)

        self.conn.commit()


# singleton instance
db = Database()