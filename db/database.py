from contextlib import contextmanager
import pathlib
import re
import sqlite3

DB_PATH = pathlib.Path(__file__).parent / "dut.db"


def ensure_db():
    """앱 시작 시 DB가 없으면 자동 초기화, 있으면 마이그레이션"""
    if not DB_PATH.exists():
        from db.init_db import init
        init()
    _migrate()



def _migrate():
    """schema.sql 기준으로 기존 DB에 빠진 컬럼을 자동 추가"""
    conn = sqlite3.connect(DB_PATH)
    try:
        _migrate_rented_status(conn)
        for table, col_name, col_def in _iter_missing_columns(conn):
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {col_name} {col_def}")
        _sync_rented_status(conn)
        conn.commit()
    finally:
        conn.close()


def _sync_rented_status(conn):
    """기존 활성 대여 건의 equipment status를 'rented'로 동기화"""
    exists = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='equipment'"
    ).fetchone()
    if not exists:
        return
    conn.execute("""
        UPDATE equipment SET status = 'rented'
        WHERE id IN (
            SELECT equipment_id FROM rentals WHERE returned_at IS NULL
        )
        AND status = 'available'
    """)


def _migrate_rented_status(conn):
    """equipment CHECK constraint에 'rented' 추가 (테이블 재생성)"""
    row = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='equipment'"
    ).fetchone()
    if not row or "'rented'" in row[0]:
        return
    conn.execute("PRAGMA foreign_keys=OFF")
    conn.execute("DROP TABLE IF EXISTS equipment_new")
    conn.execute("""
        CREATE TABLE equipment_new (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            model_id      INTEGER NOT NULL REFERENCES models(id),
            serial_no     TEXT UNIQUE,
            status        TEXT NOT NULL DEFAULT 'available'
                              CHECK(status IN ('available','broken','retired','rented')),
            team_id       INTEGER REFERENCES teams(id),
            reg_no        TEXT DEFAULT '',
            owner         TEXT DEFAULT '',
            registered_at TEXT DEFAULT (datetime('now','localtime')),
            notes         TEXT DEFAULT '',
            disposed      INTEGER DEFAULT 0,
            disposed_at   TEXT,
            updated_at    TEXT DEFAULT (datetime('now','localtime'))
        )
    """)
    conn.execute("INSERT INTO equipment_new SELECT * FROM equipment")
    conn.execute("DROP TABLE equipment")
    conn.execute("ALTER TABLE equipment_new RENAME TO equipment")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.commit()


def _iter_missing_columns(conn):
    schema_path = pathlib.Path(__file__).parent / "schema.sql"
    sql = schema_path.read_text(encoding="utf-8")

    existing_tables = {
        row[0] for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
    }

    for m in re.finditer(
        r"CREATE TABLE IF NOT EXISTS (\w+)\s*\((.+?)\);", sql, re.DOTALL | re.IGNORECASE
    ):
        table = m.group(1)
        if table not in existing_tables:
            continue  # 테이블 자체가 없으면 건너뜀 (ALTER TABLE 실패 방지)
        existing_cols = {row[1] for row in conn.execute(f"PRAGMA table_info({table})")}
        for line in m.group(2).splitlines():
            line = line.strip().rstrip(",")
            if not line or line.upper().startswith(
                ("PRIMARY", "FOREIGN", "UNIQUE", "CHECK", "CONSTRAINT", "ID ")
            ):
                continue
            parts = line.split()
            if len(parts) < 2:
                continue
            col_name = parts[0]
            if col_name not in existing_cols:
                col_def = " ".join(parts[1:])
                yield table, col_name, col_def


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
