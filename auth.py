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
from requests_oauthlib import OAuth2Session

# .env 파일 로드 (있는 경우)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv가 설치되지 않은 경우 무시

# OAuth 2.0 클라이언트 설정
# Google Cloud Console에서 발급받은 클라이언트 ID와 시크릿을 사용
# 환경 변수에서 가져오거나, 없으면 기본값 사용
CLIENT_CONFIG = {
    "web": {
        "client_id": os.getenv("GOOGLE_CLIENT_ID", "403626382842-512spe9nk3dvj2omjj2iqe1880k39btu.apps.googleusercontent.com"),
        "client_secret": os.getenv("GOOGLE_CLIENT_SECRET", "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"),
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "redirect_uris": [
            "http://localhost:8501",
            "http://localhost:8502",
            "http://localhost:8503",
            "http://127.0.0.1:8501",
            "http://127.0.0.1:8502",
            "http://127.0.0.1:8503",
            "https://appstore-review-analyzer.streamlit.app/",
            "https://appstore-review-analyzer.streamlit.app"
        ]
    }
}

def get_redirect_uri():
    """현재 환경에 맞는 리디렉션 URI 반환"""
    try:
        # 1. .env 또는 환경 변수에 직접 설정된 리디렉션 URI가 있으면 최우선 사용
        manual_redirect_uri = os.getenv("REDIRECT_URI")
        if manual_redirect_uri:
            return manual_redirect_uri

        # 2. Streamlit Cloud 환경 확인
        # Streamlit Cloud에서는 여러 환경 변수가 설정됨
        is_streamlit_cloud = (
            os.getenv("STREAMLIT_SERVER_BASE_URL") or
            os.getenv("STREAMLIT_BASE_URL_PATH") or
            os.getenv("STREAMLIT_SERVER_PORT") == "8501" or
            st.get_option("server.headless")  # Streamlit Cloud는 headless 모드
        )
        
        if is_streamlit_cloud:
            # Streamlit Cloud 환경
            base_url = os.getenv("STREAMLIT_SERVER_BASE_URL", "https://appstore-review-analyzer.streamlit.app")
            base_url = base_url.rstrip('/')
            return f"{base_url}/"
        else:
            # 로컬 환경
            # 로컬 개발 환경에서 HTTP 허용
            os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
            return "http://localhost:8501"
    except:
        # 오류 발생 시 기본값 사용 (배포 환경으로 가정)
        return "https://appstore-review-analyzer.streamlit.app/"

SCOPES = ['openid', 'https://www.googleapis.com/auth/userinfo.email', 'https://www.googleapis.com/auth/userinfo.profile']

def get_flow():
    """OAuth Flow 객체 생성"""
    redirect_uri = get_redirect_uri()
    client_config = CLIENT_CONFIG['web']
    
    # OAuth2Session 생성
    oauth = OAuth2Session(
        client_id=client_config['client_id'],
        redirect_uri=redirect_uri,
        scope=SCOPES
    )
    
    # 로컬 환경에서는 HTTPS 강제 해제
    if redirect_uri.startswith('http://'):
        oauth.enforce_https = False
    
    # Flow 객체 생성
    flow = Flow(
        oauth,
        client_type='web',
        client_config=CLIENT_CONFIG
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
    
    try:
        user_info_response = requests.get(
            'https://www.googleapis.com/oauth2/v2/userinfo',
            headers={'Authorization': f'Bearer {credentials.token}'},
            timeout=10
        )
        user_info_response.raise_for_status()  # HTTP 오류 확인
        return user_info_response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"사용자 정보 조회 실패: {str(e)}")
        raise
    except Exception as e:
        st.error(f"사용자 정보 처리 오류: {str(e)}")
        raise

