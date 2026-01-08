"""
Google OAuth 인증 모듈
온보딩에서 Google 계정으로 로그인 처리
"""

import streamlit as st
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
import os
import json
from urllib.parse import urlparse, parse_qs

# .env 파일 로드 (있는 경우)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv가 설치되지 않은 경우 무시

# OAuth 2.0 클라이언트 설정
# Google Cloud Console에서 발급받은 클라이언트 ID와 시크릿을 사용
CLIENT_CONFIG = {
    "web": {
        "client_id": os.getenv("GOOGLE_CLIENT_ID", ""),
        "client_secret": os.getenv("GOOGLE_CLIENT_SECRET", ""),
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "redirect_uris": ["http://localhost:8501"]
    }
}

SCOPES = ['openid', 'https://www.googleapis.com/auth/userinfo.email', 'https://www.googleapis.com/auth/userinfo.profile']

def get_flow():
    """OAuth Flow 객체 생성"""
    flow = Flow.from_client_config(
        CLIENT_CONFIG,
        scopes=SCOPES,
        redirect_uri="http://localhost:8501"
    )
    return flow

def get_authorization_url():
    """인증 URL 생성"""
    flow = get_flow()
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent'
    )
    return authorization_url, state

def get_user_info(credentials):
    """사용자 정보 가져오기"""
    import requests
    
    user_info_response = requests.get(
        'https://www.googleapis.com/oauth2/v2/userinfo',
        headers={'Authorization': f'Bearer {credentials.token}'}
    )
    return user_info_response.json()

def check_authentication():
    """인증 상태 확인"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'user_info' not in st.session_state:
        st.session_state.user_info = None
    if 'credentials' not in st.session_state:
        st.session_state.credentials = None
    
    return st.session_state.authenticated

def handle_oauth_callback():
    """OAuth 콜백 처리"""
    query_params = st.query_params
    
    if 'code' in query_params:
        try:
            # 현재 URL에서 authorization response 구성
            code = query_params.get('code', '')
            state = query_params.get('state', '')
            
            # Streamlit의 기본 URL 사용
            redirect_uri = "http://localhost:8501"
            
            # authorization_response URL 구성
            authorization_response = f"{redirect_uri}?code={code}"
            if state:
                authorization_response += f"&state={state}"
            
            flow = get_flow()
            flow.fetch_token(authorization_response=authorization_response)
            
            credentials = flow.credentials
            
            # 사용자 정보 가져오기
            user_info = get_user_info(credentials)
            
            # 세션 상태에 저장
            st.session_state.authenticated = True
            st.session_state.user_info = user_info
            st.session_state.credentials = {
                'token': credentials.token,
                'refresh_token': credentials.refresh_token,
                'token_uri': credentials.token_uri,
                'client_id': credentials.client_id,
                'client_secret': credentials.client_secret,
                'scopes': credentials.scopes
            }
            
            # URL에서 code와 state 제거
            new_params = dict(st.query_params)
            if 'code' in new_params:
                del new_params['code']
            if 'state' in new_params:
                del new_params['state']
            st.query_params = new_params
            st.rerun()
            
        except Exception as e:
            st.error(f"인증 오류: {str(e)}")
            st.session_state.authenticated = False

def show_login_page():
    """로그인 페이지 표시"""
    st.title("🔐 로그인")
    st.markdown("---")
    
    st.markdown("### Google 계정으로 로그인하세요")
    st.info("📱 앱스토어 리뷰 분석 도구를 사용하려면 Google 계정으로 로그인해주세요.")
    
    # 환경 변수 확인
    if not CLIENT_CONFIG["web"]["client_id"] or not CLIENT_CONFIG["web"]["client_secret"]:
        st.error("⚠️ Google OAuth 설정이 필요합니다.")
        st.markdown("""
        **설정 방법:**
        1. Google Cloud Console에서 OAuth 2.0 클라이언트 ID를 생성하세요
        2. 환경 변수를 설정하세요:
           - `GOOGLE_CLIENT_ID`: 클라이언트 ID
           - `GOOGLE_CLIENT_SECRET`: 클라이언트 시크릿
        3. 리다이렉트 URI에 `http://localhost:8501`을 추가하세요
        """)
        return
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        try:
            auth_url, state = get_authorization_url()
            st.session_state.oauth_state = state
            
            # Google 로그인 버튼
            st.markdown(f"""
            <div style="text-align: center; margin: 20px 0;">
                <a href="{auth_url}" style="
                    display: inline-block;
                    background-color: #4285f4;
                    color: white;
                    padding: 12px 24px;
                    text-decoration: none;
                    border-radius: 4px;
                    font-weight: 500;
                    font-size: 16px;
                ">
                    🔵 Google로 로그인
                </a>
            </div>
            """, unsafe_allow_html=True)
        except Exception as e:
            st.error(f"로그인 오류: {str(e)}")
    
    st.markdown("---")
    st.caption("로그인하면 앱스토어 리뷰 분석 도구를 사용할 수 있습니다.")

