"""
앱스토어 리뷰 분석 웹 UI 애플리케이션
Streamlit을 사용한 사용자 친화적 인터페이스
"""

import streamlit as st
import json
import pandas as pd
import requests
import time
from datetime import datetime
import os
import io
import re
import streamlit.components.v1 as _stc
from auth import check_authentication, handle_oauth_callback, show_login_page

# ── 쿠키 헬퍼 (st.context.cookies 읽기 + JS 쓰기) ─────────────────────────
def _get_cookie(name: str) -> str | None:
    try:
        return st.context.cookies.get(name)
    except Exception:
        return None

def _set_cookie(name: str, value: str, days: int = 365) -> None:
    from datetime import timedelta
    expires = (datetime.now() + timedelta(days=days)).strftime("%a, %d %b %Y %H:%M:%S GMT")
    safe = value.replace('"', '\\"').replace('\n', '').replace('\r', '')
    _stc.html(
        f'<script>document.cookie="{name}={safe}; expires={expires}; path=/; SameSite=Lax";</script>',
        height=0,
    )

def _delete_cookie(name: str) -> None:
    _stc.html(
        f'<script>document.cookie="{name}=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/";</script>',
        height=0,
    )

# 페이지 설정
st.set_page_config(
    page_title="앱스토어 리뷰 분석",
    layout="wide"
)

# 전역 스타일
st.markdown("""
<style>
/* ── 프리텐다드 폰트 ── */
@import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');

* {
    font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
}

/* ── 기본 배경 ── */
.stApp {
    background-color: #E5E5FF;
}
/* 메인 컨텐츠 영역 배경 */
section.main, section.main > div {
    background-color: #E5E5FF;
}

/* ── 사이드바 ── */
section[data-testid="stSidebar"] {
    background: linear-gradient(160deg, #1e1b4b 0%, #312e81 100%);
    border-right: none;
}
section[data-testid="stSidebar"] * {
    color: #e0e7ff !important;
}
section[data-testid="stSidebar"] .stTextInput input,
section[data-testid="stSidebar"] .stSelectbox select {
    background-color: rgba(255,255,255,0.08) !important;
    border: 1px solid rgba(255,255,255,0.15) !important;
    color: #000000 !important;
    border-radius: 8px !important;
}
section[data-testid="stSidebar"] .stMultiSelect [data-baseweb="select"] > div,
section[data-testid="stSidebar"] .stMultiSelect [data-baseweb="select"] > div > div,
section[data-testid="stSidebar"] .stMultiSelect div[class*="ValueContainer"],
section[data-testid="stSidebar"] .stMultiSelect div[class*="control"] {
    background-color: transparent !important;
    border-color: rgba(255,255,255,0.15) !important;
    border-radius: 8px !important;
}
section[data-testid="stSidebar"] .stSlider .stSlider {
    color: #818cf8 !important;
}
section[data-testid="stSidebar"] hr {
    border-color: rgba(255,255,255,0.15) !important;
    margin: 0.6rem 0 !important;
}
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 {
    color: #fff !important;
    font-weight: 600 !important;
}
section[data-testid="stSidebar"] > div {
    padding-top: 1.5rem !important;
}
section[data-testid="stSidebar"] .stVerticalBlock {
    gap: 0.4rem !important;
}
section[data-testid="stSidebar"] .element-container {
    margin-bottom: 0 !important;
}
section[data-testid="stSidebar"] .stButton button {
    background: rgba(255,255,255,0.12) !important;
    border: 1px solid rgba(255,255,255,0.2) !important;
    color: #fff !important;
    border-radius: 8px !important;
    transition: background 0.2s;
}
section[data-testid="stSidebar"] .stButton button:hover {
    background: rgba(255,255,255,0.2) !important;
}
section[data-testid="stSidebar"] .stButton [data-testid="baseButton-primary"] {
    background: linear-gradient(135deg, #6366f1, #818cf8) !important;
    border: none !important;
}

/* ── 메인 영역 상단 여백 줄이기 ── */
.block-container {
    padding-top: 1.5rem !important;
    padding-bottom: 2rem !important;
    max-width: 1200px;
}

/* ── 페이지 타이틀 ── */
h1 {
    color: #1e1b4b !important;
    font-weight: 700 !important;
    font-size: 1.7rem !important;
}
h2 {
    color: #312e81 !important;
    font-weight: 600 !important;
    font-size: 1.2rem !important;
}
h3 {
    color: #4338ca !important;
    font-weight: 600 !important;
}

/* ── 메트릭 카드 ── */
[data-testid="metric-container"] {
    background: #fff;
    border: 1px solid #e0e7ff;
    border-radius: 14px;
    padding: 1.1rem 1.3rem !important;
    box-shadow: 0 2px 8px rgba(99,102,241,0.07);
}
[data-testid="metric-container"] label {
    color: #6b7280 !important;
    font-size: 0.78rem !important;
    font-weight: 600 !important;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}
[data-testid="metric-container"] [data-testid="stMetricValue"] {
    color: #1e1b4b !important;
    font-size: 1.8rem !important;
    font-weight: 700 !important;
}

/* ── 분석 시작 버튼 ── */
.stButton button[kind="primary"] {
    background: linear-gradient(135deg, #6366f1 0%, #818cf8 100%) !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    letter-spacing: 0.02em;
    height: 2.7rem;
    box-shadow: 0 4px 12px rgba(99,102,241,0.3);
    transition: transform 0.15s, box-shadow 0.15s;
}
.stButton button[kind="primary"]:hover {
    transform: translateY(-1px);
    box-shadow: 0 6px 16px rgba(99,102,241,0.4);
}

/* ── 일반 버튼 ── */
.stButton button[kind="secondary"] {
    border-radius: 8px !important;
    border-color: #c7d2fe !important;
    color: #4338ca !important;
}

/* ── 다운로드 버튼 ── */
[data-testid="stDownloadButton"] button {
    border-radius: 8px !important;
    border: 1px solid #c7d2fe !important;
    color: #4338ca !important;
    font-weight: 500 !important;
    width: 100%;
}
[data-testid="stDownloadButton"] button:hover {
    background: #eef2ff !important;
}

/* ── 데이터프레임 ── */
[data-testid="stDataFrame"] {
    border-radius: 12px;
    overflow: hidden;
    border: 1px solid #e0e7ff;
    box-shadow: 0 2px 8px rgba(99,102,241,0.06);
}

/* ── 성공/경고/에러 메시지 ── */
[data-testid="stAlert"] {
    border-radius: 10px !important;
    border-left-width: 4px !important;
}

/* ── 섹션 카드 래퍼 ── */
.card {
    background: #fff;
    border-radius: 14px;
    padding: 1.3rem 1.5rem;
    border: 1px solid #e0e7ff;
    box-shadow: 0 2px 8px rgba(99,102,241,0.06);
    margin-bottom: 1rem;
}

/* ── 구분선 ── */
hr {
    border-color: #e0e7ff !important;
}

/* ── info 박스 ── */
[data-testid="stAlert"][kind="info"] {
    background: #eef2ff !important;
    border-left-color: #6366f1 !important;
    color: #3730a3 !important;
}

/* ── 탭 ── */
.stTabs [data-baseweb="tab-list"] {
    gap: 4px;
    background: #eef2ff;
    border-radius: 10px;
    padding: 4px;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 7px;
    font-weight: 500;
}
.stTabs [aria-selected="true"] {
    background: #fff !important;
    color: #4338ca !important;
    box-shadow: 0 1px 4px rgba(99,102,241,0.15);
}

/* ── 사이드바 입력 필드 텍스트 색상 ── */
section[data-testid="stSidebar"] input {
    color: #1e1b4b !important;
    background-color: rgba(255,255,255,0.9) !important;
}

/* ── progress bar ── */
.stProgress > div > div {
    background: linear-gradient(90deg, #6366f1, #818cf8) !important;
    border-radius: 4px;
}

/* ── multiselect 태그 ── */
[data-baseweb="tag"] {
    background: #eef2ff !important;
    color: #4338ca !important;
    border-radius: 6px !important;
}
/* 사이드바 multiselect 태그 */
section[data-testid="stSidebar"] [data-baseweb="tag"] {
    background: rgba(255,255,255,0.2) !important;
    color: #ffffff !important;
    border-radius: 6px !important;
}
section[data-testid="stSidebar"] [data-baseweb="tag"] span {
    color: #ffffff !important;
}

/* ── 차트 컨테이너 배경 보호 ── */
[data-testid="stVegaLiteChart"],
[data-testid="stArrowVegaLiteChart"],
[data-testid="stVegaLiteChart"] > div,
[data-testid="stArrowVegaLiteChart"] > div,
.vega-embed,
.vega-embed canvas,
canvas {
    background: #ffffff !important;
    border-radius: 10px;
}
[data-testid="element-container"]:has([data-testid="stVegaLiteChart"]),
[data-testid="element-container"]:has([data-testid="stArrowVegaLiteChart"]) {
    background: #ffffff;
    border-radius: 12px;
    padding: 0.5rem;
    border: 1px solid #e0e7ff;
}
</style>
""", unsafe_allow_html=True)