def check_authentication():
    """인증 상태 확인 (개발자 우회 접속 포함)"""
    # 1. 개발자 우회 접속 확인
    query_params = st.query_params
    dev_password_input = query_params.get("dev", None)
    
    if dev_password_input:
        dev_password_secret = None
        try:
            # st.secrets에서 비밀번호 가져오기
            dev_password_secret = st.secrets.get("DEV_PASSWORD", None)
        except:
            pass
            
        # st.secrets가 안 되면 파일 직접 읽기 시도 (로컬 개발용)
        if not dev_password_secret:
            try:
                import toml
                with open(".streamlit/secrets.toml", "r") as f:
                    secrets_data = toml.load(f)
                    dev_password_secret = secrets_data.get("DEV_PASSWORD")
            except:
                pass
        
        # 비밀번호가 설정되어 있고 입력값과 일치하는지 확인
        if dev_password_secret and str(dev_password_input) == str(dev_password_secret):
            # 인증 정보 강제 설정 (우회)
            st.session_state.authenticated = True
            st.session_state.user_info = {
                'email': 'developer@bypass.local',
                'name': 'Developer',
                'verified_email': True
            }
            st.session_state.credentials = {'token': 'dev_bypass_token'}
            
            # URL에서 dev 파라미터 제거
            try:
                new_params = {}
                for key, value in query_params.items():
                    if key != 'dev':
                        new_params[key] = value
                st.query_params = new_params
            except:
                pass
            
            st.toast("🔧 개발자 모드로 로그인되었습니다.", icon="🛠️")
            return True

    # 2. 기존 세션 인증 확인
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'user_info' not in st.session_state:
        st.session_state.user_info = None
    if 'credentials' not in st.session_state:
        st.session_state.credentials = None
    
    # 인증 상태와 사용자 정보가 모두 있어야 인증된 것으로 간주
    is_authenticated = (
        st.session_state.get('authenticated', False) and 
        st.session_state.get('user_info') is not None and
        isinstance(st.session_state.get('user_info'), dict) and
        len(st.session_state.get('user_info', {})) > 0
    )
    
    return is_authenticated

def handle_oauth_callback():
    """OAuth 콜백 처리"""
    query_params = st.query_params
    
    # 세션 상태 초기화
    if 'processed_oauth_codes' not in st.session_state:
        st.session_state.processed_oauth_codes = set()
    if 'oauth_processing' not in st.session_state:
        st.session_state.oauth_processing = False
    
    # 이미 인증되어 있고 사용자 정보가 있으면 처리하지 않음
    if (st.session_state.get('authenticated', False) and 
        st.session_state.get('user_info') is not None):
        # query params에 code가 있으면 제거만 시도
        if 'code' in query_params or 'state' in query_params:
            try:
                # 기존 params를 순회하면서 code, state 제외하고 다시 설정
                params_to_keep = {}
                has_code_or_state = False
                for k, v in query_params.items():
                    if k not in ['code', 'state']:
                        params_to_keep[k] = v
                    else:
                        has_code_or_state = True
                
                # code나 state가 있었으면 URL 정리
                if has_code_or_state:
                    st.query_params.clear()
                    for key, value in params_to_keep.items():
                        st.query_params[key] = value
            except:
                pass
        return
    
    if 'code' in query_params:
        code = query_params.get('code', '')
        
        # 이미 처리된 코드면 무시하고 query params만 제거
        if code in st.session_state.processed_oauth_codes:
            try:
                params_to_keep = {}
                for k, v in query_params.items():
                    if k not in ['code', 'state']:
                        params_to_keep[k] = v
                
                st.query_params.clear()
                for key, value in params_to_keep.items():
                    st.query_params[key] = value
            except:
                pass
            return
        
        # 콜백 처리 중 플래그 확인 (무한 루프 방지)
        if st.session_state.get('oauth_processing', False):
            return
        
        # 콜백 처리 중 플래그 설정
        st.session_state.oauth_processing = True
        
        try:
            state = query_params.get('state', '')
            
            # 현재 환경에 맞는 리디렉션 URI 가져오기
            redirect_uri = get_redirect_uri()
            
            # authorization_response URL 구성
            authorization_response = f"{redirect_uri}?code={code}"
            if state:
                authorization_response += f"&state={state}"
            
            flow = get_flow()
            
            try:
                flow.fetch_token(authorization_response=authorization_response)
            except Exception as e:
                st.error(f"❌ 토큰 획득 실패: {str(e)}")
                raise
            
            credentials = flow.credentials
            
            # 사용자 정보 가져오기
            try:
                user_info = get_user_info(credentials)
            except Exception as e:
                st.error(f"❌ 사용자 정보 조회 실패")
                raise
            
            # 세션 상태에 저장 (중요: 먼저 저장)
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
            
            # 처리된 코드로 표시
            st.session_state.processed_oauth_codes.add(code)
            
            # 콜백 처리 완료 플래그 해제
            st.session_state.oauth_processing = False
            
            # 인증 완료 플래그 설정
            st.session_state.oauth_success = True
            
            # URL에서 code와 state 제거 (가능한 경우만)
            try:
                params_to_keep = {}
                for k, v in query_params.items():
                    if k not in ['code', 'state']:
                        params_to_keep[k] = v
                
                st.query_params.clear()
                for key, value in params_to_keep.items():
                    st.query_params[key] = value
            except:
                # query params 수정 실패는 무시
                pass
            
            st.success("✅ 로그인 성공!")
            st.rerun()
            
        except Exception as e:
            # 오류 발생 시 플래그 해제
            st.session_state.oauth_processing = False
            st.error(f"인증 중 오류 발생: {str(e)}")
            # 기존 인증 상태는 유지

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

