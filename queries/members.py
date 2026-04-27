import pandas as pd
import streamlit as st

from db.database import get_conn


@st.cache_data(ttl=300)
def get_members() -> pd.DataFrame:
    with get_conn() as conn:
        return pd.read_sql(
            "SELECT id, name FROM members ORDER BY name", conn
        )


def add_member(name: str):
    with get_conn() as conn:
        existing = conn.execute(
            "SELECT id FROM members WHERE name=?", (name,)
        ).fetchone()
        if existing:
            raise ValueError(f"'{name}' 멤버가 이미 존재합니다.")
        conn.execute("INSERT INTO members(name) VALUES(?)", (name,))
    get_members.clear()


def delete_member(member_id: int):
    with get_conn() as conn:
        conn.execute("DELETE FROM members WHERE id=?", (member_id,))
    get_members.clear()
