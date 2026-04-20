import streamlit as st
from datetime import date

from queries.rentals import (
    get_active_rentals, get_rental_history, add_rental, return_rental, extend_rental
)
from queries.equipment import get_all_equipment
from db.database import get_conn

@st.dialog("반납 확인")
def confirm_return_dialog(items: list):
    # items: list of (rental_id, equipment_id, model, serial)
    st.markdown(f"**{len(items)}개** 단말을 반납 처리하시겠습니까?")
    for _, _, model, serial in items:
        st.markdown(f"- {model} ({serial})")
    col_ok, col_cancel = st.columns(2)
    if col_ok.button("확인", type="primary", use_container_width=True):
        for rental_id, equipment_id, _, _ in items:
            return_rental(rental_id, equipment_id)
        st.session_state["return_success"] = f"반납 완료: {len(items)}개"
        st.rerun()
    if col_cancel.button("취소", use_container_width=True):
        st.rerun()


_, _btn_col = st.columns([8, 2])
with _btn_col:
    if st.button("새로 고침"):
        get_active_rentals.clear()
        get_rental_history.clear()
        st.rerun()

st.title("📒 대여 현황")

tab_active, tab_history, tab_new = st.tabs(["대여 중", "대여 이력", "대여 등록"])

# ── 대여 중 목록 ────────────────────────────────────────────
with tab_active:

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

        st.markdown(f"**총 {len(active_df)}건** (🔴 : 반납 연체) — 행을 클릭하여 선택하세요")
        display_cols = ["모델", "시리얼번호", "대여팀", "대여자", "대여일시", "반납예정일"]
        event = st.dataframe(
            active_df[display_cols].style.apply(highlight_overdue, axis=1),
            width='stretch',
            hide_index=True,
            on_select="rerun",
            selection_mode="multi-row",
        )

        selected_rows = event.selection.rows
        if selected_rows:
            selected_rentals = active_df.iloc[selected_rows]
            count = len(selected_rows)
            st.divider()
            st.markdown(f"**{count}개 선택됨**")

            btn_return, btn_extend = st.columns(2)

            if btn_return.button(f"✅ 반납 처리 ({count}개)", use_container_width=True, type="primary"):
                with get_conn() as conn:
                    items = [
                        (
                            int(r["대여ID"]),
                            conn.execute(
                                "SELECT id FROM equipment WHERE serial_no=?",
                                (r["시리얼번호"],)
                            ).fetchone()["id"],
                            r["모델"],
                            r["시리얼번호"],
                        )
                        for _, r in selected_rentals.iterrows()
                    ]
                confirm_return_dialog(items)

            if "return_success" in st.session_state:
                st.success(st.session_state.pop("return_success"))
                st.rerun()

            with btn_extend.popover(f"📅 반납 연장 ({count}개)", use_container_width=True):
                earliest = selected_rentals["반납예정일"][selected_rentals["반납예정일"] != ""].min()
                new_date = st.date_input(
                    "새 반납 예정일 (선택된 전체 적용)",
                    value=date.fromisoformat(earliest) if earliest else date.today(),
                    key="extend_date",
                )
                if st.button("연장 확정", type="primary"):
                    for _, r in selected_rentals.iterrows():
                        extend_rental(int(r["대여ID"]), str(new_date))
                    st.success(f"{count}개 연장 완료 → {new_date}")
                    st.rerun()
        else:
            st.caption("행을 클릭하면 반납 처리 / 반납 연장 버튼이 나타납니다.")

# ── 대여 이력 ───────────────────────────────────────────────
with tab_history:
    hist_df = get_rental_history()

    if hist_df.empty:
        st.info("대여 이력이 없습니다.")
    else:
        teams = ["전체"] + sorted(hist_df["대여팀"].unique().tolist())
        sel_team = st.selectbox("팀 필터", teams, key="hist_team")
        if sel_team != "전체":
            hist_df = hist_df[hist_df["대여팀"] == sel_team]

        hist_cols = ["모델", "시리얼번호", "대여팀", "대여자", "대여일시", "반납예정일", "반납일시"]
        st.dataframe(hist_df[hist_cols], width='stretch', hide_index=True)

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
