import os
import sys

# PyInstaller 번들 환경 vs 일반 환경 경로 처리
if getattr(sys, 'frozen', False):
    # EXE 실행 시: 실행파일이 위치한 폴더를 BASE_DIR로 사용
    # (DB, 데이터 파일은 실행파일 옆에 위치)
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.environ.get('KY_ENERGY_BASE_DIR',
                              os.path.abspath(os.path.dirname(__file__)))

DB_PATH = os.path.join(BASE_DIR, 'ky_energy.db')


class Config:
    SECRET_KEY = 'ky-energy-secret-2026'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + DB_PATH
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DEBUG = False
