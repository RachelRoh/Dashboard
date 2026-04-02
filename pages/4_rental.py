import streamlit as st
from datetime import date

from queries.rentals import (
    get_active_rentals, get_rental_history, add_rental, return_rental
)
from queries.equipment import get_all_equipment
from db.database import get_conn

st.title("📒 대여 현황")

tab_active, tab_history, tab_new = st.tabs(["대여 중", "대여 이력", "대여 등록"])

# ── 대여 중 목록 ────────────────────────────────────────────
with tab_active:
    if st.button("🔄 새로고침", key="refresh_active"):
        get_active_rentals.clear()
        st.rerun()

    active_df = get_active_rentals()

    if active_df.empty:
        st.info("현재 대여 중인 단말이 없습니다.")
    else:
        today = date.today().isoformat()
        active_df["반납예정일"] = active_df["반납예정일"].fillna("")

        def highlight_overdue(row):
            if row["반납예정일"] and row["반납예정일"] < today:
                return ["background-color: #FFEBEE"] * len(row)
            return [""] * len(row)

        st.markdown(f"**총 {len(active_df)}건** (🔴 : 반납 연체)")
        st.dataframe(
            active_df.style.apply(highlight_overdue, axis=1),
            width='stretch',
            hide_index=True,
        )

        st.divider()
        st.subheader("반납 처리")
        labels = [
            f"[{r['대여ID']}] {r['모델']} ({r['시리얼번호']}) - {r['대여자']}"
            for _, r in active_df.iterrows()
        ]
        selected_label = st.selectbox("반납할 단말 선택", labels)
        idx = labels.index(selected_label)
        selected_rental = active_df.iloc[idx]

        if st.button("반납 처리"):
            with get_conn() as conn:
                row = conn.execute(
                    "SELECT id FROM equipment WHERE serial_no=?",
                    (selected_rental["시리얼번호"],)
                ).fetchone()
            return_rental(int(selected_rental["대여ID"]), row["id"])
            get_active_rentals.clear()
            serial = selected_rental["시리얼번호"]
            st.success(f"반납 완료: {selected_rental['모델']} ({serial})")
            st.rerun()

# ── 대여 이력 ───────────────────────────────────────────────
with tab_history:
    if st.button("🔄 새로고침", key="refresh_history"):
        get_rental_history.clear()
        st.rerun()

    hist_df = get_rental_history()

    if hist_df.empty:
        st.info("대여 이력이 없습니다.")
    else:
        teams = ["전체"] + sorted(hist_df["대여팀"].unique().tolist())
        sel_team = st.selectbox("팀 필터", teams, key="hist_team")
        if sel_team != "전체":
            hist_df = hist_df[hist_df["대여팀"] == sel_team]

        st.dataframe(hist_df, width='stretch', hide_index=True)

# ── 대여 등록 ───────────────────────────────────────────────
with tab_new:
    st.subheader("새 대여 등록")

    all_df = get_all_equipment()
    avail_df = all_df[all_df["상태"] == "가용"].reset_index(drop=True)

    if avail_df.empty:
        st.warning("현재 가용 단말이 없습니다.")
    else:
        with get_conn() as conn:
            teams_rows = conn.execute(
                "SELECT id, name FROM teams ORDER BY name"
            ).fetchall()
        team_map = {r["name"]: r["id"] for r in teams_rows}

        eq_labels = [
            f"{r['모델']} - {r['시리얼번호']} ({r['보유팀']})"
            for _, r in avail_df.iterrows()
        ]

        with st.form("rental_form"):
            sel_eq = st.selectbox("단말 선택", eq_labels)
            sel_team = st.selectbox("대여 팀", list(team_map.keys()))
            borrower = st.text_input("대여자 이름")
            exp_return = st.date_input("반납 예정일", value=date.today())
            submitted = st.form_submit_button("대여 등록")

        if submitted:
            if not borrower.strip():
                st.error("대여자 이름을 입력하세요.")
            else:
                eq_idx = eq_labels.index(sel_eq)
                eq_row = avail_df.iloc[eq_idx]
                with get_conn() as conn:
                    eq_id = conn.execute(
                        "SELECT id FROM equipment WHERE serial_no=?",
                        (eq_row["시리얼번호"],)
                    ).fetchone()["id"]
                add_rental(
                    equipment_id=eq_id,
                    team_id=team_map[sel_team],
                    borrower_name=borrower.strip(),
                    expected_return=str(exp_return),
                )
                get_all_equipment.clear()
                st.success(
                    f"대여 등록 완료: {eq_row['모델']} -> {borrower} ({sel_team})"
                )
                st.rerun()
