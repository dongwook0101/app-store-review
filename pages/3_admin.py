"""
Admin Dashboard — only accessible to emails listed in ADMIN_EMAILS secret/env.
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, timezone

# ── Access control ─────────────────────────────────────────────────────────────

def _require_admin():
    """Stop rendering and show an error unless the current user is an admin."""
    # session_state에 인증 정보가 없으면 쿠키로 복원 시도
    if not st.session_state.get('authenticated') or not st.session_state.get('user_info'):
        st.error("로그인이 필요합니다. 메인 페이지에서 먼저 로그인하세요.")
        st.page_link("app.py", label="← 메인으로 돌아가기")
        st.stop()

    email = (st.session_state.user_info or {}).get('email', '')

    # ADMIN_EMAILS secrets에서 직접 확인 (tracker import 실패 대비)
    try:
        import os
        raw = st.secrets.get("ADMIN_EMAILS", "") or os.getenv("ADMIN_EMAILS", "")
        admins = {e.strip().lower() for e in raw.split(",") if e.strip()}
        if email.strip().lower() not in admins:
            st.error(f"접근 권한이 없습니다. ({email})")
            st.stop()
    except Exception as e:
        st.error(f"어드민 설정 오류: {e}")
        st.stop()

_require_admin()

# ── DB helpers ─────────────────────────────────────────────────────────────────

def _query(sql: str, params: dict = None) -> pd.DataFrame:
    """Run a read-only query and return a DataFrame. Returns empty DF on error."""
    try:
        from db import get_engine
        from sqlalchemy import text
        engine = get_engine()
        if engine is None:
            return pd.DataFrame()
        with engine.connect() as conn:
            result = conn.execute(text(sql), params or {})
            rows = result.fetchall()
            cols = list(result.keys())
        return pd.DataFrame(rows, columns=cols)
    except Exception as e:
        st.warning(f"DB 조회 오류: {e}")
        return pd.DataFrame()

# ── Sidebar filters ────────────────────────────────────────────────────────────

st.sidebar.header("필터")
days_back = st.sidebar.selectbox("조회 기간", [7, 14, 30, 90], index=0, format_func=lambda d: f"최근 {d}일")
since = datetime.now(timezone.utc) - timedelta(days=days_back)
since_str = since.strftime("%Y-%m-%d %H:%M:%S+00")

# ── Page header ────────────────────────────────────────────────────────────────

st.markdown("""
<div style="background:linear-gradient(135deg,#1e1b4b,#4338ca);border-radius:14px;
            padding:1.2rem 2rem;margin-bottom:1.5rem;">
  <div style="color:rgba(255,255,255,.7);font-size:.75rem;font-weight:600;
              letter-spacing:.1em;text-transform:uppercase;">Admin</div>
  <div style="color:#fff;font-size:1.4rem;font-weight:700;">🛡️ 대시보드</div>
