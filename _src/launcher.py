"""
스마트 에너지 운영관리 시스템 - 실행 진입점
더블클릭만으로 실행 가능한 런처 스크립트
"""
import sys
import os
import threading
import time
import webbrowser

# ── PyInstaller 번들 환경 / 일반 환경 경로 통합 처리 ──────────────────────
if getattr(sys, 'frozen', False):
    # PyInstaller로 빌드된 실행파일(.exe) 환경
    BASE_DIR = os.path.dirname(sys.executable)
    BUNDLE_DIR = sys._MEIPASS
else:
    # 일반 개발 환경 (python launcher.py)
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    BUNDLE_DIR = BASE_DIR

# 모듈 경로 추가
sys.path.insert(0, BUNDLE_DIR)
os.chdir(BASE_DIR)

# ── 환경 변수 설정 ─────────────────────────────────────────────────────────
os.environ['KY_ENERGY_BASE_DIR'] = BASE_DIR
os.environ['KY_ENERGY_BUNDLE_DIR'] = BUNDLE_DIR

# ── Flask 앱 import ────────────────────────────────────────────────────────
from app import create_app
from models import db

PORT = 5000
URL = f'http://localhost:{PORT}'


def init_database(app):
    """최초 실행 시 DB가 없으면 자동 생성 및 더미데이터 삽입"""
    db_path = os.path.join(BASE_DIR, 'ky_energy.db')
    with app.app_context():
        if not os.path.exists(db_path):
            print('[DB] 데이터베이스를 초기화합니다...')
            db.create_all()
            _insert_dummy_data(app)
            print('[DB] 초기화 완료.')
        else:
            # DB 파일은 있으나 테이블이 비어있는 경우 대비
            try:
                from models import Equipment
                count = Equipment.query.count()
                if count == 0:
                    print('[DB] 테이블이 비어 있습니다. 더미데이터를 삽입합니다...')
                    _insert_dummy_data(app)
                    print('[DB] 더미데이터 삽입 완료.')
            except Exception:
                db.create_all()
                _insert_dummy_data(app)


