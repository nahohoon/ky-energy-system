from flask import Blueprint, render_template
from models import db, Equipment, OperationLog, MaintenanceLog, EnergyAnalysis, SavingSimulation
from sqlalchemy import func
from datetime import date, timedelta

dashboard_bp = Blueprint('dashboard', __name__)

# ── 효율등급 → 상태 텍스트·코멘트·절감 우선순위 ─────────────────────────
GRADE_META = {
    'A': {'label': 'A등급', 'badge': 'success', 'text': '최적 운전',      'priority': 4},
    'B': {'label': 'B등급', 'badge': 'info',    'text': '양호',           'priority': 3},
    'C': {'label': 'C등급', 'badge': 'warning', 'text': '효율 저하',      'priority': 2},
    'D': {'label': 'D등급', 'badge': 'danger',  'text': '과부하/비효율',  'priority': 1},
}

EQUIP_COMMENT = {
    '드라이어': '응결수 과다 · 재생 사이클 비정상',
    'DRYER':    '응결수 과다 · 재생 사이클 비정상',
    '피스톤':   '압축 효율 저하 · 밸브 마모 의심',
    '스크류':   '인버터 미적용 또는 부하율 고정 운전',
}

def _equip_comment(name):
    n = name or ''
    for kw, msg in EQUIP_COMMENT.items():
        if kw in n:
            return msg
    return '운전 조건 재설정 및 인버터 최적화 필요'


