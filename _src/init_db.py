"""
더미데이터 포함 DB 초기화 스크립트
실행: python init_db.py
"""
from app import create_app
from models import db, Company, Equipment, OperationLog, EnergyAnalysis, \
                   SavingSimulation, MaintenanceLog, Part, InventoryLog
from datetime import date, timedelta

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

    # ── 3. 운전데이터 (최근 30일, 패턴형 데이터) ──────────────────
    today = date.today()
    op_profiles = {
        0: {'base_hours': 21.0, 'base_load': 78.0, 'base_pressure': 7.1, 'base_freq': 56.0},
        1: {'base_hours': 18.5, 'base_load': 72.0, 'base_pressure': 7.0, 'base_freq': 54.0},
        2: {'base_hours': 17.0, 'base_load': 84.0, 'base_pressure': 7.3, 'base_freq': 58.0},
        3: {'base_hours': 14.0, 'base_load': 63.0, 'base_pressure': 6.9, 'base_freq': 51.0},
    }
    rated_power_map = {0: 37.3, 1: 22.4, 2: 37.0, 3: 15.0}

    for eq_idx, eq in enumerate(equipments[:4]):
        profile = op_profiles[eq_idx]
        for i in range(30):
            log_date = today - timedelta(days=29 - i)
            weekday = log_date.weekday()
            weekly_adj = -2.0 if weekday >= 5 else 0.0
            trend_adj = (i - 15) * 0.05

            run_hours = round(profile['base_hours'] + weekly_adj + trend_adj, 1)
            load_rate = round(profile['base_load'] + (1.5 if weekday in [1, 2, 3] else -1.0 if weekday >= 5 else 0.0) + trend_adj * 0.8, 1)
            pressure = round(profile['base_pressure'] + (0.08 if weekday in [1, 2] else -0.05 if weekday >= 5 else 0.0), 2)
            frequency = round(profile['base_freq'] + (0.8 if weekday in [1, 2, 3] else -0.6 if weekday >= 5 else 0.0), 1)

            power_kwh = round(rated_power_map[eq_idx] * run_hours * (load_rate / 100) * 0.96, 1)

            db.session.add(OperationLog(
                equipment_id=eq.id,
                log_date=log_date,
                run_hours=run_hours,
                power_kwh=power_kwh,
                load_rate=load_rate,
                pressure=pressure,
                frequency=frequency,
                memo='주간 운전 패턴 반영' if weekday < 5 else '주말 감속 운전'
            ))

    # ── 4. 에너지 분석 (최근 6개월, 월별 패턴) ───────────────────
    analysis_profiles = {
        0: {'grade': 'B', 'monthly_base': [15400, 15150, 14980, 14750, 14500, 14380], 'saving_rate': 0.08},
        1: {'grade': 'B', 'monthly_base': [9050, 8920, 8800, 8680, 8540, 8460], 'saving_rate': 0.07},
        2: {'grade': 'D', 'monthly_base': [16100, 15920, 15750, 15580, 15320, 15150], 'saving_rate': 0.16},
        3: {'grade': 'C', 'monthly_base': [5200, 5140, 5080, 5010, 4950, 4880], 'saving_rate': 0.12},
    }

    month_anchor = today.replace(day=1)
    for eq_idx, eq in enumerate(equipments[:4]):
        profile = analysis_profiles[eq_idx]
        for m in range(6):
            ym = (month_anchor - timedelta(days=30 * m)).strftime('%Y-%m')
            total = float(profile['monthly_base'][m])
            unit = round(total / (eq.rated_power * 24 * 30), 4) if eq.rated_power else 0
            saving_kwh = round(total * profile['saving_rate'], 1)
            db.session.add(EnergyAnalysis(
                equipment_id=eq.id,
                analysis_month=ym,
                total_kwh=total,
                unit_kwh=unit,
                efficiency_grade=profile['grade'],
                saving_possible=saving_kwh,
                saving_amount=round(saving_kwh * 130, 0),
            ))

    # ── 5. 절감 시뮬레이션 ────────────────────────────────
    sims = [
        SavingSimulation(
            title='인버터 제어 전환 시나리오 (50HP #1)',
            equipment_id=equipments[0].id,
            before_kwh=12500, after_kwh=9800, unit_price=130,
            saving_kwh=2700, saving_amount=351000, co2_saving=1.24,
            memo='정속운전 설비를 인버터 제어로 전환하여 부하변동 대응 효율을 높이는 시나리오'
        ),
        SavingSimulation(
            title='운전 스케줄 최적화 (30HP #2)',
            equipment_id=equipments[1].id,
            before_kwh=8200, after_kwh=6900, unit_price=130,
            saving_kwh=1300, saving_amount=169000, co2_saving=0.60,
            memo='야간·주말 공회전 구간을 줄여 월 전력사용량을 절감하는 시나리오'
        ),
        SavingSimulation(
            title='에어 누설 개선 + 배관 최적화',
            equipment_id=None,
            before_kwh=22000, after_kwh=18500, unit_price=130,
            saving_kwh=3500, saving_amount=455000, co2_saving=1.61,
            memo='누설률 저감과 압력손실 개선을 통해 전체 시스템 효율을 개선하는 시나리오'
        ),
    ]
    for s in sims:
        db.session.add(s)

    # ── 6. 유지보수 이력 ──────────────────────────────────
    maint_data = [
        (equipments[0].id, today - timedelta(days=45), '필터 교체', '흡입 필터 교체', 35000, '김기사', today + timedelta(days=45)),
        (equipments[0].id, today - timedelta(days=90), '오일 교체', '콤프레샤 오일 전량 교체', 58000, '이기사', today + timedelta(days=90)),
        (equipments[1].id, today - timedelta(days=30), '필터 교체', '오일 필터 교체', 28000, '김기사', today + timedelta(days=60)),
        (equipments[2].id, today - timedelta(days=10), '점검', '전반 점검 및 벨트 장력 조정', 0, '이기사', today + timedelta(days=20)),
        (equipments[2].id, today - timedelta(days=60), '수리', '냉각팬 모터 교체', 120000, '외주업체', today + timedelta(days=50)),
        (equipments[3].id, today - timedelta(days=20), '오일 교체', '피스톤 오일 교체', 22000, '김기사', today + timedelta(days=70)),
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
        ('오일 필터', 'FL-OIL-01', 'EA', 5, 2, 22000, '부품창고 A-2'),
        ('콤프레샤 오일 (20L)', 'OIL-20-A', 'CAN', 6, 3, 58000, '부품창고 A-2'),
        ('V-벨트 A형', 'BLT-A-38', 'EA', 8, 4, 12000, '부품창고 B-1'),
        ('에어 필터 엘리먼트', 'FL-AIR-01', 'EA', 2, 2, 45000, '부품창고 A-3'),
        ('드레인 밸브', 'VLV-DRN-1', 'EA', 3, 2, 18000, '부품창고 B-2'),
        ('압력 게이지 (7kgf)', 'GAU-7K-01', 'EA', 2, 1, 32000, '부품창고 B-2'),
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
    print('✅ DB 초기화 및 더미데이터 삽입 완료!')
