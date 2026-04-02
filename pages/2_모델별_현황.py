import streamlit as st
from queries.equipment import get_model_summary, get_all_equipment

st.set_page_config(page_title="모델별 현황", page_icon="📋", layout="wide")
st.title("📋 모델별 현황")

if st.button("🔄 새로고침"):
    get_model_summary.clear()
    get_all_equipment.clear()
    st.rerun()

summary_df = get_model_summary()
all_df = get_all_equipment()

if summary_df.empty:
    st.warning("데이터가 없습니다.")
    st.stop()

models = summary_df["모델"].tolist()
tabs = st.tabs(models)

for tab, model in zip(tabs, models):
    with tab:
        row = summary_df[summary_df["모델"] == model].iloc[0]

        c1, c2, c3 = st.columns(3)
        c1.metric("전체", int(row["전체"]))
        c2.metric("가용", int(row["가용"]))
        c3.metric("고장", int(row["고장"]))

        model_df = all_df[all_df["모델"] == model].reset_index(drop=True)
        st.dataframe(
            model_df[["시리얼번호", "상태", "보유팀", "비고", "최종수정"]],
            width='stretch',
            hide_index=True,
        )