# ── [DEBUG] 현재 상태 출력 ────────────────────────────────────────────

# ── OAuth 콜백을 가장 먼저 처리 (CookieManager 이전) ──────────────────
if 'code' in st.query_params and not st.session_state.get('authenticated'):
    handle_oauth_callback()
    # handle_oauth_callback 내부에서 st.rerun()이 호출되므로 아래로 내려오지 않음

# ── 개발자 우회 접속 처리 ──────────────────────────────────────────────
if 'dev' in st.query_params and not st.session_state.get('authenticated'):
    from auth import check_authentication as _check
    _check()  # dev 파라미터 처리 (check_authentication 내부에서 처리됨)

# ── 쿠키에서 세션 복원 (새로고침 시) ─────────────────────────────────────
if not st.session_state.get('authenticated'):
    _user_cookie = _get_cookie("user_info")
    if _user_cookie:
        try:
            _stored = json.loads(_user_cookie)
            if _stored.get('email'):
                st.session_state.authenticated = True
                st.session_state.user_info = _stored
        except Exception:
            pass

# ── 로그인 성공 직후 쿠키 저장 (최초 1회) ─────────────────────────────────
if st.session_state.get('authenticated') and st.session_state.get('user_info'):
    if not st.session_state.get('user_cookie_saved'):
        try:
            _set_cookie("user_info", json.dumps(st.session_state.user_info, ensure_ascii=False))
        except Exception:
            pass
        st.session_state.user_cookie_saved = True

# ── 인증 상태 확인 ─────────────────────────────────────────────────────
is_authenticated = check_authentication()

# 인증되지 않은 경우 로그인 페이지 표시
if not is_authenticated:
    if st.session_state.get('oauth_error'):
        st.error(f"로그인 오류: {st.session_state.pop('oauth_error')}")
    show_login_page()
    st.stop()

# ── DB 초기화 (인증 후 최초 1회) ──────────────────────────────────────
if 'db_initialized' not in st.session_state:
    try:
        from db import init_db
        init_db()
    except Exception:
        pass
    st.session_state.db_initialized = True

# 세션 상태 초기화
if 'reviews_data' not in st.session_state:
    st.session_state.reviews_data = None
if 'app_id' not in st.session_state:
    st.session_state.app_id = None
if 'app_info' not in st.session_state:
    st.session_state.app_info = None

def fetch_reviews_play_store(app_id, country='us', count=200, start_year=None, end_year=None):
    """
    google-play-scraper를 사용하여 Play Store 리뷰를 수집합니다.
    continuation_token으로 페이지네이션하며 start_year 이전 도달 시 중단합니다.
    """
    try:
        from google_play_scraper import reviews as gp_reviews, Sort
    except ImportError:
        st.error("google-play-scraper 라이브러리가 필요합니다. requirements.txt를 확인하세요.")
        return []

    lang_map = {
        'us': 'en', 'gb': 'en', 'ca': 'en', 'au': 'en',
        'kr': 'ko', 'jp': 'ja', 'cn': 'zh', 'tw': 'zh', 'hk': 'zh',
        'de': 'de', 'fr': 'fr', 'it': 'it', 'es': 'es', 'br': 'pt',
        'ru': 'ru', 'nl': 'nl', 'se': 'sv', 'pl': 'pl', 'tr': 'tr',
        'th': 'th', 'id': 'id', 'vn': 'vi', 'in': 'hi',
        'sa': 'ar', 'ae': 'ar', 'sg': 'en', 'ph': 'en', 'my': 'en',
    }
    lang = lang_map.get(country.lower(), 'en')

    reviews_list = []
    continuation_token = None
    batch_size = 200
    max_total = 5000  # 무한루프 방지

    while len(reviews_list) < max_total:
        try:
            result, continuation_token = gp_reviews(
                app_id,
                lang=lang,
                country=country.lower(),
                sort=Sort.NEWEST,
                count=batch_size,
                continuation_token=continuation_token,
            )
        except Exception as e:
            st.warning(f"Play Store 리뷰 수집 오류 ({country}): {e}")
            break

        if not result:
            break

        reached_start = False
        for r in result:
            date = r.get('at')
            if date:
                if end_year and date.year > end_year:
                    continue
                if start_year and date.year < start_year:
                    reached_start = True
                    continue
            reviews_list.append({
                'title': '',
                'review': r.get('content', ''),
                'rating': r.get('score', 0),
                'date': date.strftime('%Y-%m-%dT%H:%M:%S') if date else '',
                'country': country.upper(),
                'author': r.get('userName', ''),
            })

        # start_year 이전 데이터에 도달했거나 더 이상 토큰 없으면 중단
        if reached_start or continuation_token is None:
            break

        # count 제한에 도달
        if len(reviews_list) >= count:
            break

    return reviews_list


