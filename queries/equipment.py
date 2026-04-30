import datetime
import sqlite3
import pandas as pd
import streamlit as st

from db.database import get_conn

STATUS_KR = {
    "available": "가용",
    "rented":    "대여중",
    "broken":    "고장",
    "retired":   "미사용",
}


@st.cache_data(ttl=300)
def get_model_summary() -> pd.DataFrame:
    """모델별 가용/미사용/고장/폐기/전체 수량"""
    with get_conn() as conn:
        df = pd.read_sql(
            """
            SELECT
                m.name AS 모델,
                COUNT(*) AS 전체,
                SUM(e.status = 'available'
                    AND (e.disposed IS NULL OR e.disposed = 0)) AS 가용,
                SUM(e.status = 'rented'
                    AND (e.disposed IS NULL OR e.disposed = 0)) AS 대여중,
                SUM(e.status = 'retired'
                    AND (e.disposed IS NULL OR e.disposed = 0)) AS 미사용,
                SUM(e.status = 'broken'
                    AND (e.disposed IS NULL OR e.disposed = 0)) AS 고장,
                SUM(e.disposed = 1) AS 폐기
            FROM equipment e
            JOIN models m ON e.model_id = m.id
            GROUP BY m.id
            ORDER BY m.name
            """,
            conn,
        )
    return df


@st.cache_data(ttl=300)
def get_all_equipment() -> pd.DataFrame:
    """전체 단말 목록 (상세)"""
    with get_conn() as conn:
        df = pd.read_sql(
            """
            SELECT
                e.id,
                m.name          AS 모델,
                e.serial_no     AS 시리얼번호,
                e.owner         AS 소유자,
                e.registered_at AS 등록일시,
                e.status,
                e.disposed,
                t.name          AS 보유팀,
                e.notes         AS 비고,
                e.updated_at    AS 최종수정
            FROM equipment e
            JOIN models m ON e.model_id = m.id
            LEFT JOIN teams t ON e.team_id = t.id
            ORDER BY m.name, e.serial_no
            """,
            conn,
        )
    df["상태"] = df["status"].map(STATUS_KR)
    return df.drop(columns=["status"])


@st.cache_data(ttl=300)
def get_equipment_by_team() -> pd.DataFrame:
    """팀별 모델 수량"""
    with get_conn() as conn:
        df = pd.read_sql(
            """
            SELECT
                t.name AS 팀,
                m.name AS 모델,
                COUNT(*) AS 수량
            FROM equipment e
            JOIN models m ON e.model_id = m.id
            JOIN teams  t ON e.team_id  = t.id
            GROUP BY t.name, m.name
            ORDER BY t.name, m.name
            """,
            conn,
        )
    return df


@st.cache_data(ttl=300)
def get_equipment_by_model() -> pd.DataFrame:
    """모델별 단말 목록 + 상태"""
    return get_all_equipment()


@st.cache_data(ttl=300)
def get_models() -> pd.DataFrame:
    """모델 목록"""
    with get_conn() as conn:
        return pd.read_sql(
            "SELECT id, name FROM models ORDER BY name", conn
        )


@st.cache_data(ttl=300)
def get_teams() -> pd.DataFrame:
    """팀 목록"""
    with get_conn() as conn:
        return pd.read_sql("SELECT id, name FROM teams ORDER BY name", conn)


def add_equipment(
    model_id: int, serial_no: str, status: str,
    team_id: int, notes: str = "", owner: str = "", registered_at: str = "",
):
    if not registered_at:
        registered_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        with get_conn() as conn:
            conn.execute(
                "INSERT INTO equipment"
                "(model_id, serial_no, status, team_id,"
                " notes, owner, registered_at)"
                " VALUES(?,?,?,?,?,?,?)",
                (model_id, serial_no or None, status, team_id,
                 notes, owner, registered_at),
            )
    except sqlite3.IntegrityError:
        raise ValueError(f"시리얼 번호 '{serial_no}'는 이미 등록되어 있습니다.")
    _clear_equipment_cache()


def remove_equipment(
    equipment_id: int, reason: str, target_team_id: int | None = None
):
    """
    reason: '이관' | '미사용' | '고장'
    - 이관   → team_id=target_team_id (상태 유지)
    - 미사용 → status='retired', team_id=NULL
    - 고장   → status='broken' (팀 유지)
    """
    with get_conn() as conn:
        if reason == "이관":
            conn.execute(
                "UPDATE equipment"
                " SET team_id=?, updated_at=datetime('now','localtime')"
                " WHERE id=?",
                (target_team_id, equipment_id),
            )
        elif reason == "고장":
            conn.execute(
                "UPDATE equipment"
                " SET status='broken',"
                " updated_at=datetime('now','localtime')"
                " WHERE id=?",
                (equipment_id,),
            )
        else:  # 미사용
            conn.execute(
                "UPDATE equipment"
                " SET status='retired',"
                " updated_at=datetime('now','localtime')"
                " WHERE id=?",
                (equipment_id,),
            )
    _clear_equipment_cache()


