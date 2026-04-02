from contextlib import contextmanager
import pathlib
import sqlite3

DB_PATH = pathlib.Path(__file__).parent / "dut.db"


def ensure_db():
    """앱 시작 시 DB가 없으면 자동 초기화"""
    if not DB_PATH.exists():
        from db.init_db import init
        init()


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
