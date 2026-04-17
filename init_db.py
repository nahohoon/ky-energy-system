"""
더미데이터 포함 DB 초기화 스크립트
실행: python init_db.py
"""
from app import create_app
from models import db, Company, Equipment, OperationLog, EnergyAnalysis, \
                   SavingSimulation, MaintenanceLog, Part, InventoryLog
from datetime import date, timedelta
import random

app = create_app()

with app.app_context():
    db.drop_all()
    db.create_all()

    # ── 1. 회사 ──────────────────────────────────────────
    company = Company(
        name='케이와이산업(주)',
        bizno='123-45-67890',
        address='대구광역시 달서구 성서공단로 123',
        contact='053-000-0000'
    )
    db.session.add(company)
    db.session.flush()

    # ── 2. 설비 ──────────────────────────────────────────
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

    # ── 3. 운전데이터 (최근 30일) ──────────────────────────
    today = date.today()
    base_power = {0: 37.3, 1: 22.4, 2: 37.0, 3: 15.0, 4: 2.5}
    for eq_idx, eq in enumerate(equipments[:4]):   # 에어드라이어 제외
        for i in range(30):
            d = today - timedelta(days=30 - i)
            run_h  = round(random.uniform(16, 23), 1)
            load   = round(random.uniform(55, 85), 1)
            kwh    = round(base_power[eq_idx] * run_h * (load / 100) * random.uniform(0.93, 1.07), 1)
            log = OperationLog(
                equipment_id=eq.id,
                log_date=d,
                run_hours=run_h,
                power_kwh=kwh,
                load_rate=load,
                pressure=round(random.uniform(6.8, 7.5), 2),
                frequency=round(random.uniform(48, 60), 1),
            )
            db.session.add(log)

    # ── 4. 에너지 분석 (최근 6개월) ──────────────────────
    grades = ['A', 'A', 'B', 'B', 'C']
    for eq_idx, eq in enumerate(equipments[:4]):
        for m in range(6):
            ym = (today.replace(day=1) - timedelta(days=30 * m)).strftime('%Y-%m')
            total = round(base_power[eq_idx] * 20 * 0.7 * 30 * random.uniform(0.9, 1.1), 1)
            unit  = round(total / (base_power[eq_idx] * 24 * 30), 4)
            grade = grades[eq_idx]
            saving_rate = 0.08 if grade == 'B' else 0.15 if grade == 'C' else 0.03
            saving_kwh  = round(total * saving_rate, 1)
            ea = EnergyAnalysis(
                equipment_id=eq.id,
                analysis_month=ym,
                total_kwh=total,
                unit_kwh=unit,
                efficiency_grade=grade,
                saving_possible=saving_kwh,
                saving_amount=round(saving_kwh * 130, 0),
            )
            db.session.add(ea)

    # ── 5. 절감 시뮬레이션 ────────────────────────────────
    sims = [
        SavingSimulation(
            title='인버터 교체 시나리오 (50HP #1)',
            equipment_id=equipments[0].id,
            before_kwh=12500, after_kwh=9800, unit_price=130,
            saving_kwh=2700,  saving_amount=351000, co2_saving=1.24,
            memo='정속운전 → 인버터 제어 전환 시 부하율 68% 기준 예상 절감'
        ),
        SavingSimulation(
            title='운전 스케줄 최적화 (30HP #2)',
            equipment_id=equipments[1].id,
            before_kwh=8200, after_kwh=6900, unit_price=130,
            saving_kwh=1300, saving_amount=169000, co2_saving=0.60,
            memo='야간·주말 자동 정지 스케줄 적용 시 예상 절감'
        ),
        SavingSimulation(
            title='에어 누설 점검 + 배관 개선',
            equipment_id=None,
            before_kwh=22000, after_kwh=18500, unit_price=130,
            saving_kwh=3500, saving_amount=455000, co2_saving=1.61,
            memo='전체 설비 에어 누설률 15% → 3% 개선 시나리오'
        ),
    ]
    for s in sims:
        db.session.add(s)

    # ── 6. 유지보수 이력 ──────────────────────────────────
    maint_data = [
        (equipments[0].id, today - timedelta(days=45), '필터 교체',   '흡입 필터 교체', 35000, '김기사', today + timedelta(days=45)),
        (equipments[0].id, today - timedelta(days=90), '오일 교체',   '콤프레샤 오일 전량 교체', 58000, '이기사', today + timedelta(days=90)),
        (equipments[1].id, today - timedelta(days=30), '필터 교체',   '오일 필터 교체', 28000, '김기사', today + timedelta(days=60)),
        (equipments[2].id, today - timedelta(days=10), '점검',         '전반 점검 및 벨트 장력 조정', 0, '이기사', today + timedelta(days=80)),
        (equipments[2].id, today - timedelta(days=60), '수리',         '냉각팬 모터 교체', 120000, '외주업체', today + timedelta(days=120)),
        (equipments[3].id, today - timedelta(days=20), '오일 교체',   '피스톤 오일 교체', 22000, '김기사', today + timedelta(days=100)),
    ]
    for (eid, md, mt, desc, cost, worker, nd) in maint_data:
        db.session.add(MaintenanceLog(
            equipment_id=eid, maint_date=md, maint_type=mt,
            description=desc, cost=cost, worker=worker, next_date=nd
        ))

    # ── 7. 부품 ──────────────────────────────────────────
    parts_data = [
        ('흡입 필터 (50HP용)', 'FL-50-001', 'EA', 4, 2, 35000, '부품창고 A-1'),
        ('흡입 필터 (30HP용)', 'FL-30-001', 'EA', 3, 2, 28000, '부품창고 A-1'),
        ('오일 필터',           'FL-OIL-01', 'EA', 5, 2, 22000, '부품창고 A-2'),
        ('콤프레샤 오일 (20L)', 'OIL-20-A',  'CAN',6, 3, 58000, '부품창고 A-2'),
        ('V-벨트 A형',          'BLT-A-38',  'EA', 8, 4, 12000, '부품창고 B-1'),
        ('에어 필터 엘리먼트',  'FL-AIR-01', 'EA', 2, 2, 45000, '부품창고 A-3'),
        ('드레인 밸브',         'VLV-DRN-1', 'EA', 3, 2, 18000, '부품창고 B-2'),
        ('압력 게이지 (7kgf)',  'GAU-7K-01', 'EA', 2, 1, 32000, '부품창고 B-2'),
    ]
    parts = []
    for (name, pno, unit, qty, safe, price, loc) in parts_data:
        p = Part(name=name, part_no=pno, unit=unit, stock_qty=qty,
                 safe_qty=safe, unit_price=price, location=loc)
        db.session.add(p)
        parts.append(p)
    db.session.flush()

    # ── 8. 입출고 이력 ────────────────────────────────────
    inv_entries = [
        (parts[0].id, today - timedelta(days=60), '입고', 5, '정기 발주', '홍길동'),
        (parts[0].id, today - timedelta(days=45), '출고', 1, '설비 #1 필터 교체', '김기사'),
        (parts[1].id, today - timedelta(days=40), '입고', 4, '정기 발주', '홍길동'),
        (parts[1].id, today - timedelta(days=30), '출고', 1, '설비 #2 필터 교체', '김기사'),
        (parts[3].id, today - timedelta(days=95), '입고', 8, '정기 발주', '홍길동'),
        (parts[3].id, today - timedelta(days=90), '출고', 2, '설비 #1 오일 교체', '이기사'),
        (parts[4].id, today - timedelta(days=50), '입고', 10, '정기 발주', '홍길동'),
        (parts[4].id, today - timedelta(days=10), '출고', 2, '설비 #3 벨트 교체', '이기사'),
    ]
    for (pid, ld, io, qty, reason, worker) in inv_entries:
        db.session.add(InventoryLog(part_id=pid, log_date=ld,
                                    in_out=io, qty=qty, reason=reason, worker=worker))

    db.session.commit()
    print("✅ DB 초기화 및 더미데이터 삽입 완료!")
