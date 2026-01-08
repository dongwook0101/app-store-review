@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ========================================
echo Streamlit 웹 UI 시작
echo ========================================
echo.
echo 현재 디렉토리: %CD%
echo.
echo Streamlit을 실행합니다...
echo.
pause
streamlit run app.py
pause
