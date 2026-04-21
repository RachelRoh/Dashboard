import datetime
import io
import pandas as pd
import streamlit as st
from queries.equipment import (
    get_equipment_by_team, get_all_equipment,
    get_models, get_teams, add_equipment, remove_equipment,
    get_disposal_pending, add_model, hard_delete_equipment,
)

STATUS_KR = {"available": "가용", "broken": "고장", "retired": "폐기"}
STATUS_EN = {v: k for k, v in STATUS_KR.items()}
REMOVE_REASONS = ["이관", "미사용", "고장"]


@st.dialog("모델 생성하기")
def _show_create_model_dialog():
    terminal_type = st.selectbox(
        "단말 종류", ["E단말", "M단말"], key="dlg_terminal_type"
    )

    if terminal_type == "E단말":
        col1, col2 = st.columns(2)
        with col1:
            a_type = st.selectbox("A종류", ["A", "B", "C"], key="dlg_a_type")
        with col2:
            w_type = st.selectbox("W종류", ["R", "V"], key="dlg_w_type")
        model_name = f"{a_type}_{w_type}"
    else:
        col1, col2 = st.columns(2)
        with col1:
            device_type = st.selectbox(
                "단말타입", ["S620A", "A455A", "A465A"], key="dlg_device_type"
            )
        with col2:
            device_class = st.selectbox(
                "단말구분", ["OV1", "OV2", "CV1", "CV2"], key="dlg_device_class"
            )
        model_name = f"{device_type}_{device_class}"

    st.divider()
    st.markdown(f"**생성될 모델명:** `{model_name}`")

    existing = get_models()["name"].tolist()
    already_exists = model_name in existing
    if already_exists:
        st.warning(f"'{model_name}' 모델이 이미 존재합니다.")

    if st.button(
        "생성하기", type="primary", disabled=already_exists, key="dlg_create_btn"
    ):
        add_model(model_name)
        st.session_state["_new_model_name"] = model_name
        st.rerun()


@st.dialog("삭제 완료!")
def _show_delete_done():
    st.write(st.session_state.get("_del_done_msg", ""))
    if st.button("확인", type="primary"):
        del st.session_state["_del_done_msg"]
        st.rerun()


# 삭제 완료 팝업 트리거
if "_del_done_msg" in st.session_state:
    _show_delete_done()

_, _btn_col = st.columns([8, 2])
with _btn_col:
    if st.button("새로 고침"):
        get_equipment_by_team.clear()
        get_all_equipment.clear()
        get_disposal_pending.clear()
        st.rerun()

st.title("👥 파트별 현황")

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

USE_TABS_THRESHOLD = 6

if len(teams) <= USE_TABS_THRESHOLD:
    tabs = st.tabs(teams)
    _tab_iter = zip(tabs, teams)
else:
    selected_team = st.selectbox("팀 선택", teams)
    _tab_iter = [(st.container(), selected_team)]