</div>
""", unsafe_allow_html=True)

# ── Top metrics ────────────────────────────────────────────────────────────────

col1, col2, col3, col4, col5 = st.columns(5)

total_users       = _query("SELECT COUNT(*) AS n FROM users")
users_today       = _query("SELECT COUNT(*) AS n FROM users WHERE last_login_at >= NOW() - INTERVAL '1 day'")
users_7d          = _query("SELECT COUNT(*) AS n FROM users WHERE last_login_at >= NOW() - INTERVAL '7 days'")
total_analyses    = _query("SELECT COUNT(*) AS n FROM analysis_events WHERE action_type = 'complete_analysis'")
total_starts      = _query("SELECT COUNT(*) AS n FROM analysis_events WHERE action_type = 'start_analysis'")

def _n(df): return int(df['n'].iloc[0]) if not df.empty else 0

col1.metric("전체 사용자",         _n(total_users))
col2.metric("오늘 로그인",         _n(users_today))
col3.metric("최근 7일 활성 사용자", _n(users_7d))
col4.metric("완료된 분석",         _n(total_analyses))
col5.metric("시작된 분석",         _n(total_starts))

st.markdown("---")

# ── Charts ─────────────────────────────────────────────────────────────────────

chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    st.markdown("**일별 로그인 수**")
    daily_logins = _query("""
        SELECT DATE(login_at AT TIME ZONE 'UTC') AS day, COUNT(*) AS logins
        FROM user_sessions
        WHERE login_at >= :since
        GROUP BY day ORDER BY day
    """, {"since": since_str})
    if not daily_logins.empty:
        daily_logins = daily_logins.set_index('day')
        st.bar_chart(daily_logins['logins'])
    else:
        st.info("데이터 없음")

with chart_col2:
    st.markdown("**일별 분석 완료 수**")
    daily_analyses = _query("""
        SELECT DATE(created_at AT TIME ZONE 'UTC') AS day, COUNT(*) AS analyses
        FROM analysis_events
        WHERE action_type = 'complete_analysis' AND created_at >= :since
        GROUP BY day ORDER BY day
    """, {"since": since_str})
    if not daily_analyses.empty:
        daily_analyses = daily_analyses.set_index('day')
        st.bar_chart(daily_analyses['analyses'])
    else:
        st.info("데이터 없음")

st.markdown("**국가별 분석 횟수**")
country_breakdown = _query("""
    SELECT selected_countries AS country, COUNT(*) AS count
    FROM analysis_events
    WHERE action_type = 'complete_analysis'
      AND selected_countries IS NOT NULL
      AND created_at >= :since
    GROUP BY selected_countries
    ORDER BY count DESC
    LIMIT 20
""", {"since": since_str})
if not country_breakdown.empty:
    st.bar_chart(country_breakdown.set_index('country')['count'])
else:
    st.info("데이터 없음")

st.markdown("---")

# ── Tables ─────────────────────────────────────────────────────────────────────

tab1, tab2, tab3, tab4 = st.tabs(["최근 사용자", "최근 로그인", "최근 분석 이벤트", "Top 사용자"])

with tab1:
    recent_users = _query("""
        SELECT email, name, role, login_count,
               last_login_at AT TIME ZONE 'UTC' AS last_login,
               created_at    AT TIME ZONE 'UTC' AS joined
        FROM users
        ORDER BY last_login_at DESC NULLS LAST
        LIMIT 50
    """)
    if not recent_users.empty:
        st.dataframe(recent_users, use_container_width=True)
    else:
        st.info("데이터 없음")

with tab2:
    recent_sessions = _query("""
        SELECT email,
               login_at  AT TIME ZONE 'UTC' AS login_at,
               logout_at AT TIME ZONE 'UTC' AS logout_at
        FROM user_sessions
        WHERE login_at >= :since
        ORDER BY login_at DESC
        LIMIT 100
    """, {"since": since_str})
    if not recent_sessions.empty:
        st.dataframe(recent_sessions, use_container_width=True)
    else:
        st.info("데이터 없음")

with tab3:
    recent_events = _query("""
        SELECT email, action_type, app_id, selected_countries, status,
               created_at AT TIME ZONE 'UTC' AS created_at
        FROM analysis_events
        WHERE created_at >= :since
        ORDER BY created_at DESC
        LIMIT 100
    """, {"since": since_str})
    if not recent_events.empty:
        st.dataframe(recent_events, use_container_width=True)
    else:
        st.info("데이터 없음")

with tab4:
    top_users = _query("""
        SELECT email, COUNT(*) AS total_analyses
        FROM analysis_events
        WHERE action_type = 'complete_analysis'
          AND created_at >= :since
        GROUP BY email
        ORDER BY total_analyses DESC
        LIMIT 20
    """, {"since": since_str})
    if not top_users.empty:
        st.dataframe(top_users, use_container_width=True)
    else:
        st.info("데이터 없음")
