import streamlit as st
from queries.members import get_members, add_member, delete_member

st.title("👤 멤버 관리")

members_df = get_members()

# ── 멤버 목록 ────────────────────────────────────────────────
st.subheader("등록된 멤버")
if members_df.empty:
    st.info("등록된 멤버가 없습니다.")
else:
    st.dataframe(
        members_df[["name"]].rename(columns={"name": "이름"}),
        hide_index=True,
        width="stretch",
    )

st.divider()

# ── 멤버 추가 ────────────────────────────────────────────────
with st.expander("➕ 멤버 추가", expanded=False):
    with st.form("add_member_form", clear_on_submit=True):
        new_name = st.text_input("이름 *")
        if st.form_submit_button("추가", type="primary"):
            name = new_name.strip()
            if not name:
                st.error("이름을 입력하세요.")
            else:
                try:
                    add_member(name)
                    st.success(f"'{name}' 멤버 추가 완료")
                    st.rerun()
                except ValueError as e:
                    st.error(str(e))

# ── 멤버 삭제 ────────────────────────────────────────────────
with st.expander("🗑️ 멤버 삭제", expanded=False):
    if members_df.empty:
        st.info("삭제할 멤버가 없습니다.")
    else:
        name_to_id = dict(zip(members_df["name"], members_df["id"]))
        n = st.session_state.get("member_del_reset", 0)
        sel = st.selectbox(
            "삭제할 멤버 선택",
            [""] + members_df["name"].tolist(),
            format_func=lambda x: "선택하세요" if x == "" else x,
            key=f"del_member_{n}",
        )
        if sel and st.button("삭제", type="primary", key="del_member_btn"):
            delete_member(name_to_id[sel])
            st.session_state["member_del_reset"] = n + 1
            st.success(f"'{sel}' 멤버 삭제 완료")
            st.rerun()