@st.cache_data(ttl=300)
def get_disposal_pending() -> pd.DataFrame:
    """폐기 대기 목록 (미사용/고장 처리됐으나 폐기 미완료)"""
    with get_conn() as conn:
        df = pd.read_sql(
            """
            SELECT
                e.id,
                m.name          AS 모델,
                e.serial_no     AS 시리얼번호,
                e.owner         AS 소유자,
                e.status,
                t.name          AS 팀,
                e.notes         AS 비고,
                e.updated_at    AS 처리일시
            FROM equipment e
            JOIN models m ON e.model_id = m.id
            LEFT JOIN teams t ON e.team_id = t.id
            WHERE e.status IN ('broken', 'retired')
              AND (e.disposed IS NULL OR e.disposed = 0)
            ORDER BY e.updated_at DESC
            """,
            conn,
        )
    df["사유"] = df["status"].map({"broken": "고장", "retired": "미사용"})
    return df.drop(columns=["status"])


@st.cache_data(ttl=300)
def get_disposal_done() -> pd.DataFrame:
    """폐기 완료 목록"""
    with get_conn() as conn:
        df = pd.read_sql(
            """
            SELECT
                e.id,
                m.name      AS 모델,
                e.serial_no AS 시리얼번호,
                e.owner     AS 소유자,
                e.notes     AS 비고,
                e.disposed_at AS 폐기일시
            FROM equipment e
            JOIN models m ON e.model_id = m.id
            WHERE e.disposed = 1
            ORDER BY e.disposed_at DESC
            """,
            conn,
        )
    return df


def dispose_equipment(equipment_id: int):
    """폐기 처리 → disposed=1 마킹"""
    with get_conn() as conn:
        conn.execute(
            "UPDATE equipment"
            " SET disposed=1,"
            " disposed_at=datetime('now','localtime')"
            " WHERE id=?",
            (equipment_id,),
        )
    get_disposal_pending.clear()
    get_disposal_done.clear()
    _clear_equipment_cache()


def hard_delete_equipment(equipment_id: int):
    """잘못 추가한 단말 완전 삭제 — 대여 이력이 없는 경우에만 허용"""
    with get_conn() as conn:
        count = conn.execute(
            "SELECT COUNT(*) FROM rentals WHERE equipment_id=?",
            (equipment_id,)
        ).fetchone()[0]
        if count > 0:
            raise ValueError("대여 이력이 있는 단말은 삭제할 수 없습니다.")
        conn.execute("DELETE FROM equipment WHERE id=?", (equipment_id,))
    _clear_equipment_cache()


def restore_equipment(equipment_id: int):
    """폐기 완료 → 폐기 대기로 원복"""
    with get_conn() as conn:
        conn.execute(
            "UPDATE equipment"
            " SET disposed=0, disposed_at=NULL"
            " WHERE id=?",
            (equipment_id,),
        )
    get_disposal_pending.clear()
    get_disposal_done.clear()
    _clear_equipment_cache()


def update_equipment(
    equipment_id: int,
    model_id: int,
    serial_no: str,
    team_id: int,
    owner: str,
    registered_at: str,
    notes: str,
):
    try:
        with get_conn() as conn:
            conn.execute(
                "UPDATE equipment"
                " SET model_id=?, serial_no=?, team_id=?, owner=?,"
                "     registered_at=?, notes=?,"
                "     updated_at=datetime('now','localtime')"
                " WHERE id=?",
                (model_id, serial_no or None, team_id, owner,
                 registered_at, notes, equipment_id),
            )
    except sqlite3.IntegrityError:
        raise ValueError(f"시리얼 번호 '{serial_no}'는 이미 등록되어 있습니다.")
    _clear_equipment_cache()


def add_model(name: str):
    with get_conn() as conn:
        conn.execute("INSERT OR IGNORE INTO models(name) VALUES(?)", (name,))
    get_models.clear()
    get_model_summary.clear()


def _clear_equipment_cache():
    get_all_equipment.clear()
    get_equipment_by_team.clear()
    get_model_summary.clear()
    get_equipment_by_model.clear()
    get_disposal_pending.clear()
