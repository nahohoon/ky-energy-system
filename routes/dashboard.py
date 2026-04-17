from flask import Blueprint, render_template
from models import db, Equipment, OperationLog, MaintenanceLog, EnergyAnalysis
from sqlalchemy import func
from datetime import date, timedelta

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
def index():
    # 설비 현황
    total_eq   = Equipment.query.count()
    running_eq = Equipment.query.filter_by(status='가동중').count()
    check_eq   = Equipment.query.filter_by(status='점검중').count()

    # 이번 달 전력사용량
    today = date.today()
    month_start = today.replace(day=1)
    month_kwh = db.session.query(func.sum(OperationLog.power_kwh))\
        .filter(OperationLog.log_date >= month_start).scalar() or 0

    # 예상 절감액 (최근 에너지분석 기준)
    this_month = today.strftime('%Y-%m')
    total_saving = db.session.query(func.sum(EnergyAnalysis.saving_amount))\
        .filter(EnergyAnalysis.analysis_month == this_month).scalar() or 0
    if total_saving == 0:
        prev_month = (today.replace(day=1) - timedelta(days=1)).strftime('%Y-%m')
        total_saving = db.session.query(func.sum(EnergyAnalysis.saving_amount))\
            .filter(EnergyAnalysis.analysis_month == prev_month).scalar() or 0

    # 최근 운전 로그 (10건)
    recent_logs = db.session.query(OperationLog)\
        .order_by(OperationLog.log_date.desc(), OperationLog.id.desc()).limit(10).all()

    # 최근 정비 이력 (5건)
    recent_maint = db.session.query(MaintenanceLog)\
        .order_by(MaintenanceLog.maint_date.desc()).limit(5).all()

    # 설비별 이번달 전력사용량 (차트)
    equip_power = db.session.query(
        Equipment.name,
        func.sum(OperationLog.power_kwh).label('total')
    ).join(OperationLog, Equipment.id == OperationLog.equipment_id)\
     .filter(OperationLog.log_date >= month_start)\
     .group_by(Equipment.id).all()

    # 월별 절감액 (최근 6개월, 차트)
    monthly_saving = db.session.query(
        EnergyAnalysis.analysis_month,
        func.sum(EnergyAnalysis.saving_amount).label('total')
    ).group_by(EnergyAnalysis.analysis_month)\
     .order_by(EnergyAnalysis.analysis_month.desc()).limit(6).all()
    monthly_saving = list(reversed(monthly_saving))

    return render_template('dashboard/index.html',
        total_eq=total_eq, running_eq=running_eq, check_eq=check_eq,
        month_kwh=round(month_kwh,1), total_saving=int(total_saving),
        recent_logs=recent_logs, recent_maint=recent_maint,
        equip_power=equip_power, monthly_saving=monthly_saving,
        today=today
    )
