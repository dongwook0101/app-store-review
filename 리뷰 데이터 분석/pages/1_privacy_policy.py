"""
개인정보처리방침 페이지
"""

import streamlit as st
from pathlib import Path

# 페이지 설정
st.set_page_config(
    page_title="개인정보처리방침",
    page_icon="🔒",
    layout="wide"
)

# 개인정보처리방침 파일 읽기
privacy_policy_path = Path(__file__).parent.parent / "privacy_policy.md"

if privacy_policy_path.exists():
    with open(privacy_policy_path, "r", encoding="utf-8") as f:
        privacy_policy_content = f.read()
    
    st.title("🔒 개인정보처리방침")
    st.markdown("---")
    st.markdown(privacy_policy_content)
else:
    st.error("개인정보처리방침 파일을 찾을 수 없습니다.")

