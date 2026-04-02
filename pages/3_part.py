import streamlit as st
from queries.equipment import (
    get_equipment_by_team, get_all_equipment,
    get_models, get_teams, add_equipment, remove_equipment,
    get_disposal_pending,
)

STATUS_KR = {"available": "가용", "broken": "고장", "retired": "폐기"}
STATUS_EN = {v: k for k, v in STATUS_KR.items()}
REMOVE_REASONS = ["이관", "미사용", "고장"]

st.title("👥 파트별 현황")


@st.dialog("삭제 완료!")
def _show_delete_done():
    st.write(st.session_state.get("_del_done_msg", ""))
    if st.button("확인", type="primary"):
        del st.session_state["_del_done_msg"]
        st.rerun()


# 삭제 완료 팝업 트리거
if "_del_done_msg" in st.session_state:
    _show_delete_done()


if st.button("🔄 새로고침"):
    get_equipment_by_team.clear()
    get_all_equipment.clear()
    get_disposal_pending.clear()
    st.rerun()

team_df = get_equipment_by_team()
all_df = get_all_equipment()
teams_df = get_teams()
models_df = get_models()
model_map = dict(zip(models_df["name"], models_df["id"]))
pending_df = get_disposal_pending()

if teams_df.empty:
    st.warning("등록된 팀이 없습니다.")
    st.stop()

teams = sorted(teams_df["name"].tolist())
team_id_map = dict(zip(teams_df["name"], teams_df["id"]))
tabs = st.tabs(teams)

for tab, team in zip(tabs, teams):
    with tab:
        # 가용 단말만 메인 목록에 표시
        team_all = all_df[all_df["보유팀"] == team].reset_index(drop=True)
        team_detail = team_all[team_all["상태"] == "가용"].reset_index(drop=True)
        team_pending = pending_df[pending_df["팀"] == team].reset_index(drop=True)

        c1, c2, c3 = st.columns(3)
        c1.metric("전체", len(team_all))
        c2.metric("가용", len(team_detail))
        c3.metric("폐기 예정", len(team_pending))

        st.dataframe(
            team_detail[["모델", "등록번호", "시리얼번호", "비고"]],
            width='stretch',
            hide_index=True,
        )

        # ── 단말 추가 ───────────────────────────────────────
        with st.expander("➕ 단말 추가", expanded=False):
            with st.form(f"add_form_{team}", clear_on_submit=True):
                sel_model = st.selectbox("모델 *", list(model_map.keys()))
                col1, col2 = st.columns(2)
                with col1:
                    reg_no = st.text_input("등록 번호")
                with col2:
                    serial_no = st.text_input("시리얼 번호")
                notes = st.text_input("비고")
                submitted = st.form_submit_button("추가", type="primary")

            if submitted:
                add_equipment(
                    model_id=model_map[sel_model],
                    serial_no=serial_no.strip(),
                    status="available",
                    team_id=team_id_map[team],
                    notes=notes.strip(),
                    reg_no=reg_no.strip(),
                )
                st.success(
                    f"단말 추가 완료: {sel_model}"
                    f" ({serial_no or '시리얼 없음'}) — {team}"
                )
                st.rerun()

        # ── 단말 삭제 ───────────────────────────────────────
        with st.expander("🗑️ 단말 삭제", expanded=False):
            # 가용 단말만 삭제 대상
            deletable = team_detail.reset_index(drop=True)

            if deletable.empty:
                st.info("삭제할 단말이 없습니다.")
            else:
                eq_labels = [
                    f"{r['모델']} — {r['시리얼번호']}"
                    for _, r in deletable.iterrows()
                ]
                # 위젯 키에 카운터를 붙여 확인 후 강제 초기화
                n = st.session_state.get(f"del_reset_{team}", 0)
                sel_eq = st.selectbox(
                    "단말 선택", [""] + eq_labels,
                    format_func=lambda x: "선택하세요" if x == "" else x,
                    key=f"del_eq_{team}_{n}",
                )
                reason = st.selectbox(
                    "사유 *", [""] + REMOVE_REASONS,
                    format_func=lambda x: "선택하세요" if x == "" else x,
                    key=f"del_reason_{team}_{n}",
                )

                target_team_id = None
                if reason == "이관":
                    other_teams = [t for t in teams if t != team]
                    sel_target = st.selectbox(
                        "이관 팀 *", other_teams, key=f"del_target_{team}_{n}"
                    )
                    target_team_id = team_id_map[sel_target]

                if sel_eq and reason and st.button(
                    "확인", key=f"del_btn_{team}", type="primary"
                ):
                    eq_idx = eq_labels.index(sel_eq)
                    eq_id = int(deletable.iloc[eq_idx]["id"])
                    remove_equipment(eq_id, reason, target_team_id)

                    # 카운터 증가 → 다음 렌더링에서 새 키로 위젯 생성 = 초기화
                    st.session_state[f"del_reset_{team}"] = n + 1

                    if reason == "이관":
                        st.success(f"이관 완료: {sel_eq} → {sel_target}")
                        st.rerun()
                    else:
                        st.session_state["_del_done_msg"] = (
                            f"{sel_eq}이(가) [{reason}] 처리되어\n"
                            "폐기 예정 목록으로 이동되었습니다."
                        )
                        st.rerun()

        # ── 폐기 예정 ───────────────────────────────────────
        with st.expander(f"🗂️ 폐기 예정 ({len(team_pending)}건)", expanded=False):
            if team_pending.empty:
                st.info("폐기 예정인 단말이 없습니다.")
            else:
                st.dataframe(
                    team_pending[["모델", "등록번호", "시리얼번호", "사유", "비고", "처리일시"]],
                    width='stretch',
                    hide_index=True,
                )
