"""
Google OAuth 인증 모듈
온보딩에서 Google 계정으로 로그인 처리
"""

import streamlit as st
from google_auth_oauthlib.flow import Flow
import os


# .env 파일 로드 (있는 경우)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv가 설치되지 않은 경우 무시

def _get_secret(key, default=""):
    """st.secrets에서 안전하게 값을 가져옴 (없으면 default 반환)"""
    try:
        return st.secrets.get(key, default) or default
    except Exception:
        return default

CLOUD_REDIRECT_URI = "https://appstore-review-analyzer.streamlit.app/"
LOCAL_REDIRECT_URI = "http://localhost:8501"

def get_redirect_uri():
    """현재 환경에 맞는 리디렉션 URI 반환"""
    # 1. Secrets 또는 환경변수에 명시된 값 최우선
    uri = _get_secret("REDIRECT_URI", "") or os.getenv("REDIRECT_URI", "")
    if uri:
        return uri

    # 2. STREAMLIT_SHARING_MODE 또는 HOME 경로로 Streamlit Cloud 판단
    #    Streamlit Cloud는 HOME=/home/adminuser 환경
    home = os.getenv("HOME", "")
    if "adminuser" in home or os.getenv("STREAMLIT_SHARING_MODE"):
        return CLOUD_REDIRECT_URI

    # 3. 로컬 기본값
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    return LOCAL_REDIRECT_URI

SCOPES = ['openid', 'https://www.googleapis.com/auth/userinfo.email', 'https://www.googleapis.com/auth/userinfo.profile']

def _get_credentials():
    """OAuth 클라이언트 ID/Secret 반환"""
    client_id = os.getenv("GOOGLE_CLIENT_ID") or _get_secret("GOOGLE_CLIENT_ID", "403626382842-512spe9nk3dvj2omjj2iqe1880k39btu.apps.googleusercontent.com")
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET") or _get_secret("GOOGLE_CLIENT_SECRET", "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")
    return client_id, client_secret

def get_flow(state=None):
    """OAuth Flow 객체 생성"""
    redirect_uri = get_redirect_uri()
    client_id, client_secret = _get_credentials()

    if redirect_uri.startswith('http://'):
        os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

    client_config = {
        "web": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "redirect_uris": [redirect_uri]
        }
    }

    flow = Flow.from_client_config(
        client_config,
        scopes=SCOPES,
        redirect_uri=redirect_uri,
        state=state
    )
    return flow

def get_authorization_url():
    """인증 URL 직접 생성 (Flow 라이브러리 우회)"""
    import secrets as sec
    from urllib.parse import urlencode

    client_id, _ = _get_credentials()
    redirect_uri = get_redirect_uri()
    state = sec.token_urlsafe(32)

    params = {
        'client_id': client_id,
        'redirect_uri': redirect_uri,
        'scope': ' '.join(SCOPES),
        'response_type': 'code',
        'access_type': 'offline',
        'prompt': 'consent',
        'state': state,
    }
    auth_url = 'https://accounts.google.com/o/oauth2/v2/auth?' + urlencode(params)
    return auth_url, state

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
    import requests as req

    query_params = st.query_params

    if 'processed_oauth_codes' not in st.session_state:
        st.session_state.processed_oauth_codes = set()

    if 'code' not in query_params:
        st.write("🔍 [콜백] code 파라미터 없음 → 건너뜀")
        return

    code = query_params.get('code', '')
    st.write(f"🔍 [콜백] code 감지됨: {code[:20]}...")

    if code in st.session_state.processed_oauth_codes:
        st.write("🔍 [콜백] 이미 처리된 코드 → 건너뜀")
        return

    if st.session_state.get('oauth_processing', False):
        st.write("🔍 [콜백] oauth_processing=True → 건너뜀")
        return

    st.session_state.oauth_processing = True
    success = False

    try:
        redirect_uri = get_redirect_uri()
        st.write(f"🔍 [콜백] redirect_uri: {redirect_uri}")

        client_id, client_secret = _get_credentials()

        st.write("🔍 [콜백] Google 토큰 요청 중...")
        token_response = req.post(
            'https://oauth2.googleapis.com/token',
            data={
                'code': code,
                'client_id': client_id,
                'client_secret': client_secret,
                'redirect_uri': redirect_uri,
                'grant_type': 'authorization_code'
            },
            timeout=10
        )
        token_data = token_response.json()
        st.write(f"🔍 [콜백] 토큰 응답: { {k: v for k, v in token_data.items() if k != 'access_token'} }")

        if 'error' in token_data:
            raise Exception(f"토큰 교환 실패: {token_data.get('error')} - {token_data.get('error_description', '')}")

        access_token = token_data['access_token']
        st.write("🔍 [콜백] 액세스 토큰 획득 성공")

        user_response = req.get(
            'https://www.googleapis.com/oauth2/v2/userinfo',
            headers={'Authorization': f'Bearer {access_token}'},
            timeout=10
        )
        user_response.raise_for_status()
        user_info = user_response.json()
        st.write(f"🔍 [콜백] 사용자 정보: {user_info.get('email')}")

        st.session_state.authenticated = True
        st.session_state.user_info = user_info
        st.session_state.credentials = {
            'token': access_token,
            'refresh_token': token_data.get('refresh_token'),
        }
        st.session_state.processed_oauth_codes.add(code)
        st.session_state.oauth_processing = False
        st.session_state.oauth_success = True
        success = True
        st.write("🔍 [콜백] 인증 완료! rerun 예정...")

    except Exception as e:
        st.session_state.oauth_processing = False
        st.session_state.oauth_error = str(e)
        st.write(f"🔍 [콜백] 오류 발생: {e}")

    if success:
        st.rerun()

def show_login_page():
    """로그인 페이지 표시"""
    st.title("🔐 로그인")
    st.markdown("---")
    
    st.markdown("### Google 계정으로 로그인하세요")
    st.info("📱 앱스토어 리뷰 분석 도구를 사용하려면 Google 계정으로 로그인해주세요.")
    
    client_id, client_secret = _get_credentials()
    if not client_id or not client_secret:
        st.error("⚠️ Google OAuth 설정이 필요합니다. Streamlit Cloud Secrets에 GOOGLE_CLIENT_ID와 GOOGLE_CLIENT_SECRET을 등록하세요.")
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