def _insert_dummy_data(app):
    """더미데이터 삽입 (init_db.py 내용을 함수화)"""
    with app.app_context():
        try:
            import importlib, types
            # init_db 모듈을 직접 실행하지 않고 내부 로직만 호출
            from models import (Company, Equipment, OperationLog, EnergyAnalysis,
                                SavingSimulation, MaintenanceLog, Part, InventoryLog)
            from datetime import date, timedelta, datetime
            import random

            random.seed(42)
            today = date.today()

            # 회사
            company = Company(
                name='케이와이산업(주)',
                bizno='123-45-67890',
                address='대구광역시 달서구 성서공단로 123',
                contact='053-000-0000'
            )
            db.session.add(company)
            db.session.flush()

            # 설비
            equip_data = [
                dict(name='50HP 스크류 콤프레샤 #1', model='KOBELCO SG-50A',
                     horsepower=50, rated_power=37.3, install_loc='압축기실 A',
                     status='가동중', install_date=date(2020, 3, 15)),
                dict(name='30HP 스크류 콤프레샤 #2', model='KOBELCO SG-30A',
                     horsepower=30, rated_power=22.4, install_loc='압축기실 A',
                     status='가동중', install_date=date(2021, 6, 10)),
                dict(name='50HP 스크류 콤프레샤 #3', model='ATLAS COPCO GA37',
                     horsepower=50, rated_power=37.0, install_loc='압축기실 B',
                     status='점검중', install_date=date(2019, 9, 1)),
                dict(name='20HP 피스톤 콤프레샤 #4', model='JUCAI WH-20',
                     horsepower=20, rated_power=15.0, install_loc='생산동 2층',
                     status='가동중', install_date=date(2022, 1, 20)),
                dict(name='에어드라이어 #1', model='KAESER DC-T100',
                     horsepower=None, rated_power=2.5, install_loc='압축기실 A',
                     status='가동중', install_date=date(2020, 3, 15)),
            ]
            equipments = []
            for d in equip_data:
                eq = Equipment(company_id=company.id, **d)
                db.session.add(eq)
                equipments.append(eq)
            db.session.flush()

            # 운전 데이터 (최근 30일)
            base_params = [
                dict(run_hours=20.5, avg_pressure=7.0, avg_freq=50.0,
                     load_rate=78.0, power_kwh=538.0),
                dict(run_hours=18.0, avg_pressure=6.8, avg_freq=47.0,
                     load_rate=71.0, power_kwh=358.0),
                dict(run_hours=22.0, avg_pressure=7.2, avg_freq=52.0,
                     load_rate=85.0, power_kwh=570.0),
                dict(run_hours=14.0, avg_pressure=6.5, avg_freq=45.0,
                     load_rate=62.0, power_kwh=185.0),
                dict(run_hours=10.0, avg_pressure=6.2, avg_freq=42.0,
                     load_rate=55.0, power_kwh=22.0),
            ]
            for i, eq in enumerate(equipments):
                bp = base_params[i]
                for day_offset in range(30):
                    target_date = today - timedelta(days=29 - day_offset)
                    is_weekend = target_date.weekday() >= 5
                    factor = random.uniform(0.88, 1.08)
                    if is_weekend:
                        factor *= 0.75
                    log = OperationLog(
                        equipment_id=eq.id,
                        log_date=target_date,
                        run_hours=round(bp['run_hours'] * factor, 1),
                        avg_pressure=round(bp['avg_pressure'] + random.uniform(-0.2, 0.2), 2),
                        avg_freq=round(bp['avg_freq'] + random.uniform(-1.5, 1.5), 1),
                        load_rate=round(min(100, bp['load_rate'] * factor), 1),
                        power_kwh=round(bp['power_kwh'] * factor, 1),
                        note=''
                    )
                    db.session.add(log)

            # 에너지 분석 (최근 6개월)
            efficiency_grades = ['A', 'A', 'B', 'C', 'A']
            base_kwh = [12800, 9200, 13500, 4600, 650]
            base_saving = [1280, 1380, 2970, 920, 65]
            for i, eq in enumerate(equipments):
                for m in range(6):
                    month_offset = 5 - m
                    if today.month - month_offset <= 0:
                        y = today.year - 1
                        mo = today.month - month_offset + 12
                    else:
                        y = today.year
                        mo = today.month - month_offset
                    seasonal = 1.0 + 0.05 * (m - 2.5)
                    kwh = round(base_kwh[i] * seasonal * random.uniform(0.96, 1.04))
                    saving = round(base_saving[i] * seasonal * random.uniform(0.95, 1.05))
                    ea = EnergyAnalysis(
                        equipment_id=eq.id,
                        analysis_month=date(y, mo, 1),
                        total_kwh=kwh,
                        unit_power=round(kwh / (eq.rated_power * 22 * 8), 3),
                        efficiency_grade=efficiency_grades[i],
                        est_saving_kwh=round(saving / 100, 1),
                        est_saving_won=saving
                    )
                    db.session.add(ea)

            # 절감 시뮬레이션
            sim_data = [
                dict(title='인버터 제어 최적화 - #1', before_kwh=12800, after_kwh=10240,
                     saving_rate=20.0, monthly_saving=307200, invest_cost=2500000,
                     co2_reduction=1286, note='부하율 78% 구간 인버터 주파수 최적화'),
                dict(title='운전시간 단축 스케줄링 - #2', before_kwh=9200, after_kwh=7820,
                     saving_rate=15.0, monthly_saving=207000, invest_cost=0,
                     co2_reduction=691, note='비생산 시간대 가동 중지'),
                dict(title='노후 설비 교체 검토 - #3', before_kwh=13500, after_kwh=9450,
                     saving_rate=30.0, monthly_saving=607500, invest_cost=12000000,
                     co2_reduction=2430, note='15년 노후 설비 → 고효율 신형 교체'),
            ]
            for sd in sim_data:
                sim = SavingSimulation(equipment_id=equipments[0].id, **sd)
                db.session.add(sim)

            # 유지보수 이력
            maint_data = [
                dict(equipment_id=equipments[0].id, maint_date=today - timedelta(days=15),
                     maint_type='정기점검', description='에어필터 교체, 오일 보충',
                     technician='김철수', cost=85000, result='정상'),
                dict(equipment_id=equipments[2].id, maint_date=today - timedelta(days=5),
                     maint_type='고장수리', description='베어링 소음 발생 → 베어링 교체',
                     technician='이영희', cost=320000, result='수리완료(점검중)'),
                dict(equipment_id=equipments[1].id, maint_date=today - timedelta(days=45),
                     maint_type='정기점검', description='벨트 장력 조정, 에어필터 청소',
                     technician='박민수', cost=45000, result='정상'),
            ]
            for md in maint_data:
                ml = MaintenanceLog(**md)
                db.session.add(ml)

            # 부품
            parts_data = [
                dict(part_no='AF-001', name='에어필터 (50HP용)', spec='φ150×300',
                     unit='개', stock_qty=4, safety_qty=2, unit_price=25000,
                     supplier='필터테크', location='창고 A-1'),
                dict(part_no='OL-001', name='콤프레샤 오일 (20L)', spec='ISO VG46',
                     unit='통', stock_qty=6, safety_qty=3, unit_price=55000,
                     supplier='KY오일', location='창고 A-2'),
                dict(part_no='BL-001', name='V벨트', spec='B-52',
                     unit='개', stock_qty=3, safety_qty=2, unit_price=18000,
                     supplier='동양벨트', location='창고 B-1'),
                dict(part_no='BR-001', name='주 베어링 (6208)', spec='6208-2RS',
                     unit='개', stock_qty=2, safety_qty=2, unit_price=35000,
                     supplier='NSK코리아', location='창고 B-2'),
                dict(part_no='SP-001', name='압력센서', spec='0-16bar',
                     unit='개', stock_qty=1, safety_qty=1, unit_price=85000,
                     supplier='센서월드', location='창고 C-1'),
            ]
            parts = []
            for pd in parts_data:
                p = Part(**pd)
                db.session.add(p)
                parts.append(p)
            db.session.flush()

            # 입출고 이력
            for idx, part in enumerate(parts):
                il = InventoryLog(
                    part_id=part.id,
                    log_date=today - timedelta(days=20 + idx * 3),
                    inout_type='입고',
                    quantity=10,
                    note='정기 입고'
                )
                db.session.add(il)

            db.session.commit()
            print('[DB] 더미데이터 삽입 완료.')

        except Exception as e:
            db.session.rollback()
            print(f'[DB] 더미데이터 삽입 중 오류: {e}')


def open_browser():
    """Flask 서버 준비 후 브라우저 자동 오픈"""
    time.sleep(2.0)
    webbrowser.open(URL)
    print(f'[브라우저] {URL} 열기 완료')


def main():
    print('=' * 50)
    print('  스마트 에너지 운영관리 시스템')
    print('  Smart Energy Operation Management System')
    print('=' * 50)
    print(f'[시스템] 시작 중... ({URL})')

    app = create_app()

    # DB 자동 초기화
    init_database(app)

    # 브라우저 자동 오픈 (별도 스레드)
    browser_thread = threading.Thread(target=open_browser, daemon=True)
    browser_thread.start()

    print(f'[서버] Flask 서버 실행 중 - {URL}')
    print('[안내] 브라우저에서 시스템이 자동으로 열립니다.')
    print('[종료] 이 창을 닫으면 시스템이 종료됩니다.')
    print('-' * 50)

    # Flask 서버 실행 (use_reloader=False 필수 - PyInstaller 호환)
    app.run(
        host='127.0.0.1',
        port=PORT,
        debug=False,
        use_reloader=False,
        threaded=True
    )


if __name__ == '__main__':
    main()
