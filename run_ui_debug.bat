@echo off
chcp 65001
cd /d "%~dp0"
echo ========================================
echo Streamlit 웹 UI 시작 (디버그 모드)
echo ========================================
echo.
echo 현재 디렉토리: %CD%
echo.
echo Python 경로 확인:
python --version
echo.
echo Streamlit 설치 확인:
python -c "import streamlit; print('Streamlit 설치됨:', streamlit.__version__)"
echo.
echo 파일 존재 확인:
if exist app.py (
    echo app.py 파일 발견!
) else (
    echo 오류: app.py 파일을 찾을 수 없습니다!
    pause
    exit /b 1
)
echo.
echo Streamlit 실행 중...
echo.
streamlit run app.py
echo.
echo Streamlit이 종료되었습니다.
pause






