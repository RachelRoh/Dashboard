import streamlit as st
from queries.equipment import get_model_summary
from components.charts import pie_model_total

_, _btn_col = st.columns([8, 2])
with _btn_col:
    if st.button("새로 고침"):
        get_model_summary.clear()
        st.rerun()

st.title("📊 단말 현황 요약")

df = get_model_summary()

# ── KPI 메트릭 ──────────────────────────────────────────────
total  = int(df["전체"].sum())
avail  = int(df["가용"].sum())
unused = int(df["미사용"].sum())
broken = int(df["고장"].sum())
disposed = int(df["폐기"].sum())

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("총 단말 수", total)
c2.metric("가용", avail)
c3.metric("미사용", unused)
c4.metric("고장", broken)
c5.metric("폐기", disposed)

st.divider()

# ── 차트 ────────────────────────────────────────────────────
st.subheader("모델별 전체 수량")
st.plotly_chart(pie_model_total(df), width='stretch')

st.divider()

# ── 요약 테이블 ─────────────────────────────────────────────
st.subheader("모델별 수량 테이블")
st.dataframe(
    df[["모델", "가용", "미사용", "고장", "폐기", "전체"]],
    width='stretch',
    hide_index=True,
    column_config={
        "가용":   st.column_config.NumberColumn(format="%d"),
        "미사용": st.column_config.NumberColumn(format="%d"),
        "고장":   st.column_config.NumberColumn(format="%d"),
        "폐기":   st.column_config.NumberColumn(format="%d"),
        "전체":   st.column_config.NumberColumn(format="%d"),
    },
)
