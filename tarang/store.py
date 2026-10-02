import json
import sqlite3
import time
import re
from contextlib import contextmanager
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS commitments(id INTEGER PRIMARY KEY, chat INTEGER NOT NULL UNIQUE, outcome TEXT NOT NULL, owner TEXT NOT NULL, state TEXT NOT NULL DEFAULT 'open', paused INTEGER NOT NULL DEFAULT 0, next_check REAL NOT NULL);
CREATE TABLE IF NOT EXISTS events(id INTEGER PRIMARY KEY, key TEXT NOT NULL UNIQUE, commitment INTEGER NOT NULL REFERENCES commitments(id), source TEXT NOT NULL, payload TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'pending', attempts INTEGER NOT NULL DEFAULT 0, due REAL NOT NULL, created REAL NOT NULL);
CREATE TABLE IF NOT EXISTS operations(id INTEGER PRIMARY KEY, commitment INTEGER NOT NULL REFERENCES commitments(id), key TEXT NOT NULL, proposal TEXT NOT NULL, category TEXT NOT NULL, amount INTEGER NOT NULL, state TEXT NOT NULL, expires REAL NOT NULL, UNIQUE(commitment,key));
CREATE TABLE IF NOT EXISTS budgets(category TEXT PRIMARY KEY, ceiling INTEGER NOT NULL, cap INTEGER NOT NULL, delegated INTEGER NOT NULL, scope TEXT NOT NULL, recipient TEXT NOT NULL, kind TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS evidence(id INTEGER PRIMARY KEY, commitment INTEGER NOT NULL REFERENCES commitments(id), operation INTEGER, source TEXT NOT NULL, mode TEXT NOT NULL, content TEXT NOT NULL, verifies INTEGER NOT NULL, created REAL NOT NULL);
CREATE TABLE IF NOT EXISTS ledger(id INTEGER PRIMARY KEY, commitment INTEGER, kind TEXT NOT NULL, data TEXT NOT NULL, created REAL NOT NULL);
CREATE TABLE IF NOT EXISTS outbox(id INTEGER PRIMARY KEY, key TEXT NOT NULL UNIQUE, chat INTEGER NOT NULL, payload TEXT NOT NULL, state TEXT NOT NULL DEFAULT 'pending');
CREATE TABLE IF NOT EXISTS conversation_messages(id INTEGER PRIMARY KEY, external_id TEXT NOT NULL UNIQUE, scope TEXT NOT NULL, sender TEXT NOT NULL, body TEXT NOT NULL, sent_at REAL NOT NULL, received_at REAL NOT NULL, status TEXT NOT NULL, attempts INTEGER NOT NULL DEFAULT 0, due REAL NOT NULL, error TEXT);
CREATE TABLE IF NOT EXISTS conflicts(id INTEGER PRIMARY KEY, fingerprint TEXT NOT NULL UNIQUE, scope TEXT NOT NULL, report TEXT NOT NULL, state TEXT NOT NULL DEFAULT 'review', created REAL NOT NULL);
CREATE TABLE IF NOT EXISTS group_messages(id INTEGER PRIMARY KEY, external_id TEXT NOT NULL UNIQUE, source_id TEXT NOT NULL, sender TEXT NOT NULL, body TEXT NOT NULL, sent_at REAL NOT NULL, received_at REAL NOT NULL, kind TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS group_messages_source ON group_messages(source_id,id);
CREATE TABLE IF NOT EXISTS group_runs(id INTEGER PRIMARY KEY, created REAL NOT NULL, through_id INTEGER NOT NULL, result TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS metadata(key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS demo_sessions(chat INTEGER PRIMARY KEY, scenario TEXT NOT NULL, stage TEXT NOT NULL, generation TEXT NOT NULL, consent INTEGER NOT NULL DEFAULT 0, updated REAL NOT NULL);
CREATE TABLE IF NOT EXISTS demo_turns(key TEXT PRIMARY KEY, chat INTEGER NOT NULL, generation TEXT NOT NULL, body TEXT NOT NULL, reply TEXT NOT NULL DEFAULT '', status TEXT NOT NULL, created REAL NOT NULL, lease REAL NOT NULL DEFAULT 0);
CREATE TABLE IF NOT EXISTS demo_seen(key TEXT PRIMARY KEY, created REAL NOT NULL);
CREATE TABLE IF NOT EXISTS demo_usage(day TEXT NOT NULL, chat INTEGER NOT NULL, kind TEXT NOT NULL, count INTEGER NOT NULL, PRIMARY KEY(day,chat,kind));
"""


class Store:
    def __init__(self, path):
        self.postgres = path.startswith(("postgres://", "postgresql://"))
        if not self.postgres:
            Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.path = path
        with self.tx() as db:
            if self.postgres:
                schema = (
                    SCHEMA.replace("INTEGER PRIMARY KEY", "BIGSERIAL PRIMARY KEY")
                    .replace("INTEGER", "BIGINT")
                    .replace(" REAL", " DOUBLE PRECISION")
                )
                for statement in schema.split(";"):
                    if statement.strip():
                        db.execute(statement)
            else:
                db.executescript(SCHEMA)

    @contextmanager
    def tx(self):
        if self.postgres:
            import psycopg
            from psycopg.rows import dict_row

            with psycopg.connect(
                self.path, row_factory=dict_row, connect_timeout=15
            ) as conn:
                with conn.transaction():
                    # Serialize short state transactions across webhook and worker.
                    conn.execute("SELECT pg_advisory_xact_lock(7349281)")
                    yield PostgresConnection(conn)
            return
        db = sqlite3.connect(self.path, timeout=15)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys=ON")
        db.execute("PRAGMA journal_mode=WAL")
        db.execute("BEGIN IMMEDIATE")
        try:
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    @staticmethod
    def log(db, cid, kind, data):
        db.execute(
            "INSERT INTO ledger(commitment,kind,data,created) VALUES(?,?,?,?)",
            (cid, kind, json.dumps(data), time.time()),
        )

    @staticmethod
    def event(db, key, cid, source, payload, due=None):
        db.execute(
            "INSERT OR IGNORE INTO events(key,commitment,source,payload,due,created) VALUES(?,?,?,?,?,?)",
            (key, cid, source, json.dumps(payload), due or time.time(), time.time()),
        )

    @staticmethod
    def message(db, key, chat, text, buttons=None):
        payload = {"chat_id": chat, "text": text}
        if buttons:
            payload["reply_markup"] = {"inline_keyboard": buttons}
        db.execute(
            "INSERT OR IGNORE INTO outbox(key,chat,payload) VALUES(?,?,?)",
            (key, chat, json.dumps(payload)),
        )

    def snapshot(self):
        with self.tx() as db:
            return {
                t: [
                    dict(r)
                    for r in db.execute(f"SELECT * FROM {t} ORDER BY 1 DESC LIMIT 200")
                ]
                for t in (
                    "commitments",
                    "operations",
                    "budgets",
                    "evidence",
                    "events",
                    "ledger",
                    "outbox",
                    "conversation_messages",
                    "conflicts",
                    "group_runs",
                )
            }


class HybridRow(dict):
    def __getitem__(self, key):
        return (
            list(self.values())[key]
            if isinstance(key, int)
            else super().__getitem__(key)
        )


class PostgresCursor:
    def __init__(self, cursor, inserted=False):
        self.cursor = cursor
        self.lastrowid = None
        if inserted:
            row = cursor.fetchone()
            if row:
                self.lastrowid = row["id"]

    def fetchone(self):
        row = self.cursor.fetchone()
        return HybridRow(row) if row is not None else None

    def fetchall(self):
        return [HybridRow(r) for r in self.cursor.fetchall()]

    def __iter__(self):
        return iter(self.fetchall())


class PostgresConnection:
    def __init__(self, conn):
        self.conn = conn

    def execute(self, sql, parameters=()):
        sql = sql.replace("?", "%s")
        ignore = "INSERT OR IGNORE" in sql
        sql = sql.replace("INSERT OR IGNORE", "INSERT")
        if ignore:
            sql += " ON CONFLICT DO NOTHING"
        inserted = bool(
            re.match(
                r"INSERT INTO (commitments|events|operations|evidence|ledger|outbox|conversation_messages|conflicts|group_messages|group_runs)\b",
                sql,
            )
        )
        if inserted:
            sql += " RETURNING id"
        return PostgresCursor(self.conn.execute(sql, parameters), inserted)
