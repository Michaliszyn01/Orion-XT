from datetime import datetime
import json

from storage.database import Database


class MemoryStore:
    def __init__(self, db: Database | None = None):
        self.db = db or Database()

    def save_event(
        self,
        event_type: str,
        content: str,
        importance: int = 1,
        metadata: dict | None = None,
    ):
        self._ensure_table("events")
        now = self._now()
        metadata_json = self._metadata_json(metadata)

        self._insert_row("events", {
            "event_type": event_type,
            "type": event_type,
            "category": event_type,
            "content": content,
            "message": content,
            "description": content,
            "importance": importance,
            "metadata": metadata_json,
            "meta": metadata_json,
            "created_at": now,
            "timestamp": now,
        })

    def save_short_memory(
        self,
        category: str,
        content: str,
        importance: int = 1,
        metadata: dict | None = None,
    ):
        self._ensure_table("short_term_memory")
        now = self._now()
        metadata_json = self._metadata_json(metadata)

        self._insert_row("short_term_memory", {
            "category": category,
            "content": content,
            "value": content,
            "importance": importance,
            "metadata": metadata_json,
            "meta": metadata_json,
            "created_at": now,
            "timestamp": now,
        })

    def save_long_memory(
        self,
        category: str,
        key: str,
        value: str,
        importance: int = 1,
        metadata: dict | None = None,
    ):
        self._ensure_table("long_term_memory")
        now = self._now()
        metadata_json = self._metadata_json(metadata)
        values = {
            "category": category,
            "key": key,
            "memory_key": key,
            "name": key,
            "value": value,
            "content": value,
            "importance": importance,
            "metadata": metadata_json,
            "meta": metadata_json,
            "created_at": now,
            "timestamp": now,
            "updated_at": now,
        }

        columns = self._table_columns("long_term_memory")
        key_column = self._first_existing(columns, ["key", "memory_key", "name"])
        category_column = self._first_existing(columns, ["category"])

        if key_column:
            where_parts = [f"{self._quote_identifier(key_column)} = ?"]
            params = [key]

            if category and category_column:
                where_parts.append(f"{self._quote_identifier(category_column)} = ?")
                params.append(category)

            query = (
                f"SELECT rowid AS rowid FROM {self._quote_identifier('long_term_memory')} "
                f"WHERE {' AND '.join(where_parts)} LIMIT 1"
            )
            existing = self.db.fetch_one(query, tuple(params))

            if existing:
                self._update_row_by_rowid("long_term_memory", values, existing["rowid"])
                return

        self._insert_row("long_term_memory", values)

    def get_recent_events(self, limit: int = 10):
        self._ensure_table("events")
        return self._fetch_rows("events", limit=limit)

    def get_relevant_memories(self, category: str | None = None, limit: int = 10):
        self._ensure_table("long_term_memory")
        self._ensure_table("short_term_memory")

        limit = self._clean_limit(limit)
        rows = (
            self._fetch_rows("long_term_memory", category=category, limit=limit)
            + self._fetch_rows("short_term_memory", category=category, limit=limit)
        )

        rows.sort(key=self._memory_sort_key, reverse=True)
        return rows[:limit]

    def get_preferences(self):
        self._ensure_table("preferences")
        columns = self._table_columns("preferences")
        key_column = self._first_existing(columns, ["key", "name", "preference_key"])
        value_column = self._first_existing(columns, ["value", "content", "preference_value"])

        if not key_column or not value_column:
            return {}

        query = (
            f"SELECT {self._quote_identifier(key_column)}, {self._quote_identifier(value_column)} "
            f"FROM {self._quote_identifier('preferences')}"
        )
        rows = self.db.fetch_all(query)
        return {row[key_column]: row[value_column] for row in rows}

    def set_preference(self, key: str, value: str):
        self._ensure_table("preferences")
        columns = self._table_columns("preferences")
        key_column = self._first_existing(columns, ["key", "name", "preference_key"])
        value_column = self._first_existing(columns, ["value", "content", "preference_value"])

        if not key_column or not value_column:
            return

        now = self._now()
        values = {
            key_column: key,
            value_column: value,
            "created_at": now,
            "timestamp": now,
            "updated_at": now,
        }

        query = (
            f"SELECT rowid AS rowid FROM {self._quote_identifier('preferences')} "
            f"WHERE {self._quote_identifier(key_column)} = ? LIMIT 1"
        )
        existing = self.db.fetch_one(query, (key,))

        if existing:
            self._update_row_by_rowid("preferences", values, existing["rowid"])
            return

        self._insert_row("preferences", values)

    def _table_columns(self, table_name: str) -> set[str]:
        rows = self.db.fetch_all(f"PRAGMA table_info({self._quote_identifier(table_name)})")
        return {row["name"] for row in rows}

    def _ensure_table(self, table_name: str):
        if self._table_columns(table_name):
            return

        schemas = {
            "events": """
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT,
                    content TEXT,
                    importance INTEGER DEFAULT 1,
                    metadata TEXT,
                    created_at TEXT
                )
            """,
            "short_term_memory": """
                CREATE TABLE IF NOT EXISTS short_term_memory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category TEXT,
                    content TEXT,
                    importance INTEGER DEFAULT 1,
                    metadata TEXT,
                    created_at TEXT
                )
            """,
            "long_term_memory": """
                CREATE TABLE IF NOT EXISTS long_term_memory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category TEXT,
                    "key" TEXT,
                    value TEXT,
                    content TEXT,
                    importance INTEGER DEFAULT 1,
                    metadata TEXT,
                    created_at TEXT,
                    updated_at TEXT
                )
            """,
            "preferences": """
                CREATE TABLE IF NOT EXISTS preferences (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    "key" TEXT UNIQUE,
                    value TEXT,
                    updated_at TEXT
                )
            """,
        }

        query = schemas.get(table_name)
        if query:
            self.db.execute(query)

    def _insert_row(self, table_name: str, values: dict):
        columns = self._table_columns(table_name)
        insert_values = {
            column: value
            for column, value in values.items()
            if column in columns
        }

        if not insert_values:
            self.db.execute(f"INSERT INTO {self._quote_identifier(table_name)} DEFAULT VALUES")
            return

        column_sql = ", ".join(self._quote_identifier(column) for column in insert_values)
        placeholders = ", ".join("?" for _ in insert_values)
        query = (
            f"INSERT INTO {self._quote_identifier(table_name)} "
            f"({column_sql}) VALUES ({placeholders})"
        )
        self.db.execute(query, tuple(insert_values.values()))

    def _update_row_by_rowid(self, table_name: str, values: dict, rowid: int):
        columns = self._table_columns(table_name)
        update_values = {
            column: value
            for column, value in values.items()
            if column in columns and column not in {"created_at", "timestamp"}
        }

        if not update_values:
            return

        set_sql = ", ".join(
            f"{self._quote_identifier(column)} = ?"
            for column in update_values
        )
        query = (
            f"UPDATE {self._quote_identifier(table_name)} "
            f"SET {set_sql} WHERE rowid = ?"
        )
        self.db.execute(query, tuple(update_values.values()) + (rowid,))

    def _fetch_rows(self, table_name: str, category: str | None = None, limit: int = 10):
        columns = self._table_columns(table_name)
        if not columns:
            return []

        params = []
        where_sql = ""

        if category and "category" in columns:
            where_sql = f" WHERE {self._quote_identifier('category')} = ?"
            params.append(category)

        order_sql = self._order_sql(columns)
        params.append(self._clean_limit(limit))

        query = (
            f"SELECT * FROM {self._quote_identifier(table_name)}"
            f"{where_sql}{order_sql} LIMIT ?"
        )
        rows = self.db.fetch_all(query, tuple(params))

        for row in rows:
            row["_source"] = table_name

        return rows

    def _order_sql(self, columns: set[str]) -> str:
        order_parts = []

        if "importance" in columns:
            order_parts.append(f"{self._quote_identifier('importance')} DESC")

        if "created_at" in columns:
            order_parts.append(f"{self._quote_identifier('created_at')} DESC")
        elif "timestamp" in columns:
            order_parts.append(f"{self._quote_identifier('timestamp')} DESC")

        if "id" in columns:
            order_parts.append(f"{self._quote_identifier('id')} DESC")

        return f" ORDER BY {', '.join(order_parts)}" if order_parts else ""

    def _memory_sort_key(self, row: dict):
        try:
            importance = int(row.get("importance") or 0)
        except (TypeError, ValueError):
            importance = 0

        timestamp = row.get("updated_at") or row.get("created_at") or row.get("timestamp") or ""
        return importance, timestamp

    def _metadata_json(self, metadata: dict | None) -> str:
        return json.dumps(metadata or {}, ensure_ascii=False)

    def _now(self) -> str:
        return datetime.now().isoformat(timespec="seconds")

    def _clean_limit(self, limit: int) -> int:
        try:
            return max(1, int(limit))
        except (TypeError, ValueError):
            return 10

    def _first_existing(self, columns: set[str], names: list[str]) -> str | None:
        for name in names:
            if name in columns:
                return name

        return None

    def _quote_identifier(self, name: str) -> str:
        if not name or name[0].isdigit():
            raise ValueError(f"Identificador SQLite invalido: {name!r}")

        if not all(char.isalnum() or char == "_" for char in name):
            raise ValueError(f"Identificador SQLite invalido: {name!r}")

        return f'"{name}"'
