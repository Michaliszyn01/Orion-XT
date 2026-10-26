import sqlite3
from pathlib import Path


class Database:
    def __init__(self, path: str = "data/orion.db"):
        self.path = Path(path)

    def _connection_path(self) -> Path:
        if self.path.exists() and self.path.is_dir():
            return self.path.with_name(f"{self.path.stem}_store.sqlite3")

        return self.path

    def connect(self):
        db_path = self._connection_path()
        db_path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(db_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA journal_mode=MEMORY")
        return connection

    def execute(self, query: str, params: tuple = ()):
        with self.connect() as conn:
            cursor = conn.execute(query, params)
            conn.commit()
            return cursor

    def fetch_all(self, query: str, params: tuple = ()):
        with self.connect() as conn:
            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def fetch_one(self, query: str, params: tuple = ()):
        with self.connect() as conn:
            cursor = conn.execute(query, params)
            row = cursor.fetchone()
            return dict(row) if row else None
