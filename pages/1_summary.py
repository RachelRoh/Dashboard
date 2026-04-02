import streamlit as st
from queries.equipment import get_model_summary
from components.charts import pie_model_total

st.title("📊 단말 현황 요약")

if st.button("🔄 새로고침"):
    get_model_summary.clear()
    st.rerun()

df = get_model_summary()

# ── KPI 메트릭 ──────────────────────────────────────────────
total = int(df["전체"].sum())
avail = int(df["가용"].sum())
pending = int(df["폐기 예정"].sum())
done = int(df["폐기 완료"].sum())

c1, c2, c3, c4 = st.columns(4)
c1.metric("총 단말 수", total)
c2.metric("가용", avail, delta=f"{avail/total*100:.0f}%" if total else "0%")
c3.metric("폐기 예정", pending,
          delta=f"-{pending}" if pending else "0", delta_color="inverse")
c4.metric("폐기 완료", done)

st.divider()

# ── 차트 ────────────────────────────────────────────────────
st.subheader("모델별 전체 수량")
st.plotly_chart(pie_model_total(df), width='stretch')

st.divider()

# ── 요약 테이블 ─────────────────────────────────────────────
st.subheader("모델별 수량 테이블")
st.dataframe(
    df[["모델", "전체", "가용", "폐기 예정", "폐기 완료"]],
    width='stretch',
    hide_index=True,
    column_config={
        "전체":    st.column_config.NumberColumn(format="%d"),
        "가용":    st.column_config.NumberColumn(format="%d"),
        "폐기 예정": st.column_config.NumberColumn(format="%d"),
        "폐기 완료": st.column_config.NumberColumn(format="%d"),
    },
)
