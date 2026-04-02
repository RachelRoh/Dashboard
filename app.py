import streamlit as st
from db.database import ensure_db

st.set_page_config(
    page_title="단말 관리 시스템",
    page_icon="📱",
    layout="wide",
    initial_sidebar_state="expanded",
)

ensure_db()

st.title("📱 단말 관리 시스템")
st.caption("그룹 내 단말 현황 및 대여 관리 대시보드")

st.divider()

# ── 페이지 안내 ─────────────────────────────────────────────
st.subheader("📖 페이지 안내")

col1, col2 = st.columns(2)
with col1:
    st.info(
        "**📊 단말 현황 요약**\n\n"
        "전체 단말 수량을 모델별 파이 차트로 확인하고, "
        "가용·폐기 예정·폐기 완료 현황을 한눈에 파악합니다."
    )
    st.info(
        "**📋 모델별 현황**\n\n"
        "모델 탭에서 각 모델의 보유 현황과 단말별 상태·배정 파트를 확인합니다."
    )
    st.info(
        "**🗑️ 폐기 현황**\n\n"
        "미사용·고장 처리된 단말의 폐기 대기 목록을 관리하고, "
        "폐기 처리 후 완료 이력을 확인합니다."
    )
with col2:
    st.info(
        "**👥 파트별 현황**\n\n"
        "파트 탭에서 보유 단말 목록을 확인하고, 단말 추가·삭제(미사용/고장/이관)를 처리합니다."
    )
    st.info(
        "**🔑 대여 현황**\n\n"
        "현재 대여 중인 단말 목록, 전체 대여 이력 조회 및 신규 대여 등록을 처리합니다."
    )