@dashboard_bp.route('/')
def index():
    today       = date.today()
    month_start = today.replace(day=1)
    this_month  = today.strftime('%Y-%m')

    # ── 설비 현황 ───────────────────────────────────────────────────────
    total_eq   = Equipment.query.count()
    running_eq = Equipment.query.filter_by(status='가동중').count()
    check_eq   = Equipment.query.filter_by(status='점검중').count()
    stop_eq    = total_eq - running_eq - check_eq

    # ── 이번 달 전력사용량 ───────────────────────────────────────────────
    month_kwh = db.session.query(func.sum(OperationLog.power_kwh))\
        .filter(OperationLog.log_date >= month_start).scalar() or 0

    prev_start = (month_start - timedelta(days=1)).replace(day=1)
    prev_end   = month_start - timedelta(days=1)
    prev_kwh   = db.session.query(func.sum(OperationLog.power_kwh))\
        .filter(OperationLog.log_date >= prev_start,
                OperationLog.log_date <= prev_end).scalar() or 0
    kwh_diff = round(month_kwh - prev_kwh, 1)

    # ── 절감 핵심 KPI ──────────────────────────────────────────────────
    # 1) 절감 시뮬레이션 기반 월 절감액 합계 (가장 현실적인 수치)
    total_sim_saving = db.session.query(
        func.sum(SavingSimulation.saving_amount)
    ).scalar() or 0

    # 2) 절감 전력량(kWh) 합계
    total_saving_kwh = db.session.query(
        func.sum(SavingSimulation.saving_kwh)
    ).scalar() or 0
    if not total_saving_kwh:
        # saving_kwh 없으면 before-after 차이로 계산
        rows = db.session.query(
            SavingSimulation.before_kwh, SavingSimulation.after_kwh
        ).all()
        total_saving_kwh = sum(
            (r.before_kwh or 0) - (r.after_kwh or 0) for r in rows
        )

    # 3) CO2 절감량 (tCO2)
    total_co2 = db.session.query(
        func.sum(SavingSimulation.co2_saving)
    ).scalar() or 0
    if not total_co2:
        # co2_saving 없으면 saving_kwh * 0.4663 kg/kWh 환산
        total_co2 = round(total_saving_kwh * 0.4663 / 1000, 2)

    # 4) EnergyAnalysis 기반 절감 가능액 (보조 수치)
    ea_saving = db.session.query(
        func.sum(EnergyAnalysis.saving_amount)
    ).filter(EnergyAnalysis.analysis_month == this_month).scalar() or 0
    if ea_saving == 0:
        prev_month = (month_start - timedelta(days=1)).strftime('%Y-%m')
        ea_saving  = db.session.query(
            func.sum(EnergyAnalysis.saving_amount)
        ).filter(EnergyAnalysis.analysis_month == prev_month).scalar() or 0

    # 최종 월 절감액: sim 값이 있으면 우선 사용
    monthly_saving = int(total_sim_saving) if total_sim_saving else int(ea_saving)
    annual_saving  = monthly_saving * 12

    # ── 진단 결과 ─────────────────────────────────────────────────────
    # 비효율(C/D) 설비 수
    inefficient_count = db.session.query(
        func.count(func.distinct(EnergyAnalysis.equipment_id))
    ).filter(
        EnergyAnalysis.efficiency_grade.in_(['C', 'D'])
    ).scalar() or 0

    # 전체 설비 중 비효율 비율
    inefficient_rate = round(inefficient_count / total_eq * 100) if total_eq else 0

    # 평균 효율등급 (A=4,B=3,C=2,D=1 환산)
    grade_map = {'A': 4, 'B': 3, 'C': 2, 'D': 1}
    grade_rows = db.session.query(
        EnergyAnalysis.efficiency_grade,
        func.count(EnergyAnalysis.id).label('cnt')
    ).filter(EnergyAnalysis.analysis_month == this_month)\
     .group_by(EnergyAnalysis.efficiency_grade).all()
    if not grade_rows:
        prev_month = (month_start - timedelta(days=1)).strftime('%Y-%m')
        grade_rows = db.session.query(
            EnergyAnalysis.efficiency_grade,
            func.count(EnergyAnalysis.id).label('cnt')
        ).filter(EnergyAnalysis.analysis_month == prev_month)\
         .group_by(EnergyAnalysis.efficiency_grade).all()

    total_grade_cnt = sum(r.cnt for r in grade_rows)
    avg_score = (
        sum(grade_map.get(r.efficiency_grade, 2) * r.cnt for r in grade_rows)
        / total_grade_cnt
    ) if total_grade_cnt else 2.5

    if avg_score >= 3.5:
        overall_grade, grade_badge = 'A', 'success'
    elif avg_score >= 2.5:
        overall_grade, grade_badge = 'B', 'info'
    elif avg_score >= 1.5:
        overall_grade, grade_badge = 'C', 'warning'
    else:
        overall_grade, grade_badge = 'D', 'danger'

    # ── 비효율 설비 TOP 3 ─────────────────────────────────────────────
    analysis_base_month = this_month
    top_raw = db.session.query(
        Equipment.name,
        EnergyAnalysis.efficiency_grade,
        EnergyAnalysis.saving_possible,
        EnergyAnalysis.saving_amount,
        EnergyAnalysis.total_kwh
    ).join(EnergyAnalysis, Equipment.id == EnergyAnalysis.equipment_id)\
     .filter(EnergyAnalysis.analysis_month == analysis_base_month)\
     .filter(EnergyAnalysis.efficiency_grade.in_(['C', 'D']))\
     .order_by(EnergyAnalysis.saving_amount.desc()).limit(3).all()

    if not top_raw:
        prev_month = (month_start - timedelta(days=1)).strftime('%Y-%m')
        analysis_base_month = prev_month
        top_raw = db.session.query(
            Equipment.name,
            EnergyAnalysis.efficiency_grade,
            EnergyAnalysis.saving_possible,
            EnergyAnalysis.saving_amount,
            EnergyAnalysis.total_kwh
        ).join(EnergyAnalysis, Equipment.id == EnergyAnalysis.equipment_id)\
         .filter(EnergyAnalysis.analysis_month == analysis_base_month)\
         .filter(EnergyAnalysis.efficiency_grade.in_(['C', 'D']))\
         .order_by(EnergyAnalysis.saving_amount.desc()).limit(3).all()

    # TOP3 없으면 전 등급에서 절감액 순으로 보완
    if not top_raw:
        analysis_base_month = this_month
        top_raw = db.session.query(
            Equipment.name,
            EnergyAnalysis.efficiency_grade,
            EnergyAnalysis.saving_possible,
            EnergyAnalysis.saving_amount,
            EnergyAnalysis.total_kwh
        ).join(EnergyAnalysis, Equipment.id == EnergyAnalysis.equipment_id)\
         .order_by(EnergyAnalysis.saving_amount.desc()).limit(3).all()

    top_inefficient = []
    for rank, item in enumerate(top_raw, 1):
        g = item.efficiency_grade or 'C'
        meta = GRADE_META.get(g, GRADE_META['C'])
        saving_kwh = round((item.saving_possible or 0), 1)
        saving_won = int(item.saving_amount or 0)
        total_kwh  = round(item.total_kwh or 0, 1)
        saving_rate = round(saving_kwh / total_kwh * 100, 1) if total_kwh else 0

        top_inefficient.append({
            'rank':         rank,
            'name':         item.name,
            'grade':        g,
            'grade_label':  meta['label'],
            'grade_badge':  meta['badge'],
            'status_text':  meta['text'],
            'comment':      _equip_comment(item.name),
            'saving_possible': saving_kwh,
            'saving_amount':   saving_won,
            'total_kwh':       total_kwh,
            'saving_rate':     saving_rate,
        })

    # ── 설비별 전력사용량 (이번 달) ───────────────────────────────────
    equip_power = db.session.query(
        Equipment.name,
        func.sum(OperationLog.power_kwh).label('total')
    ).join(OperationLog, Equipment.id == OperationLog.equipment_id)\
     .filter(OperationLog.log_date >= month_start)\
     .group_by(Equipment.id)\
     .order_by(func.sum(OperationLog.power_kwh).desc()).all()

    # 절감 가능량 매핑 (설비별)
    ea_map = {}
    for ea in EnergyAnalysis.query.filter_by(analysis_month=analysis_base_month).all():
        ea_map[ea.equipment_id] = ea

    equip_power_with_saving = []
    for eq in equip_power:
        equip_power_with_saving.append({
            'name':  eq.name,
            'total': round(eq.total or 0, 1),
        })

    # ── 월별 전력 추이 (최근 6개월) ──────────────────────────────────
    monthly_power = db.session.query(
        EnergyAnalysis.analysis_month,
        func.sum(EnergyAnalysis.total_kwh).label('kwh'),
        func.sum(EnergyAnalysis.saving_possible).label('saving')
    ).group_by(EnergyAnalysis.analysis_month)\
     .order_by(EnergyAnalysis.analysis_month.desc()).limit(6).all()
    monthly_power = list(reversed(monthly_power))

    # ── 최근 운전 로그 ─────────────────────────────────────────────────
    recent_logs = OperationLog.query\
        .order_by(OperationLog.log_date.desc(), OperationLog.id.desc()).limit(8).all()

    # ── 정비 예정 설비 ─────────────────────────────────────────────────
    upcoming_maint = MaintenanceLog.query\
        .filter(MaintenanceLog.next_date != None)\
        .filter(MaintenanceLog.next_date <= today + timedelta(days=30))\
        .filter(MaintenanceLog.next_date >= today)\
        .order_by(MaintenanceLog.next_date).limit(4).all()

    # ── 절감 시뮬레이션 목록 ──────────────────────────────────────────
    sims = SavingSimulation.query\
        .order_by(SavingSimulation.saving_amount.desc()).limit(3).all()

    return render_template(
        'dashboard/index.html',
        # 설비 현황
        total_eq=total_eq, running_eq=running_eq,
        check_eq=check_eq, stop_eq=stop_eq,
        # 전력
        month_kwh=round(month_kwh, 1),
        prev_kwh=round(prev_kwh, 1),
        kwh_diff=kwh_diff,
        # 절감 KPI
        monthly_saving=monthly_saving,
        annual_saving=annual_saving,
        total_saving_kwh=round(total_saving_kwh, 1),
        total_co2=round(total_co2, 2),
        # 진단 결과
        inefficient_count=inefficient_count,
        inefficient_rate=inefficient_rate,
        overall_grade=overall_grade,
        grade_badge=grade_badge,
        # TOP3
        top_inefficient=top_inefficient,
        analysis_base_month=analysis_base_month,
        # 차트
        equip_power=equip_power_with_saving,
        monthly_power=monthly_power,
        # 하단
        recent_logs=recent_logs,
        upcoming_maint=upcoming_maint,
        sims=sims,
        total_sim_saving=int(total_sim_saving),
        today=today,
    )
