@echo off
chcp 65001 > nul
echo ============================================================
echo  스마트 에너지 운영관리 시스템 - EXE 빌드 스크립트
echo ============================================================
echo.

:: Python 설치 확인
python --version > nul 2>&1
if errorlevel 1 (
    echo [오류] Python이 설치되어 있지 않습니다.
    echo  - https://www.python.org/downloads/ 에서 Python 3.10 이상을 설치해주세요.
    pause
    exit /b 1
)

echo [1/4] 필수 패키지 설치 중...
pip install flask flask-sqlalchemy pyinstaller --quiet
if errorlevel 1 (
    echo [오류] 패키지 설치 실패. 인터넷 연결을 확인해주세요.
    pause
    exit /b 1
)

echo [2/4] _src 폴더로 이동...
cd _src
if errorlevel 1 (
    echo [오류] _src 폴더를 찾을 수 없습니다.
    pause
    exit /b 1
)

echo [3/4] PyInstaller 빌드 실행 중... (약 2~5분 소요)
pyinstaller ky_energy.spec --distpath ..\dist --workpath ..\build --noconfirm
if errorlevel 1 (
    echo [오류] 빌드 실패. 오류 메시지를 확인해주세요.
    cd ..
    pause
    exit /b 1
)

cd ..

echo [4/4] 빌드 완료!
echo.
echo ============================================================
echo  완료: dist\스마트에너지시스템\ 폴더를 확인하세요.
echo  실행: dist\스마트에너지시스템\스마트에너지시스템.exe 더블클릭
echo ============================================================
echo.
pause