for tab, team in _tab_iter:
    with tab:
        team_all = all_df[all_df["보유팀"] == team].reset_index(drop=True)
        team_active = team_all[team_all["disposed"] == 0].reset_index(drop=True)
        team_detail = team_all[team_all["상태"] == "가용"].reset_index(drop=True)
        team_pending = (
            pending_df[pending_df["팀"] == team].reset_index(drop=True)
        )

        cnt_avail    = len(team_all[(team_all["상태"] == "가용") & (team_all["disposed"] == 0)])
        cnt_rented   = len(team_all[(team_all["상태"] == "대여중") & (team_all["disposed"] == 0)])
        cnt_unused   = len(team_pending[team_pending["사유"] == "미사용"])
        cnt_broken   = len(team_pending[team_pending["사유"] == "고장"])
        cnt_disposed = len(team_all[team_all["disposed"] == 1])

        c1, c2, c3, c4, c5 = st.columns(5)
        c1.markdown(
            "<p style='font-size:.875rem;margin-bottom:0'>가용</p>"
            f"<p style='font-size:2rem;font-weight:700;color:#FF4B4B;margin:0'>{cnt_avail}</p>",
            unsafe_allow_html=True,
        )
        c2.metric("대여중", cnt_rented)
        c3.metric("미사용", cnt_unused)
        c4.metric("고장", cnt_broken)
        c5.metric("폐기", cnt_disposed)
        st.markdown("<br><br>", unsafe_allow_html=True)
        with st.container(border=True):
            fc1, fc2, fc3 = st.columns(3)
            model_opts = ["전체"] + sorted(team_active["모델"].dropna().unique().tolist())
            model_filter = fc1.selectbox("모델", model_opts, key=f"filter_model_{team}")
            owner_opts = ["전체"] + sorted(team_active["소유자"].dropna().unique().tolist())
            owner_filter = fc2.selectbox("소유자", owner_opts, key=f"filter_owner_{team}")
            status_filter = fc3.selectbox(
                "상태", ["가용", "대여중", "고장", "미사용", "전체"], index=0, key=f"filter_status_{team}"
            )
            search = st.text_input(
                "검색", placeholder="모델, 시리얼번호, 소유자, 비고 등 전체 검색", key=f"search_{team}"
            )
        filtered_active = team_active.copy()
        if model_filter != "전체":
            filtered_active = filtered_active[filtered_active["모델"] == model_filter]
        if status_filter != "전체":
            filtered_active = filtered_active[filtered_active["상태"] == status_filter]
        if owner_filter != "전체":
            filtered_active = filtered_active[filtered_active["소유자"] == owner_filter]
        if search:
            mask = filtered_active[["모델", "시리얼번호", "소유자", "비고"]].apply(
                lambda col: col.astype(str).str.contains(search, case=False, na=False)
            ).any(axis=1)
            filtered_active = filtered_active[mask]
        _disp = filtered_active[["모델", "시리얼번호", "상태", "소유자", "등록일시", "비고"]].copy()
        _disp["등록일"] = _disp["등록일시"].str[:10]
        st.dataframe(
            _disp[["모델", "시리얼번호", "소유자", "비고", "상태", "등록일"]],
            width='stretch',
            hide_index=True,
        )
        st.markdown("<br><br>", unsafe_allow_html=True)
        # ── 단말 추가 ───────────────────────────────────────
        with st.expander("➕ 단말 추가", expanded=False):
            model_keys = list(model_map.keys())
            new_model = st.session_state.get("_new_model_name")
            default_idx = (
                model_keys.index(new_model)
                if new_model and new_model in model_keys
                else 0
            )
            mc1, mc2 = st.columns([4, 1], vertical_alignment="bottom")
            with mc1:
                st.selectbox(
                    "모델 *", model_keys, index=default_idx,
                    key=f"sel_model_{team}",
                )
            with mc2:
                if st.button(
                    "🆕 모델 생성하기", key=f"create_model_btn_{team}",
                ):
                    _show_create_model_dialog()

            with st.form(f"add_form_{team}", clear_on_submit=True):
                col1, col2 = st.columns(2)
                with col1:
                    serial_no = st.text_input("시리얼 넘버")
                with col2:
                    owner = st.text_input("소유자")
                col3, col4 = st.columns(2)
                with col3:
                    registered_at = st.date_input(
                        "등록일시", value=datetime.date.today()
                    )
                with col4:
                    notes = st.text_input("비고")
                submitted = st.form_submit_button("추가", type="primary")

            if submitted:
                sel_model = st.session_state.get(f"sel_model_{team}", "")
                try:
                    add_equipment(
                        model_id=model_map[sel_model],
                        serial_no=serial_no.strip(),
                        status="available",
                        team_id=team_id_map[team],
                        owner=owner.strip(),
                        registered_at=registered_at.isoformat(),
                        notes=notes.strip(),
                    )
                except ValueError as e:
                    st.error(str(e))
                else:
                    st.session_state.pop("_new_model_name", None)
                    st.success(
                        f"단말 추가 완료: {sel_model}"
                        f" ({serial_no or '시리얼 없음'}) — {team}"
                    )
                    st.rerun()

        # ── CSV 일괄 추가 ────────────────────────────────────
        with st.expander("➕ CSV로 일괄 추가", expanded=False):
            st.caption("모델, 시리얼번호, 소유자, 등록일시, 비고 컬럼을 포함한 CSV 파일을 업로드하세요.")
            uploaded = st.file_uploader(
                "CSV 파일 선택", type="csv", key=f"csv_{team}"
            )
            if uploaded:
                try:
                    csv_df = pd.read_csv(io.BytesIO(uploaded.read()))
                    required = {"모델"}
                    if not required.issubset(csv_df.columns):
                        st.error("CSV에 '모델' 컬럼이 없습니다.")
                    else:
                        csv_df = csv_df.fillna("")
                        invalid = csv_df[~csv_df["모델"].isin(model_map.keys())]
                        if not invalid.empty:
                            st.warning(
                                f"알 수 없는 모델명이 있어 제외됩니다: "
                                f"{invalid['모델'].unique().tolist()}"
                            )
                        valid_df = csv_df[csv_df["모델"].isin(model_map.keys())]
                        st.dataframe(valid_df, hide_index=True, width="stretch")
                        if not valid_df.empty and st.button(
                            "일괄 추가", type="primary", key=f"csv_submit_{team}"
                        ):
                            for _, r in valid_df.iterrows():
                                add_equipment(
                                    model_id=model_map[r["모델"]],
                                    serial_no=str(r.get("시리얼번호", "")).strip() or None,
                                    status="available",
                                    team_id=team_id_map[team],
                                    owner=str(r.get("소유자", "")).strip(),
                                    registered_at=str(r.get("등록일시", "")).strip(),
                                    notes=str(r.get("비고", "")).strip(),
                                )
                            st.success(f"{len(valid_df)}개 단말 추가 완료")
                            st.rerun()
                except Exception as e:
                    st.error(f"CSV 읽기 오류: {e}")

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

        # ── 잘못 추가한 단말 완전 삭제 ──────────────────────
        with st.expander("🗑️ 잘못 추가한 단말 완전 삭제", expanded=False):
            st.caption("대여 이력이 없는 단말만 삭제할 수 있습니다. 삭제 후 복구할 수 없습니다.")
            if deletable.empty:
                st.info("삭제 가능한 단말이 없습니다.")
            else:
                n2 = st.session_state.get(f"hd_reset_{team}", 0)
                hd_labels = [
                    f"{r['모델']} — {r['시리얼번호']}"
                    for _, r in deletable.iterrows()
                ]
                sel_hd = st.selectbox(
                    "단말 선택",
                    [""] + hd_labels,
                    format_func=lambda x: "선택하세요" if x == "" else x,
                    key=f"hd_eq_{team}_{n2}",
                )
                confirmed = st.checkbox(
                    "삭제를 확인합니다 (복구 불가)",
                    key=f"hd_confirm_{team}_{n2}",
                )
                if sel_hd and confirmed and st.button(
                    "완전 삭제", key=f"hd_btn_{team}", type="primary"
                ):
                    hd_idx = hd_labels.index(sel_hd)
                    eq_id = int(deletable.iloc[hd_idx]["id"])
                    try:
                        hard_delete_equipment(eq_id)
                        st.session_state[f"hd_reset_{team}"] = n2 + 1
                        st.success(f"삭제 완료: {sel_hd}")
                        st.rerun()
                    except ValueError as e:
                        st.error(str(e))

        # ── 폐기 예정 ───────────────────────────────────────
        with st.expander(f"🗂️ 폐기 예정 ({len(team_pending)}건)", expanded=False):
            if team_pending.empty:
                st.info("폐기 예정인 단말이 없습니다.")
            else:
                st.dataframe(
                    team_pending[["모델", "시리얼번호", "소유자", "사유", "비고", "처리일시"]],
                    width='stretch',
                    hide_index=True,
                )
