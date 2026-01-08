@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo 작업 디렉토리: %CD%
echo.
python analyze_reviews.py
echo.
echo 완료되었습니다. 아무 키나 누르세요...
pause >nul
