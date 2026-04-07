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
        for table, col_name, col_def in _iter_missing_columns(conn):
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {col_name} {col_def}")
        conn.commit()
    finally:
        conn.close()


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