def fetch_reviews_rss(app_id, country='us', max_pages=10, start_year=None, end_year=None):
    """
    iTunes RSS API를 사용하여 리뷰 데이터를 수집합니다.
    start_year와 end_year가 지정되면 해당 기간의 리뷰만 수집합니다.
    """
    all_reviews = []
    
    # 국가 코드는 그대로 사용
    cc = country.lower()
    
    # 언어 코드 매핑 (주요 국가)
    lang_map = {
        'us': 'en', 'gb': 'en', 'ca': 'en', 'au': 'en', 'ie': 'en', 'nz': 'en',
        'kr': 'ko',
        'jp': 'ja',
        'cn': 'zh', 'tw': 'zh', 'hk': 'zh',
        'de': 'de', 'at': 'de', 'ch': 'de',
        'fr': 'fr', 'be': 'fr', 'lu': 'fr',
        'it': 'it',
        'es': 'es', 'mx': 'es', 'ar': 'es', 'cl': 'es', 'co': 'es', 'pe': 'es',
        'pt': 'pt', 'br': 'pt',
        'ru': 'ru',
        'nl': 'nl',
        'sv': 'sv', 'se': 'sv',
        'pl': 'pl',
        'tr': 'tr',
        'th': 'th',
        'id': 'id',
        'vi': 'vi', 'vn': 'vi',
        'hi': 'hi', 'in': 'hi',
        'ar': 'ar', 'sa': 'ar', 'ae': 'ar',
        'zh': 'zh',
        'my': 'en', 'sg': 'en', 'ph': 'en'
    }
    lang = lang_map.get(country.lower(), 'en')
    
    try:
        for page in range(1, max_pages + 1):
            url = f"https://itunes.apple.com/rss/customerreviews/page={page}/id={app_id}/sortby=mostrecent/json?l={lang}&cc={cc}"
            
            response = requests.get(url, timeout=10)
            
            if response.status_code != 200:
                break
            
            try:
                data = response.json()
            except json.JSONDecodeError:
                break
            
            if 'feed' not in data:
                break
            
            feed = data['feed']
            
            if 'entry' not in feed:
                break
            
            entries = feed['entry']
            
            for entry in entries:
                # 앱 정보 항목은 건너뛰기
                if 'im:name' in entry:
                    continue
                
                review_data = {}
                
                if 'im:rating' in entry:
                    review_data['rating'] = int(entry['im:rating']['label'])
                
                if 'title' in entry:
                    review_data['title'] = entry['title']['label']
                
                if 'content' in entry:
                    if isinstance(entry['content'], dict) and 'label' in entry['content']:
                        review_data['review'] = entry['content']['label']
                    elif isinstance(entry['content'], list) and len(entry['content']) > 0:
                        review_data['review'] = entry['content'][0].get('label', '')
                
                if 'author' in entry and 'name' in entry['author']:
                    review_data['author'] = entry['author']['name']['label']
                
                if 'updated' in entry:
                    review_data['date'] = entry['updated']['label']
                    
                    # 날짜 필터링
                    if start_year is not None or end_year is not None:
                        try:
                            review_date = pd.to_datetime(review_data['date'])
                            review_year = review_date.year
                            
                            if end_year and review_year > end_year:
                                continue  # 설정한 종료 년도보다 최신 리뷰는 건너뜀
                                
                            if start_year and review_year < start_year:
                                # RSS는 최신순으로 정렬되어 있으므로, 시작 년도보다 오래된 리뷰가 나오면
                                # 더 이상 수집할 필요가 없음 (페이지 순회 중단)
                                return all_reviews
                        except:
                            pass
                
                if 'im:version' in entry:
                    review_data['version'] = entry['im:version']['label']
                
                if review_data:
                    review_data['country'] = country.upper()
                    all_reviews.append(review_data)
            
            # 리뷰가 더 없으면 중단
            if len(entries) < 50:
                break
            
            time.sleep(0.3)  # API 호출 간 딜레이
        
        return all_reviews
    
    except Exception as e:
        # Streamlit 환경이 아닐 경우를 대비한 처리
        try:
            st.error(f"오류 발생: {str(e)}")
        except:
            print(f"오류 발생: {str(e)}")
        return None

def get_app_info(app_id):
    """앱 정보를 가져옵니다."""
    try:
        url = f"https://itunes.apple.com/lookup?id={app_id}"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('results') and len(data['results']) > 0:
                return data['results'][0]
    except:
        pass
    return None

# 메인 UI
st.markdown("""
<div style="
    background: linear-gradient(135deg, #6366f1 0%, #4338ca 100%);
    border-radius: 16px;
    padding: 1.4rem 2rem;
    margin-bottom: 1.5rem;
    display: flex;
    align-items: center;
    gap: 1rem;
">
    <div>
        <div style="color:rgba(255,255,255,0.2); font-size:0.8rem; font-weight:600; letter-spacing:0.08em; text-transform:uppercase; margin-bottom:0.3rem;">App Store &amp; Play Store Analytics</div>
        <div style="color:#fff; font-size:1.5rem; font-weight:700; margin:0;">📱 리뷰 분석 대시보드</div>
        <div style="color:rgba(255,255,255,0.2); font-size:0.85rem; margin-top:0.3rem;">앱스토어·플레이스토어 리뷰를 수집하고 인사이트를 발견하세요</div>
    </div>
</div>
""", unsafe_allow_html=True)

