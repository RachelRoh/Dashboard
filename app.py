import streamlit as st
from db.database import ensure_db

st.set_page_config(
    page_title="단말 관리 시스템",
    page_icon="🕵️",
    layout="wide",
    initial_sidebar_state="expanded",
)

ensure_db()

pg = st.navigation([
    st.Page("home.py",                       title="페이지 안내",   icon="📖"),
    st.Page("pages/1_summary.py",            title="단말 현황 요약", icon="📊"),
    st.Page("pages/2_model.py",              title="모델별 현황",   icon="📱"),
    st.Page("pages/3_part.py",               title="파트별 현황",   icon="👥"),
    st.Page("pages/4_rental.py",             title="대여 현황",     icon="📒"),
    st.Page("pages/5_disposal.py",           title="폐기 현황",     icon="🗑️"),
])
pg.run()
