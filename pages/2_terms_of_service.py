"""
서비스 이용약관 페이지
"""

import streamlit as st
from pathlib import Path

# 페이지 설정
st.set_page_config(
    page_title="서비스 이용약관",
    page_icon="📋",
    layout="wide"
)

# 서비스 이용약관 파일 읽기
terms_path = Path(__file__).parent.parent / "terms_of_service.md"

if terms_path.exists():
    with open(terms_path, "r", encoding="utf-8") as f:
        terms_content = f.read()
    
    st.title("📋 서비스 이용약관")
    st.markdown("---")
    st.markdown(terms_content)
else:
    st.error("서비스 이용약관 파일을 찾을 수 없습니다.")