# 사이드바에 입력 폼
with st.sidebar:
    # 사이드바 공백 조정 CSS
    st.markdown("""
    <style>
    /* 사이드바 전체 공백 조정 */
    section[data-testid="stSidebar"] > div {
        padding-top: 0.5rem !important;
    }
    /* 로그인 섹션과 설정 섹션 사이 공백 줄이기 */
    section[data-testid="stSidebar"] .element-container {
        margin-bottom: 0.3rem !important;
    }
    /* 설정 헤더 위 공백 줄이기 */
    section[data-testid="stSidebar"] h2 {
        margin-top: 0.3rem !important;
        margin-bottom: 0.5rem !important;
    }
    /* 구분선 위 공백 줄이기 */
    section[data-testid="stSidebar"] hr {
        margin-top: 0.3rem !important;
        margin-bottom: 0.3rem !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # 사용자 정보 표시 (사이드바 상단)
    if st.session_state.user_info:
        email = st.session_state.user_info.get('email', 'Unknown')
        st.markdown(f"""
        <div style="
            background: rgba(255,255,255,0.1);
            border-radius: 10px;
            padding: 0.7rem 0.9rem;
            margin-bottom: 0.5rem;
            display: flex;
            align-items: center;
            gap: 0.6rem;
        ">
            <div style="
                width: 32px; height: 32px;
                background: linear-gradient(135deg, #818cf8, #c7d2fe);
                border-radius: 50%;
                display: flex; align-items: center; justify-content: center;
                font-size: 0.9rem; font-weight: 700; color: #1e1b4b; flex-shrink:0;
            ">{email[0].upper()}</div>
            <div style="overflow:hidden;">
                <div style="font-size:0.72rem; color:rgba(255,255,255,0.2);">로그인 계정</div>
                <div style="font-size:0.82rem; color:#fff; font-weight:500; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">{email}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("로그아웃", use_container_width=True):
            _logout_email = (st.session_state.user_info or {}).get('email', '')
            try:
                from tracker import close_user_session, log_event
                close_user_session(_logout_email)
                log_event(_logout_email, 'logout')
            except Exception:
                pass
            st.session_state.authenticated = False
            st.session_state.user_info = None
            st.session_state.credentials = None
            st.session_state.user_cookie_saved = False
            try:
                _delete_cookie("auth_token")
                _delete_cookie("user_info")
            except Exception:
                pass
            st.rerun()
        st.markdown("---")

    st.markdown("""
    <div style="font-size:0.7rem; color:rgba(255,255,255,0.2); text-transform:uppercase; letter-spacing:0.1em; font-weight:600; margin-bottom:0.5rem;">
    ⚙ 분석 설정
    </div>
    """, unsafe_allow_html=True)
    
    store_choice = st.radio(
        "스토어 선택",
        options=["App Store", "Play Store"],
        horizontal=True,
    )

    if store_choice == "App Store":
        app_id_input = st.text_input(
            "앱 ID",
            value="1510564828",
            help="App Store 앱 ID (숫자). 예: 1510564828",
        )
    else:
        app_id_input = st.text_input(
            "패키지명",
            value="com.kakao.talk",
            help="Play Store 패키지명. 예: com.kakao.talk",
        )
    
    st.markdown("---")
    
    st.subheader("📊 분석 옵션")
    
    # 국가 선택 옵션
    country_options = {
        'ALL': {'code': 'all', 'name': '🌍 전체 국가', 'emoji': '🌍'},
        'US': {'code': 'us', 'name': '🇺🇸 미국', 'emoji': '🇺🇸'},
        'KR': {'code': 'kr', 'name': '🇰🇷 한국', 'emoji': '🇰🇷'},
        'JP': {'code': 'jp', 'name': '🇯🇵 일본', 'emoji': '🇯🇵'},
        'CN': {'code': 'cn', 'name': '🇨🇳 중국', 'emoji': '🇨🇳'},
        'GB': {'code': 'gb', 'name': '🇬🇧 영국', 'emoji': '🇬🇧'},
        'CA': {'code': 'ca', 'name': '🇨🇦 캐나다', 'emoji': '🇨🇦'},
        'AU': {'code': 'au', 'name': '🇦🇺 호주', 'emoji': '🇦🇺'},
        'DE': {'code': 'de', 'name': '🇩🇪 독일', 'emoji': '🇩🇪'},
        'FR': {'code': 'fr', 'name': '🇫🇷 프랑스', 'emoji': '🇫🇷'},
        'IT': {'code': 'it', 'name': '🇮🇹 이탈리아', 'emoji': '🇮🇹'},
        'ES': {'code': 'es', 'name': '🇪🇸 스페인', 'emoji': '🇪🇸'},
        'BR': {'code': 'br', 'name': '🇧🇷 브라질', 'emoji': '🇧🇷'},
        'IN': {'code': 'in', 'name': '🇮🇳 인도', 'emoji': '🇮🇳'},
        'MX': {'code': 'mx', 'name': '🇲🇽 멕시코', 'emoji': '🇲🇽'},
        'RU': {'code': 'ru', 'name': '🇷🇺 러시아', 'emoji': '🇷🇺'},
        'NL': {'code': 'nl', 'name': '🇳🇱 네덜란드', 'emoji': '🇳🇱'},
        'SE': {'code': 'se', 'name': '🇸🇪 스웨덴', 'emoji': '🇸🇪'},
        'CH': {'code': 'ch', 'name': '🇨🇭 스위스', 'emoji': '🇨🇭'},
        'SG': {'code': 'sg', 'name': '🇸🇬 싱가포르', 'emoji': '🇸🇬'},
        'HK': {'code': 'hk', 'name': '🇭🇰 홍콩', 'emoji': '🇭🇰'},
        'TW': {'code': 'tw', 'name': '🇹🇼 대만', 'emoji': '🇹🇼'},
        'TH': {'code': 'th', 'name': '🇹🇭 태국', 'emoji': '🇹🇭'},
        'ID': {'code': 'id', 'name': '🇮🇩 인도네시아', 'emoji': '🇮🇩'},
        'PH': {'code': 'ph', 'name': '🇵🇭 필리핀', 'emoji': '🇵🇭'},
        'MY': {'code': 'my', 'name': '🇲🇾 말레이시아', 'emoji': '🇲🇾'},
        'VN': {'code': 'vn', 'name': '🇻🇳 베트남', 'emoji': '🇻🇳'},
        'PL': {'code': 'pl', 'name': '🇵🇱 폴란드', 'emoji': '🇵🇱'},
        'TR': {'code': 'tr', 'name': '🇹🇷 터키', 'emoji': '🇹🇷'},
        'SA': {'code': 'sa', 'name': '🇸🇦 사우디아라비아', 'emoji': '🇸🇦'},
        'AE': {'code': 'ae', 'name': '🇦🇪 UAE', 'emoji': '🇦🇪'}
    }
    
    selected_countries = st.multiselect(
        "분석할 국가 선택 (최대 2개 또는 전체 국가)",
        options=list(country_options.keys()),
        default=['US', 'KR'],
        format_func=lambda x: country_options[x]['name'],
        max_selections=2,
        help="분석할 국가를 선택하세요. '전체 국가'를 선택하면 모든 국가의 리뷰를 수집합니다."
    )
    
    if store_choice == "App Store":
        max_pages = st.slider("최대 페이지 수", min_value=1, max_value=20, value=10,
                              help="각 페이지당 최대 50개의 리뷰를 가져옵니다")
        gp_count = 200  # 미사용
    else:
        gp_count = st.slider("최대 리뷰 수", min_value=50, max_value=5000, value=200, step=50,
                             help="국가당 수집할 최대 리뷰 수 (많을수록 수집 시간이 길어집니다)")
        max_pages = 10  # 미사용
    
    st.markdown("### 📅 기간 설정")
    current_year = datetime.now().year
    
    col_year1, col_year2 = st.columns(2)
    with col_year1:
        start_year = st.number_input(
            "시작 년도", 
            min_value=2008, 
            max_value=current_year, 
            value=current_year-1,
            help="이 년도부터의 리뷰를 가져옵니다."
        )
    with col_year2:
        end_year = st.number_input(
            "종료 년도", 
            min_value=2008, 
            max_value=current_year, 
            value=current_year,
            help="이 년도까지의 리뷰를 가져옵니다."
        )
        
    st.markdown("---")
    
    analyze_button = st.button("🚀 분석 시작", type="primary", use_container_width=True)
    
    # 약관 및 개인정보처리방침 링크 (사이드바 하단)
    st.markdown("---")
    st.markdown("### 📄 약관 및 정책")
    st.markdown("""
    - [개인정보처리방침](/1_privacy_policy)
    - [서비스 이용약관](/2_terms_of_service)
    """)

# Session state 초기화
if 'reviews_data' not in st.session_state:
    st.session_state.reviews_data = None
if 'app_info' not in st.session_state:
    st.session_state.app_info = None
if 'app_id' not in st.session_state:
    st.session_state.app_id = None

# 메인 영역
if analyze_button:
    is_play_store = (store_choice == "Play Store")

    # 입력값 검증
    if not app_id_input:
        st.error("앱 ID 또는 패키지명을 입력해주세요.")
    elif not is_play_store and not app_id_input.isdigit():
        st.error("App Store ID는 숫자여야 합니다. (예: 1510564828)")
    else:
        st.session_state.app_id = app_id_input
        st.session_state.app_info = None

        if not is_play_store:
            app_id_int = int(app_id_input)
            with st.spinner("앱 정보를 불러오는 중..."):
                app_info = get_app_info(app_id_int)
                st.session_state.app_info = app_info
            if app_info:
                st.success(f"✅ 앱 정보를 찾았습니다: **{app_info.get('trackName', 'Unknown')}**")
                if 'artworkUrl100' in app_info:
                    col1, col2 = st.columns([1, 3])
                    with col1:
                        st.image(app_info['artworkUrl100'], width=100)
                    with col2:
                        st.write(f"**개발자:** {app_info.get('artistName', 'N/A')}")
                        st.write(f"**카테고리:** {app_info.get('primaryGenreName', 'N/A')}")
                        st.write(f"**평균 평점:** {app_info.get('averageUserRating', 'N/A')} ⭐")
            else:
                st.warning("⚠️ 앱 정보를 찾을 수 없지만, 리뷰 수집을 계속 진행합니다.")
        else:
            st.info(f"🤖 Play Store 앱: `{app_id_input}`")

        st.markdown("---")

        # 국가 선택 확인
        if not selected_countries:
            st.error("⚠️ 분석할 국가를 최소 1개 이상 선택해주세요.")
        else:
            # DB: 분석 시작 이벤트
            try:
                from tracker import log_event
                log_event(
                    email=(st.session_state.user_info or {}).get('email', ''),
                    action_type='start_analysis',
                    app_id=app_id_input,
                    selected_countries=selected_countries,
                )
            except Exception:
                pass

            # 리뷰 수집
            all_reviews = []
            country_dataframes = {}

            if 'ALL' in selected_countries:
                countries_to_fetch = [key for key in country_options.keys() if key != 'ALL']
            else:
                countries_to_fetch = selected_countries

            progress_bar = st.progress(0)
            status_text = st.empty()

            total_countries = len(countries_to_fetch)
            for idx, country_key in enumerate(countries_to_fetch):
                country_info = country_options[country_key]
                country_code = country_info['code']
                country_name = country_info['name']

                status_text.text(f"{country_name} 리뷰 수집 중... ({start_year}년 ~ {end_year}년)")

                if is_play_store:
                    fetched = fetch_reviews_play_store(
                        app_id_input, country_code, gp_count, start_year, end_year
                    )
                else:
                    fetched = fetch_reviews_rss(
                        int(app_id_input), country_code, max_pages, start_year, end_year
                    )

                if fetched:
                    df_country = pd.DataFrame(fetched)
                    if 'date' in df_country.columns:
                        df_country['date'] = pd.to_datetime(df_country['date'], errors='coerce')
                    country_dataframes[country_key] = df_country
                    all_reviews.extend(fetched)
                    st.success(f"✅ {country_name} 리뷰 {len(fetched)}개 수집 완료")
                else:
                    st.warning(f"⚠️ {country_name} 리뷰를 찾을 수 없습니다.")
                    country_dataframes[country_key] = pd.DataFrame()

                progress_bar.progress(int((idx + 1) / total_countries * 100))
            
            status_text.empty()
            progress_bar.empty()
            
            # '전체 국가'가 선택된 경우 selected_countries를 실제 수집한 국가들로 업데이트
            if 'ALL' in selected_countries:
                selected_countries = countries_to_fetch
            
            # 세션 상태에 저장
            if all_reviews:
                st.session_state.reviews_data = {
                    'all_reviews': all_reviews,
                    'country_dataframes': country_dataframes,
                    'selected_countries': selected_countries,
                    'country_options': country_options,
                    'store': store_choice,
                }
                # DB: 분석 완료 이벤트
                try:
                    from tracker import log_event
                    log_event(
                        email=(st.session_state.user_info or {}).get('email', ''),
                        action_type='complete_analysis',
                        app_id=app_id_input,
                        selected_countries=selected_countries,
                        details={'total_reviews': len(all_reviews)},
                    )
                except Exception:
                    pass

# ── 헬퍼: 키워드 추출 (keywords.py 위임) ────────────────────────────────────
from keywords import extract_keywords as _extract_keywords


# ── 헬퍼: 이슈 카테고리 분류 ──────────────────────────────────────────────────
def _classify_issue_categories(texts):
    """키워드 매칭으로 이슈 카테고리 분류."""
    categories = {
        '로그인/계정':    ['로그인', '계정', '비밀번호', 'login', 'account', 'password', '인증', '탈퇴'],
        '결제/구독':      ['결제', '구독', '환불', '요금', '유료', 'payment', 'subscription', 'refund', '과금'],
        '성능/속도':      ['느려', '느림', '버벅', '로딩', '속도', 'slow', 'lag', 'loading', '렉', '렉걸'],
        '크래시/안정성':  ['튕겨', '튕김', '오류', '에러', '다운', 'crash', 'error', 'bug', '꺼짐', '안됨'],
        'UI/UX':          ['인터페이스', 'ui', 'ux', '디자인', '불편', '화면', '레이아웃', '버튼', '사용성'],
        '광고':           ['광고', '팝업', 'ad', 'ads', '배너'],
        '콘텐츠/기능':    ['기능', '콘텐츠', '업데이트', '추가', '삭제', 'feature', 'content', '없어진', '사라진'],
        '고객지원':       ['고객센터', '지원', '답변', 'support', 'cs', '문의', '응답'],
    }
    counts = {k: 0 for k in categories}
    for text in texts:
        if not isinstance(text, str):
            continue
        t = text.lower()
        for cat, keywords in categories.items():
            if any(kw in t for kw in keywords):
                counts[cat] += 1
    # 기타
    categorized = sum(counts.values())
    counts['기타'] = max(0, len(texts) - categorized)
    return {k: v for k, v in counts.items() if v > 0}


# 분석 결과 표시 (세션 상태에 데이터가 있으면)
if st.session_state.reviews_data is not None:
    all_reviews = st.session_state.reviews_data['all_reviews']
    country_dataframes = st.session_state.reviews_data['country_dataframes']
    selected_countries = st.session_state.reviews_data['selected_countries']
    country_options = st.session_state.reviews_data['country_options']

    if all_reviews:
        # ── 데이터 준비 ────────────────────────────────────────────────────────
        df_all = pd.DataFrame(all_reviews)
        if 'date' in df_all.columns:
            df_all['date'] = pd.to_datetime(df_all['date'], errors='coerce', utc=True).dt.tz_localize(None)
            df_all['year'] = df_all['date'].dt.year.astype('Int64')

        # 수집 메타 정보
        fetched_at = datetime.now().strftime('%Y-%m-%d %H:%M')
        total_n = len(df_all)
        _dates = df_all['date'].dropna() if 'date' in df_all.columns else pd.Series([], dtype='datetime64[ns]')
        period_str = (
            f"{_dates.min().strftime('%Y-%m-%d')} ~ {_dates.max().strftime('%Y-%m-%d')}"
            if len(_dates) > 0 else "날짜 정보 없음"
        )
        platform_str = st.session_state.reviews_data.get('store', 'App Store')
        app_name = (st.session_state.app_info or {}).get('trackName', '') or str(st.session_state.app_id)

        avg_rating = df_all['rating'].mean() if 'rating' in df_all.columns else None
        neg_ratio = (
            (df_all['rating'] <= 2).sum() / total_n * 100
            if 'rating' in df_all.columns else None
        )

        # ── 행 0: 데이터 기준 배너 ────────────────────────────────────────────
        st.markdown(f"""
        <div style="background:#fff;border:1px solid #e0e7ff;border-radius:14px;
                    padding:1rem 1.5rem;margin-bottom:1.2rem;
                    display:flex;flex-wrap:wrap;gap:1.2rem;align-items:center;">
            <div style="flex:1;min-width:160px;">
                <div style="font-size:0.7rem;color:#6b7280;text-transform:uppercase;
                            letter-spacing:.08em;font-weight:600;">분석 기준</div>
                <div style="font-size:1rem;font-weight:700;color:#1e1b4b;">
                    현재 세션 최신 {total_n:,}개 리뷰 표본</div>
                <div style="font-size:0.78rem;color:#6366f1;margin-top:2px;">
                    스토어 전체 통계가 아닌 수집 표본 기준입니다</div>
            </div>
            <div style="display:flex;gap:1.5rem;flex-wrap:wrap;">
                <div>
                    <div style="font-size:0.68rem;color:#9ca3af;font-weight:600;">플랫폼</div>
                    <div style="font-size:0.88rem;font-weight:600;color:#374151;">{platform_str}</div>
                </div>
                <div>
                    <div style="font-size:0.68rem;color:#9ca3af;font-weight:600;">앱</div>
                    <div style="font-size:0.88rem;font-weight:600;color:#374151;">{app_name}</div>
                </div>
                <div>
                    <div style="font-size:0.68rem;color:#9ca3af;font-weight:600;">수집 기간</div>
                    <div style="font-size:0.88rem;font-weight:600;color:#374151;">{period_str}</div>
                </div>
                <div>
                    <div style="font-size:0.68rem;color:#9ca3af;font-weight:600;">수집 시각</div>
                    <div style="font-size:0.88rem;font-weight:600;color:#374151;">{fetched_at}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ── 행 1: 핵심 KPI ────────────────────────────────────────────────────
        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
        kpi1.metric("수집 리뷰 수", f"{total_n:,}개")
        if avg_rating is not None:
            kpi2.metric("평균 평점", f"{avg_rating:.2f} ⭐")
        if neg_ratio is not None:
            kpi3.metric("부정 리뷰 비율", f"{neg_ratio:.1f}%",
                        delta=None,
                        help="1~2점 리뷰 비율")
        kpi4.metric("수집 국가 수", f"{df_all['country'].nunique()}개국" if 'country' in df_all.columns else "-")

        st.markdown("---")

        # ── 행 2: 리뷰 건강도 ─────────────────────────────────────────────────
        st.markdown("#### 📊 리뷰 건강도")

        health_col1, health_col2 = st.columns([1, 1])

        with health_col1:
            if 'rating' in df_all.columns:
                st.markdown("**평점 분포**")
                rating_counts = df_all['rating'].value_counts().sort_index()
                rating_df = pd.DataFrame({'평점': rating_counts.index.astype(str) + '점',
                                          '리뷰 수': rating_counts.values})
                st.bar_chart(rating_counts.rename(index=lambda x: f"{x}점"))

        with health_col2:
            st.markdown("**리뷰 건강도 진단**")
            if 'rating' in df_all.columns:
                rc = df_all['rating'].value_counts()
                low = (rc.get(1, 0) + rc.get(2, 0))
                high = (rc.get(4, 0) + rc.get(5, 0))
                mid = rc.get(3, 0)
                low_pct = low / total_n * 100
                high_pct = high / total_n * 100

                # 인사이트 카드 생성
                insights = []
                if low_pct >= 40:
                    insights.append(("🔴", "1~2점 비중이 매우 높음", f"부정 리뷰가 {low_pct:.0f}%로 즉각 대응이 필요합니다."))
                elif low_pct >= 20:
                    insights.append(("🟠", "부정 리뷰 비중 주의", f"1~2점 리뷰가 {low_pct:.0f}%입니다."))
                else:
                    insights.append(("🟢", "부정 리뷰 비중 낮음", f"1~2점 리뷰가 {low_pct:.0f}%로 양호합니다."))

                if high_pct >= 60:
                    insights.append(("🟢", "긍정 리뷰 우세", f"4~5점 리뷰가 {high_pct:.0f}%입니다."))
                elif high_pct <= 30:
                    insights.append(("🔴", "긍정 리뷰 부족", f"4~5점 리뷰가 {high_pct:.0f}%에 불과합니다."))

                # 최근 리뷰 트렌드 (날짜가 있으면)
                if 'date' in df_all.columns and len(_dates) > 0:
                    recent_cut = _dates.quantile(0.75)
                    df_recent = df_all[df_all['date'] >= recent_cut]
                    df_older = df_all[df_all['date'] < recent_cut]
                    if len(df_recent) > 5 and len(df_older) > 5:
                        r_avg = df_recent['rating'].mean()
                        o_avg = df_older['rating'].mean()
                        if r_avg < o_avg - 0.3:
                            insights.append(("🔴", "최근 리뷰가 저평점에 편중", f"최근 리뷰 평균 {r_avg:.2f}점 vs 이전 {o_avg:.2f}점"))
                        elif r_avg > o_avg + 0.3:
                            insights.append(("🟢", "최근 리뷰 개선 추세", f"최근 리뷰 평균 {r_avg:.2f}점 vs 이전 {o_avg:.2f}점"))

                for icon, title, desc in insights:
                    st.markdown(f"""
                    <div style="background:#f9fafb;border-left:4px solid #6366f1;
                                border-radius:8px;padding:0.6rem 0.9rem;margin-bottom:0.5rem;">
                        <div style="font-weight:600;color:#1e1b4b;font-size:0.88rem;">{icon} {title}</div>
                        <div style="font-size:0.78rem;color:#6b7280;margin-top:2px;">{desc}</div>
                    </div>
                    """, unsafe_allow_html=True)

        st.markdown("---")

        # ── 행 3: 핵심 VOC ────────────────────────────────────────────────────
        st.markdown("#### 💬 핵심 VOC")

        voc_col1, voc_col2, voc_col3 = st.columns(3)

        review_texts = df_all['review'].tolist() if 'review' in df_all.columns else []

        with voc_col1:
            st.markdown("**주요 불만 키워드 Top 5**")
            neg_texts = df_all[df_all['rating'] <= 2]['review'].tolist() if 'rating' in df_all.columns else review_texts
            if neg_texts:
                neg_kw = _extract_keywords(neg_texts, 5, mode='neg')
                if neg_kw:
                    for i, (word, cnt) in enumerate(neg_kw, 1):
                        st.markdown(f"""
                        <div style="display:flex;justify-content:space-between;align-items:center;
                                    padding:0.4rem 0.7rem;background:#fff5f5;border-radius:8px;
                                    margin-bottom:0.3rem;border:1px solid #fee2e2;">
                            <span style="font-weight:600;color:#dc2626;font-size:0.85rem;">#{i} {word}</span>
                            <span style="font-size:0.78rem;color:#9ca3af;">{cnt}회</span>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.info("키워드 데이터 부족")
            else:
                st.info("부정 리뷰 데이터 없음")

        with voc_col2:
            st.markdown("**주요 만족 키워드 Top 5**")
            pos_texts = df_all[df_all['rating'] >= 4]['review'].tolist() if 'rating' in df_all.columns else review_texts
            if pos_texts:
                pos_kw = _extract_keywords(pos_texts, 5, mode='pos')
                if pos_kw:
                    for i, (word, cnt) in enumerate(pos_kw, 1):
                        st.markdown(f"""
                        <div style="display:flex;justify-content:space-between;align-items:center;
                                    padding:0.4rem 0.7rem;background:#f0fdf4;border-radius:8px;
                                    margin-bottom:0.3rem;border:1px solid #bbf7d0;">
                            <span style="font-weight:600;color:#16a34a;font-size:0.85rem;">#{i} {word}</span>
                            <span style="font-size:0.78rem;color:#9ca3af;">{cnt}회</span>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.info("키워드 데이터 부족")
            else:
                st.info("긍정 리뷰 데이터 없음")

        with voc_col3:
            st.markdown("**이슈 카테고리 분포**")
            if review_texts:
                cat_counts = _classify_issue_categories(review_texts)
                if cat_counts:
                    cat_series = pd.Series(cat_counts).sort_values(ascending=False)
                    st.bar_chart(cat_series)
                else:
                    st.info("카테고리 분류 결과 없음")

        st.markdown("---")

        # ── 행 4: 비교 분석 ───────────────────────────────────────────────────
        st.markdown("#### 🌍 비교 분석")

        available_countries = [
            c for c in selected_countries
            if c in country_dataframes and len(country_dataframes[c]) > 0
        ]

        if len(available_countries) >= 2:
            cmp_cols = st.columns(len(available_countries))
            for idx, ck in enumerate(available_countries):
                ci = country_options[ck]
                dfc = country_dataframes[ck]
                with cmp_cols[idx]:
                    avg = dfc['rating'].mean() if 'rating' in dfc.columns else None
                    neg = (dfc['rating'] <= 2).sum() / len(dfc) * 100 if 'rating' in dfc.columns else None
                    st.markdown(f"""
                    <div style="background:#fff;border:1px solid #e0e7ff;border-radius:12px;
                                padding:1rem;text-align:center;">
                        <div style="font-size:1.3rem;">{ci['emoji']}</div>
                        <div style="font-weight:700;color:#1e1b4b;">{ci['name']}</div>
                        <div style="font-size:0.82rem;color:#6b7280;margin-top:0.3rem;">
                            리뷰 {len(dfc):,}개
                        </div>
                        <div style="font-size:1.1rem;font-weight:700;color:#6366f1;margin-top:0.3rem;">
                            {'⭐ ' + f'{avg:.2f}' if avg else '-'}
                        </div>
                        <div style="font-size:0.78rem;color:#dc2626;">
                            부정 {f'{neg:.1f}%' if neg is not None else '-'}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

            # 국가별 평점 분포 비교 (grouped bar)
            st.markdown("**국가별 평점 분포 비교**")
            import altair as alt
            rows = []
            for ck in available_countries:
                if 'rating' not in country_dataframes[ck].columns:
                    continue
                counts = country_dataframes[ck]['rating'].value_counts()
                for rating in [1, 2, 3, 4, 5]:
                    rows.append({
                        '평점': f'{rating}점',
                        '국가': country_options[ck]['name'],
                        '리뷰 수': int(counts.get(rating, 0)),
                    })
            dist_df = pd.DataFrame(rows)
            grouped_chart = alt.Chart(dist_df).mark_bar().encode(
                x=alt.X('평점:N', sort=['1점','2점','3점','4점','5점'], axis=alt.Axis(labelAngle=0)),
                y=alt.Y('리뷰 수:Q'),
                color=alt.Color('국가:N'),
                xOffset=alt.XOffset('국가:N'),
                tooltip=['평점', '국가', '리뷰 수'],
            ).properties(height=300)
            st.altair_chart(grouped_chart, use_container_width=True)

        elif len(available_countries) == 1:
            st.info("국가를 2개 이상 선택하면 국가별 비교를 볼 수 있습니다.")
        else:
            st.info("국가 정보가 부족하여 국가별 비교는 제한됩니다.")

        st.markdown("---")

        # ── 리뷰 데이터 테이블 ─────────────────────────────────────────────────
        st.markdown("#### 📋 리뷰 원본 데이터")

        filter_col1, filter_col2 = st.columns(2)
        df_filtered = df_all.copy()

        with filter_col1:
            if 'rating' in df_all.columns:
                sel_ratings = st.multiselect(
                    "평점 필터",
                    options=sorted(df_all['rating'].unique()),
                    default=sorted(df_all['rating'].unique()),
                )
                df_filtered = df_filtered[df_filtered['rating'].isin(sel_ratings)]

        with filter_col2:
            if 'country' in df_all.columns and df_all['country'].nunique() > 1:
                sel_ctry = st.multiselect(
                    "국가 필터",
                    options=sorted(df_all['country'].unique()),
                    default=sorted(df_all['country'].unique()),
                )
                df_filtered = df_filtered[df_filtered['country'].isin(sel_ctry)]

        display_columns = ['country', 'rating', 'title', 'review', 'date']
        available_columns = [c for c in display_columns if c in df_filtered.columns]
        st.dataframe(df_filtered[available_columns], use_container_width=True, height=400)

        st.markdown("---")

        # ── 다운로드 ───────────────────────────────────────────────────────────
        st.markdown("#### 💾 내보내기")

        def _remove_tz(df):
            df_copy = df.copy()
            if 'date' in df_copy.columns:
                try:
                    df_copy['date'] = df_copy['date'].dt.tz_convert(None)
                except (TypeError, AttributeError):
                    pass
            return df_copy

        dl_col1, dl_col2 = st.columns(2)

        with dl_col1:
            # LLM 최적화 CSV: 불필요한 컬럼 제거, 텍스트 정제
            llm_cols = [c for c in ['date', 'country', 'rating', 'review', 'author'] if c in df_all.columns]
            df_llm = _remove_tz(df_all[llm_cols].copy())
            df_llm['review'] = df_llm['review'].astype(str).str.replace('\n', ' ').str.strip()
            csv_llm = df_llm.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label="📄 CSV 다운로드 (LLM 분석용)",
                data=csv_llm,
                file_name=f"reviews_{st.session_state.app_id}_llm.csv",
                mime="text/csv",
                help="GPT/Gemini에 바로 업로드할 수 있도록 최적화된 CSV입니다.",
                use_container_width=True,
            )
            st.caption("💡 다운로드 후 ChatGPT / Gemini에 업로드하여 심층 분석하세요.")

        with dl_col2:
            # Excel (국가별 시트)
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                for ck in selected_countries:
                    if ck in country_dataframes and len(country_dataframes[ck]) > 0:
                        _remove_tz(country_dataframes[ck]).to_excel(
                            writer, sheet_name=f"{ck}_Reviews", index=False)
                _remove_tz(df_all).to_excel(writer, sheet_name='All_Reviews', index=False)
            st.download_button(
                label="📊 Excel 다운로드 (국가별 시트)",
                data=output.getvalue(),
                file_name=f"reviews_{st.session_state.app_id}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )

        # AI 분석 링크
        st.markdown("""
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:0.8rem;margin-top:0.8rem;">
            <a href="https://chat.openai.com" target="_blank" style="text-decoration:none;">
                <div style="background:#fff;border:1px solid #e0e7ff;border-radius:12px;
                            padding:1rem 1.2rem;display:flex;align-items:center;gap:0.8rem;">
                    <div style="font-size:1.5rem;">🤖</div>
                    <div>
                        <div style="font-weight:600;color:#1e1b4b;font-size:0.9rem;">ChatGPT로 분석</div>
                        <div style="font-size:0.75rem;color:#6b7280;">CSV 업로드 후 분석</div>
                    </div>
                </div>
            </a>
            <a href="https://gemini.google.com" target="_blank" style="text-decoration:none;">
                <div style="background:#fff;border:1px solid #e0e7ff;border-radius:12px;
                            padding:1rem 1.2rem;display:flex;align-items:center;gap:0.8rem;">
                    <div style="font-size:1.5rem;">✨</div>
                    <div>
                        <div style="font-weight:600;color:#1e1b4b;font-size:0.9rem;">Gemini로 분석</div>
                        <div style="font-size:0.75rem;color:#6b7280;">CSV 업로드 후 분석</div>
                    </div>
                </div>
            </a>
        </div>
        """, unsafe_allow_html=True)

    else:
        st.error("❌ 수집된 리뷰가 없습니다. 앱 ID를 확인하거나 나중에 다시 시도해주세요.")
elif st.session_state.reviews_data is None:
    # 초기 화면
    st.markdown("""
    <div style="
        background:#fff; border-radius:14px; padding:1.5rem 2rem;
        border:1px solid #e0e7ff; box-shadow:0 2px 8px rgba(99,102,241,0.06);
        margin-bottom:1.2rem;
    ">
        <div style="font-size:1rem; font-weight:600; color:#4338ca; margin-bottom:1rem;">🚀 시작하는 방법</div>
        <div style="display:grid; grid-template-columns:1fr 1fr; gap:1rem;">
            <div style="display:flex; gap:0.8rem; align-items:flex-start;">
                <div style="background:#eef2ff; color:#6366f1; border-radius:8px; width:28px; height:28px; display:flex; align-items:center; justify-content:center; font-weight:700; flex-shrink:0;">1</div>
                <div>
                    <div style="font-weight:600; color:#1e1b4b; margin-bottom:0.2rem;">앱 ID 입력</div>
                    <div style="font-size:0.82rem; color:#1e1b4b;">앱스토어 URL에서 ID를 복사하세요<br><span style="color:#6366f1;">apps.apple.com/app/id<b>1510564828</b></span></div>
                </div>
            </div>
            <div style="display:flex; gap:0.8rem; align-items:flex-start;">
                <div style="background:#eef2ff; color:#6366f1; border-radius:8px; width:28px; height:28px; display:flex; align-items:center; justify-content:center; font-weight:700; flex-shrink:0;">2</div>
                <div>
                    <div style="font-weight:600; color:#1e1b4b; margin-bottom:0.2rem;">국가 및 기간 선택</div>
                    <div style="font-size:0.82rem; color:#1e1b4b;">최대 2개 국가 비교 분석, 페이지당 최대 50개 리뷰 수집</div>
                </div>
            </div>
            <div style="display:flex; gap:0.8rem; align-items:flex-start;">
                <div style="background:#eef2ff; color:#6366f1; border-radius:8px; width:28px; height:28px; display:flex; align-items:center; justify-content:center; font-weight:700; flex-shrink:0;">3</div>
                <div>
                    <div style="font-weight:600; color:#1e1b4b; margin-bottom:0.2rem;">분석 시작</div>
                    <div style="font-size:0.82rem; color:#1e1b4b;">왼쪽 사이드바 하단의 <b>분석 시작</b> 버튼을 클릭하세요</div>
                </div>
            </div>
            <div style="display:flex; gap:0.8rem; align-items:flex-start;">
                <div style="background:#eef2ff; color:#6366f1; border-radius:8px; width:28px; height:28px; display:flex; align-items:center; justify-content:center; font-weight:700; flex-shrink:0;">4</div>
                <div>
                    <div style="font-weight:600; color:#1e1b4b; margin-bottom:0.2rem;">결과 다운로드</div>
                    <div style="font-size:0.82rem; color:#1e1b4b;">Excel · CSV · JSON 형식으로 내보내거나 AI로 분석하세요</div>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("""
<div style="
    margin-top: 2rem;
    padding: 1rem 1.5rem;
    background: #fff;
    border-radius: 12px;
    border: 1px solid #e0e7ff;
    display: flex;
    justify-content: space-between;
    ?dev=1231
    align-items: center;
">
    <div style="display:flex; gap:1.2rem; align-items:center;">
        <a href='/1_privacy_policy' style="font-size:0.8rem; color:#6366f1; text-decoration:none; font-weight:500;">개인정보처리방침</a>
        <a href='/2_terms_of_service' style="font-size:0.8rem; color:#6366f1; text-decoration:none; font-weight:500;">서비스 이용약관</a>
    </div>
    <div style="font-size:0.78rem; color:#9ca3af;">
        Developer: Chang Dong Wook &nbsp;·&nbsp;
        <a href='mailto:okdongzang@gmail.com' style="color:#9ca3af;">okdongzang@gmail.com</a>
    </div>
</div>
""", unsafe_allow_html=True)

