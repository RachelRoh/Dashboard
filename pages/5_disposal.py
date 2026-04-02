import streamlit as st
from queries.equipment import get_disposal_pending, get_disposal_done, dispose_equipment

st.title("🗑️ 폐기 현황")

if st.button("🔄 새로고침"):
    get_disposal_pending.clear()
    get_disposal_done.clear()
    st.rerun()

# ── 폐기 대기 목록 ──────────────────────────────────────────
st.subheader("폐기 대기 목록")

pending_df = get_disposal_pending()

if pending_df.empty:
    st.info("폐기 대기 중인 단말이 없습니다.")
else:
    st.caption(f"총 {len(pending_df)}개")

    display = pending_df[["모델", "등록번호", "시리얼번호", "사유", "비고", "처리일시"]].copy()
    display.insert(0, "폐기", False)

    edited = st.data_editor(
        display,
        width='stretch',
        hide_index=True,
        column_config={
            "폐기": st.column_config.CheckboxColumn("폐기", width="small"),
        },
        disabled=["모델", "등록번호", "시리얼번호", "사유", "비고", "처리일시"],
    )

    checked = edited[edited["폐기"]].index.tolist()
    if checked and st.button("폐기 처리", type="primary"):
        for idx in checked:
            dispose_equipment(int(pending_df.iloc[idx]["id"]))
        st.rerun()

st.divider()

# ── 폐기 완료 목록 ──────────────────────────────────────────
st.subheader("폐기 완료 목록")

done_df = get_disposal_done()

if done_df.empty:
    st.info("폐기 완료된 단말이 없습니다.")
else:
    st.caption(f"총 {len(done_df)}개")
    st.dataframe(
        done_df[["모델", "등록번호", "시리얼번호", "비고", "폐기일시"]],
        width='stretch',
        hide_index=True,
    )
