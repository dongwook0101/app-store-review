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
from auth import check_authentication, handle_oauth_callback, show_login_page

# 페이지 설정
st.set_page_config(
    page_title="앱스토어 리뷰 분석",
    page_icon="📱",
    layout="wide"
)

# 인증 체크 및 OAuth 콜백 처리
# OAuth 콜백 처리 (세션 상태 업데이트)
handle_oauth_callback()

# 인증 상태 확인 (콜백 처리 후)
is_authenticated = check_authentication()

# 디버깅: query params에 code가 남아있고 이미 인증된 경우 제거
if is_authenticated and ('code' in st.query_params or 'state' in st.query_params):
    try:
        new_params = {}
        for key, value in st.query_params.items():
            if key not in ['code', 'state']:
                new_params[key] = value
        st.query_params = new_params
        st.rerun()
    except:
        pass

# 인증되지 않은 경우 로그인 페이지 표시
if not is_authenticated:
    show_login_page()
    st.stop()

def fetch_reviews_rss(app_id, country='us', max_pages=10):
    """
    iTunes RSS API를 사용하여 리뷰 데이터를 수집합니다.
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
st.title("📱 앱스토어 리뷰 분석 도구")
st.markdown("---")

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
        st.markdown(f"**👤 로그인:** {st.session_state.user_info.get('email', 'Unknown')}")
        if st.button("🚪 로그아웃", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.user_info = None
            st.session_state.credentials = None
            st.rerun()
        st.markdown("---")
    
    st.header("⚙️ 설정")
    
    app_id_input = st.text_input(
        "앱 ID",
        value="1510564828",
        help="앱스토어에서 앱의 ID를 입력하세요. (예: 1510564828)"
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
    
    max_pages = st.slider("최대 페이지 수", min_value=1, max_value=20, value=10, 
                          help="각 페이지당 최대 50개의 리뷰를 가져옵니다")
    
    st.markdown("---")
    
    analyze_button = st.button("🚀 분석 시작", type="primary", use_container_width=True)

# Session state 초기화
if 'reviews_data' not in st.session_state:
    st.session_state.reviews_data = None
if 'app_info' not in st.session_state:
    st.session_state.app_info = None
if 'app_id' not in st.session_state:
    st.session_state.app_id = None

# 메인 영역
if analyze_button:
    if not app_id_input or not app_id_input.isdigit():
        st.error("올바른 앱 ID를 입력해주세요.")
    else:
        app_id = int(app_id_input)
        st.session_state.app_id = app_id
        
        # 앱 정보 가져오기
        with st.spinner("앱 정보를 불러오는 중..."):
            app_info = get_app_info(app_id)
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
        
        st.markdown("---")
        
        # 국가 선택 확인
        if not selected_countries:
            st.error("⚠️ 분석할 국가를 최소 1개 이상 선택해주세요.")
        else:
            # 리뷰 수집
            all_reviews = []
            country_dataframes = {}  # 국가별 DataFrame 저장
            
            # '전체 국가'가 선택되었는지 확인
            if 'ALL' in selected_countries:
                # 전체 국가 선택 시 모든 국가 수집 (ALL 제외)
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
                
                status_text.text(f"{country_name} 리뷰 수집 중...")
                reviews = fetch_reviews_rss(app_id, country_code, max_pages)
                
                if reviews:
                    df_country = pd.DataFrame(reviews)
                    if 'date' in df_country.columns:
                        df_country['date'] = pd.to_datetime(df_country['date'], errors='coerce')
                    country_dataframes[country_key] = df_country
                    all_reviews.extend(reviews)
                    st.success(f"✅ {country_name} 리뷰 {len(reviews)}개 수집 완료")
                else:
                    st.warning(f"⚠️ {country_name} 리뷰를 찾을 수 없습니다.")
                    country_dataframes[country_key] = pd.DataFrame()  # 빈 DataFrame
                
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
                    'country_options': country_options
                }

# 분석 결과 표시 (세션 상태에 데이터가 있으면)
if st.session_state.reviews_data is not None:
    all_reviews = st.session_state.reviews_data['all_reviews']
    country_dataframes = st.session_state.reviews_data['country_dataframes']
    selected_countries = st.session_state.reviews_data['selected_countries']
    country_options = st.session_state.reviews_data['country_options']
    
    # 앱 정보 표시
    if st.session_state.app_info:
        app_info = st.session_state.app_info
        st.success(f"✅ 앱 정보: **{app_info.get('trackName', 'Unknown')}** (ID: {st.session_state.app_id})")
        if 'artworkUrl100' in app_info:
            col1, col2 = st.columns([1, 3])
            with col1:
                st.image(app_info['artworkUrl100'], width=100)
            with col2:
                st.write(f"**개발자:** {app_info.get('artistName', 'N/A')}")
                st.write(f"**카테고리:** {app_info.get('primaryGenreName', 'N/A')}")
                st.write(f"**평균 평점:** {app_info.get('averageUserRating', 'N/A')} ⭐")
    
    if all_reviews:
        st.markdown("---")
        st.header("📊 분석 결과")
        
        # 전체 통계
        df_all = pd.DataFrame(all_reviews)
        if 'date' in df_all.columns:
            df_all['date'] = pd.to_datetime(df_all['date'], errors='coerce')
            # 년도 컬럼 추가
            df_all['year'] = df_all['date'].dt.year
        
        # 통계 메트릭
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("총 리뷰 수", len(df_all))
            
            if 'rating' in df_all.columns:
                with col2:
                    st.metric("평균 평점", f"{df_all['rating'].mean():.2f} ⭐")
                
                with col3:
                    st.metric("최고 평점", f"{df_all['rating'].max()} ⭐")
                
                with col4:
                    st.metric("최저 평점", f"{df_all['rating'].min()} ⭐")
            
            # 평점 분포
            if 'rating' in df_all.columns:
                st.subheader("📈 평점 분포")
                rating_counts = df_all['rating'].value_counts().sort_index()
                
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.bar_chart(rating_counts)
                
                with col2:
                    st.write("**평점별 리뷰 수**")
                    for rating in sorted(rating_counts.index):
                        count = rating_counts[rating]
                        st.write(f"{'⭐' * rating} {rating}점: {count}개")
            
            # 국가별 비교
            available_countries = [c for c in selected_countries if c in country_dataframes and len(country_dataframes[c]) > 0]
            if len(available_countries) > 0:
                st.subheader("🌍 국가별 비교")
                
                cols = st.columns(len(available_countries))
                for idx, country_key in enumerate(available_countries):
                    with cols[idx]:
                        country_info = country_options[country_key]
                        df_country = country_dataframes[country_key]
                        st.write(f"**{country_info['name']}**")
                        st.write(f"- 리뷰 수: {len(df_country)}")
                        if 'rating' in df_country.columns:
                            st.write(f"- 평균 평점: {df_country['rating'].mean():.2f} ⭐")
            
            # 년도별 분석
            if 'year' in df_all.columns or 'date' in df_all.columns:
                st.subheader("📅 년도별 분석")
                
                # 년도 정보가 있으면 분석
                df_year = df_all.dropna(subset=['year'])
                
                if len(df_year) > 0:
                    # 년도별 통계
                    year_stats = df_year.groupby('year').agg({
                        'rating': ['count', 'mean'],
                    }).round(2)
                    year_stats.columns = ['리뷰 수', '평균 평점']
                    year_stats = year_stats.sort_index()
                    
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.write("**년도별 리뷰 수 및 평균 평점**")
                        st.dataframe(year_stats, use_container_width=True)
                    
                    with col2:
                        st.write("**년도별 요약**")
                        if len(year_stats) > 0:
                            st.write(f"**분석 기간:** {int(year_stats.index.min())}년 ~ {int(year_stats.index.max())}년")
                            st.write(f"**총 년도 수:** {len(year_stats)}년")
                            max_year = year_stats['리뷰 수'].idxmax()
                            st.write(f"**최다 리뷰 년도:** {int(max_year)}년 ({int(year_stats.loc[max_year, '리뷰 수'])}개)")
                    
                    # 년도별 차트
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write("**년도별 리뷰 수 추이**")
                        year_counts = year_stats['리뷰 수']
                        st.line_chart(year_counts)
                    
                    with col2:
                        st.write("**년도별 평균 평점 추이**")
                        year_ratings = year_stats['평균 평점']
                        st.line_chart(year_ratings)
                    
                    # 년도별 상세 분석 (국가별)
                    if 'country' in df_year.columns:
                        st.write("**년도별 국가별 비교**")
                        
                        year_country_stats = df_year.groupby(['year', 'country']).agg({
                            'rating': ['count', 'mean'],
                        }).round(2)
                        year_country_stats.columns = ['리뷰 수', '평균 평점']
                        year_country_stats = year_country_stats.reset_index()
                        
                        # 피벗 테이블 생성
                        pivot_counts = year_country_stats.pivot_table(
                            index='year', 
                            columns='country', 
                            values='리뷰 수', 
                            aggfunc='sum'
                        ).fillna(0)
                        pivot_ratings = year_country_stats.pivot_table(
                            index='year', 
                            columns='country', 
                            values='평균 평점', 
                            aggfunc='mean'
                        ).fillna(0)
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.write("**년도별 국가별 리뷰 수**")
                            st.line_chart(pivot_counts)
                        
                        with col2:
                            st.write("**년도별 국가별 평균 평점**")
                            st.line_chart(pivot_ratings)
                
                else:
                    st.info("년도 정보가 있는 리뷰가 없습니다.")
            
            # 데이터 테이블
            st.subheader("📋 리뷰 데이터")
            
            # 필터 옵션
            col1, col2, col3 = st.columns(3)
            
            df_filtered = df_all.copy()
            
            with col1:
                if 'rating' in df_all.columns:
                    selected_ratings = st.multiselect(
                        "평점 필터",
                        options=sorted(df_all['rating'].unique()),
                        default=sorted(df_all['rating'].unique())
                    )
                    df_filtered = df_filtered[df_filtered['rating'].isin(selected_ratings)]
            
            with col2:
                if 'country' in df_all.columns:
                    selected_countries = st.multiselect(
                        "국가 필터",
                        options=df_all['country'].unique(),
                        default=df_all['country'].unique()
                    )
                    df_filtered = df_filtered[df_filtered['country'].isin(selected_countries)]
            
            with col3:
                if 'year' in df_all.columns:
                    available_years = sorted([int(y) for y in df_all['year'].dropna().unique()])
                    if available_years:
                        selected_years = st.multiselect(
                            "년도 필터",
                            options=available_years,
                            default=available_years
                        )
                        if selected_years:
                            df_filtered = df_filtered[df_filtered['year'].isin(selected_years)]
            
            # 테이블 표시
            display_columns = ['country', 'rating', 'title', 'review', 'date']
            available_columns = [col for col in display_columns if col in df_filtered.columns]
            st.dataframe(df_filtered[available_columns], use_container_width=True, height=400)
            
            # 다운로드 버튼
            st.markdown("---")
            st.subheader("💾 데이터 다운로드")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                # Excel 다운로드
                output = io.BytesIO()
                
                def remove_timezone(df):
                    """datetime 컬럼에서 타임존 정보 제거 (Excel 호환)"""
                    df_copy = df.copy()
                    if 'date' in df_copy.columns:
                        try:
                            # 타임존이 있으면 제거 (tz_convert는 타임존이 있는 경우에만 작동)
                            df_copy['date'] = df_copy['date'].dt.tz_convert(None)
                        except (TypeError, AttributeError):
                            # 타임존 정보가 없거나 이미 naive datetime인 경우 - 그대로 사용
                            pass
                    return df_copy
                
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    # 선택된 국가별로 시트 생성
                    for country_key in selected_countries:
                        if country_key in country_dataframes and len(country_dataframes[country_key]) > 0:
                            df_country_export = remove_timezone(country_dataframes[country_key])
                            sheet_name = f"{country_key}_Reviews"
                            df_country_export.to_excel(writer, sheet_name=sheet_name, index=False)
                    
                    df_all_export = remove_timezone(df_all)
                    df_all_export.to_excel(writer, sheet_name='All_Reviews', index=False)
                
                st.download_button(
                    label="📊 Excel 파일 다운로드",
                    data=output.getvalue(),
                    file_name=f"reviews_{st.session_state.app_id}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            
            with col2:
                # CSV 다운로드
                csv = df_all.to_csv(index=False, encoding='utf-8-sig')
                st.download_button(
                    label="📄 CSV 파일 다운로드",
                    data=csv,
                    file_name=f"reviews_{st.session_state.app_id}.csv",
                    mime="text/csv"
                )
            
            with col3:
                # JSON 다운로드
                json_str = json.dumps(all_reviews, ensure_ascii=False, indent=2)
                st.download_button(
                    label="📋 JSON 파일 다운로드",
                    data=json_str,
                    file_name=f"reviews_{st.session_state.app_id}.json",
                    mime="application/json"
                )
            
            st.markdown("---")
            st.write("**🤖 AI 데이터 분석**")
            st.info("💡 CSV 파일을 다운로드한 후, 각 AI 서비스 웹사이트에서 파일을 업로드하여 분석하세요.")
            
            col_ai1, col_ai2 = st.columns(2)
            
            with col_ai1:
                st.markdown(f"""
                <a href="https://chat.openai.com" target="_blank">
                    <button style="
                        background-color: #10a37f;
                        color: white;
                        padding: 0.5rem 1rem;
                        border: none;
                        border-radius: 0.25rem;
                        cursor: pointer;
                        font-size: 1rem;
                        width: 100%;
                        text-decoration: none;
                        display: inline-block;
                    ">🔵 ChatGPT 열기</button>
                </a>
                """, unsafe_allow_html=True)
                st.caption("1. 위 버튼을 클릭하여 ChatGPT 웹사이트를 엽니다\n2. CSV 파일을 업로드하거나 붙여넣기하여 분석하세요")
            
            with col_ai2:
                st.markdown(f"""
                <a href="https://gemini.google.com" target="_blank">
                    <button style="
                        background-color: #4285f4;
                        color: white;
                        padding: 0.5rem 1rem;
                        border: none;
                        border-radius: 0.25rem;
                        cursor: pointer;
                        font-size: 1rem;
                        width: 100%;
                        text-decoration: none;
                        display: inline-block;
                    ">🟢 Gemini 열기</button>
                </a>
                """, unsafe_allow_html=True)
                st.caption("1. 위 버튼을 클릭하여 Gemini 웹사이트를 엽니다\n2. CSV 파일을 업로드하거나 붙여넣기하여 분석하세요")
        else:
            st.error("❌ 수집된 리뷰가 없습니다. 앱 ID를 확인하거나 나중에 다시 시도해주세요.")
elif st.session_state.reviews_data is None:
    # 초기 화면
    st.info("👈 왼쪽 사이드바에서 앱 ID를 입력하고 '분석 시작' 버튼을 클릭하세요.")
    
    st.markdown("---")
    st.subheader("📖 사용 방법")
    
    st.markdown("""
    1. **앱 ID 찾기**: 
       - 앱스토어에서 앱 페이지를 열고 URL에서 ID를 찾으세요
       - 예: `https://apps.apple.com/app/id1510564828` → ID는 `1510564828`
    
    2. **분석 설정**:
       - 분석할 국가를 선택하세요 (최대 2개까지 비교분석 가능)
       - 최대 페이지 수를 설정하세요 (각 페이지당 최대 50개 리뷰)
    
    3. **분석 시작**:
       - '분석 시작' 버튼을 클릭하면 리뷰를 수집하고 분석합니다
    
    4. **결과 확인 및 다운로드**:
       - 분석 결과를 확인하고 Excel, CSV, JSON 형식으로 다운로드하세요
    """)
    
    st.markdown("---")
    st.subheader("💡 예시")
    st.code("앱 ID: 1510564828 (Murmur - Voice Diary)", language="text")

# 개발자 정보 (맨 아래 오른쪽)
st.markdown("---")
st.markdown("---")
st.markdown(
    """
    <div style='text-align: right; color: #666; padding: 20px;'>
        <p style='margin-bottom: 0.5em;'><strong>Developer:</strong> Chang Dong Wook</p>
        <p><strong>Email:</strong> <a href='mailto:okdongzang@gmail.com'>okdongzang@gmail.com</a></p>
    </div>
    """,
    unsafe_allow_html=True
)

