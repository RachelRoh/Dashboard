import pandas as pd
import streamlit as st

from db.database import get_conn
from queries.equipment import _clear_equipment_cache


@st.cache_data(ttl=300)
def get_active_rentals() -> pd.DataFrame:
    """현재 대여 중인 단말 목록"""
    with get_conn() as conn:
        df = pd.read_sql(
            """
            SELECT
                r.id         AS 대여ID,
                m.name       AS 모델,
                e.serial_no  AS 시리얼번호,
                t.name       AS 대여팀,
                r.borrower_name  AS 대여자,
                r.borrowed_at    AS 대여일시,
                r.expected_return AS 반납예정일
            FROM rentals r
            JOIN equipment e ON r.equipment_id = e.id
            JOIN models    m ON e.model_id     = m.id
            JOIN teams     t ON r.borrower_team = t.id
            WHERE r.returned_at IS NULL
            ORDER BY r.expected_return
            """,
            conn,
        )
    return df


@st.cache_data(ttl=300)
def get_rental_history() -> pd.DataFrame:
    """전체 대여 이력"""
    with get_conn() as conn:
        df = pd.read_sql(
            """
            SELECT
                r.id              AS 대여ID,
                m.name            AS 모델,
                e.serial_no       AS 시리얼번호,
                t.name            AS 대여팀,
                r.borrower_name   AS 대여자,
                r.borrowed_at     AS 대여일시,
                r.expected_return AS 반납예정일,
                COALESCE(r.returned_at, '대여중') AS 반납일시
            FROM rentals r
            JOIN equipment e ON r.equipment_id = e.id
            JOIN models    m ON e.model_id      = m.id
            JOIN teams     t ON r.borrower_team  = t.id
            ORDER BY r.borrowed_at DESC
            """,
            conn,
        )
    return df


def add_rental(
    equipment_id: int, team_id: int,
    borrower_name: str, expected_return: str,
):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO rentals"
            "(equipment_id, borrower_team, borrower_name, expected_return)"
            " VALUES(?,?,?,?)",
            (equipment_id, team_id, borrower_name, expected_return),
        )
        conn.execute(
            "UPDATE equipment SET status='rented' WHERE id=?",
            (equipment_id,),
        )
    get_active_rentals.clear()
    get_rental_history.clear()
    _clear_equipment_cache()


def return_rental(rental_id: int, equipment_id: int):
    with get_conn() as conn:
        conn.execute(
            "UPDATE rentals"
            " SET returned_at=datetime('now','localtime')"
            " WHERE id=?",
            (rental_id,),
        )
        conn.execute(
            "UPDATE equipment SET status='available' WHERE id=?",
            (equipment_id,),
        )
    get_active_rentals.clear()
    get_rental_history.clear()
    _clear_equipment_cache()
