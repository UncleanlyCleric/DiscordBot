import sqlite3

class TriviaDB:
    def __init__(self, path="trivia.db"):
        self.conn = sqlite3.connect(path)
        self.cur = self.conn.cursor()
        self.init()

    def init(self):
        self.cur.execute("""
        CREATE TABLE IF NOT EXISTS players (
            user_id INTEGER PRIMARY KEY,
            games INTEGER DEFAULT 0,
            wins INTEGER DEFAULT 0,
            score INTEGER DEFAULT 0,
            correct INTEGER DEFAULT 0,
            wrong INTEGER DEFAULT 0
        )
        """)
        self.conn.commit()

    def ensure(self, user_id):
        self.cur.execute("INSERT OR IGNORE INTO players (user_id) VALUES (?)", (user_id,))
        self.conn.commit()

    def add_game(self, user_id):
        self.ensure(user_id)
        self.cur.execute("UPDATE players SET games = games + 1 WHERE user_id=?", (user_id,))
        self.conn.commit()

    def add_win(self, user_id):
        self.ensure(user_id)
        self.cur.execute("UPDATE players SET wins = wins + 1 WHERE user_id=?", (user_id,))
        self.conn.commit()

    def add_score(self, user_id, score):
        self.ensure(user_id)
        self.cur.execute("UPDATE players SET score = score + ? WHERE user_id=?", (score, user_id))
        self.conn.commit()