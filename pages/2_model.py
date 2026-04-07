import streamlit as st
from queries.equipment import get_model_summary, get_all_equipment

_, _btn_col = st.columns([8, 2])
with _btn_col:
    if st.button("새로 고침"):
        get_model_summary.clear()
        get_all_equipment.clear()
        st.rerun()

st.title("📱 모델별 현황")

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

        c1, c2, c3, c4 = st.columns(4)
        c1.markdown(
            "<p style='font-size:.875rem;margin-bottom:0'>가용</p>"
            f"<p style='font-size:2rem;font-weight:700;color:#FF4B4B;margin:0'>{int(row['가용'])}</p>",
            unsafe_allow_html=True,
        )
        c2.metric("미사용", int(row["미사용"]))
        c3.metric("고장", int(row["고장"]))
        c4.metric("폐기", int(row["폐기"]))

        status_order = {"가용": 0, "미사용": 1, "고장": 2, "폐기": 3}
        model_df = (
            all_df[all_df["모델"] == model]
            .assign(상태순서=lambda d: d["상태"].map(status_order))
            .sort_values(["상태순서", "시리얼번호"])
            .drop(columns="상태순서")
            .reset_index(drop=True)
        )
        _cols = ["시리얼번호", "상태", "보유팀", "소유자", "등록일시", "비고"]
        _disp = model_df[_cols].copy()
        _disp["등록일"] = _disp["등록일시"].str[:10]
        _disp = _disp.rename(columns={"보유팀": "소유팀"})
        st.dataframe(
            _disp[["시리얼번호", "상태", "소유팀", "소유자", "등록일", "비고"]],
            width='stretch',
            hide_index=True,
        )
