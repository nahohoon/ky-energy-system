@echo off
chcp 65001 > nul
echo ============================================================
echo  스마트 에너지 운영관리 시스템 - 직접 실행 (Python 필요)
echo ============================================================
echo.

python --version > nul 2>&1
if errorlevel 1 (
    echo [오류] Python이 설치되어 있지 않습니다.
    echo  - https://www.python.org/downloads/ 에서 설치 후 다시 실행해주세요.
    pause
    exit /b 1
)

echo [1/2] 필수 패키지 확인 및 설치 중...
pip install flask flask-sqlalchemy --quiet

echo [2/2] 시스템 실행 중...
cd _src
python launcher.py
pause
