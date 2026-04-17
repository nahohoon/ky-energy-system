from flask import Blueprint, render_template
from models import db, Equipment, OperationLog, MaintenanceLog, EnergyAnalysis, SavingSimulation
from sqlalchemy import func
from datetime import date, timedelta

dashboard_bp = Blueprint('dashboard', __name__)

def get_status_comment(name, grade):
    nm = (name or '').upper()
    if 'DRYER' in nm or '드라이어' in nm or 'DRYER' in nm:
        return '비효율 운전'
    if grade == 'D':
        return '과부하 운전'
    if grade == 'C':
        return '효율 저하'
    return '운전 최적화 필요'

@dashboard_bp.route('/')
def index():
    today = date.today()
    month_start = today.replace(day=1)
    this_month = today.strftime('%Y-%m')

    total_eq = Equipment.query.count()
    running_eq = Equipment.query.filter_by(status='가동중').count()
    check_eq = Equipment.query.filter_by(status='점검중').count()
    stop_eq = total_eq - running_eq - check_eq

    month_kwh = db.session.query(func.sum(OperationLog.power_kwh))\
        .filter(OperationLog.log_date >= month_start).scalar() or 0

    prev_start = (month_start - timedelta(days=1)).replace(day=1)
    prev_end = month_start - timedelta(days=1)
    prev_kwh = db.session.query(func.sum(OperationLog.power_kwh))\
        .filter(OperationLog.log_date >= prev_start, OperationLog.log_date <= prev_end).scalar() or 0
    kwh_diff = round(month_kwh - prev_kwh, 1)

    total_saving = db.session.query(func.sum(EnergyAnalysis.saving_amount))\
        .filter(EnergyAnalysis.analysis_month == this_month).scalar() or 0
    if total_saving == 0:
        prev_month = (month_start - timedelta(days=1)).strftime('%Y-%m')
        total_saving = db.session.query(func.sum(EnergyAnalysis.saving_amount))\
            .filter(EnergyAnalysis.analysis_month == prev_month).scalar() or 0

    total_co2 = db.session.query(func.sum(SavingSimulation.co2_saving)).scalar() or 0
    recent_logs = OperationLog.query.order_by(OperationLog.log_date.desc(), OperationLog.id.desc()).limit(8).all()
    recent_maint = MaintenanceLog.query.order_by(MaintenanceLog.maint_date.desc()).limit(5).all()

    equip_power = db.session.query(
        Equipment.id,
        Equipment.name,
        Equipment.horsepower,
        Equipment.install_loc,
        Equipment.status,
        func.sum(OperationLog.power_kwh).label('total')
    ).join(OperationLog, Equipment.id == OperationLog.equipment_id)\
     .filter(OperationLog.log_date >= month_start)\
     .group_by(Equipment.id)\
     .order_by(func.sum(OperationLog.power_kwh).desc()).all()

    monthly_power = db.session.query(
        EnergyAnalysis.analysis_month,
        func.sum(EnergyAnalysis.total_kwh).label('kwh'),
        func.sum(EnergyAnalysis.saving_possible).label('saving')
    ).group_by(EnergyAnalysis.analysis_month)\
     .order_by(EnergyAnalysis.analysis_month.desc()).limit(6).all()
    monthly_power = list(reversed(monthly_power))

    analysis_base_month = this_month
    top_inefficient_raw = db.session.query(
        Equipment.name,
        EnergyAnalysis.efficiency_grade,
        EnergyAnalysis.saving_possible,
        EnergyAnalysis.saving_amount,
        EnergyAnalysis.total_kwh
    ).join(EnergyAnalysis, Equipment.id == EnergyAnalysis.equipment_id)\
     .filter(EnergyAnalysis.analysis_month == analysis_base_month)\
     .filter(EnergyAnalysis.efficiency_grade.in_(['C', 'D']))\
     .order_by(EnergyAnalysis.saving_amount.desc()).limit(3).all()

    if not top_inefficient_raw:
        prev_month = (month_start - timedelta(days=1)).strftime('%Y-%m')
        analysis_base_month = prev_month
        top_inefficient_raw = db.session.query(
            Equipment.name,
            EnergyAnalysis.efficiency_grade,
            EnergyAnalysis.saving_possible,
            EnergyAnalysis.saving_amount,
            EnergyAnalysis.total_kwh
        ).join(EnergyAnalysis, Equipment.id == EnergyAnalysis.equipment_id)\
         .filter(EnergyAnalysis.analysis_month == analysis_base_month)\
         .filter(EnergyAnalysis.efficiency_grade.in_(['C', 'D']))\
         .order_by(EnergyAnalysis.saving_amount.desc()).limit(3).all()

    top_inefficient = []
    for item in top_inefficient_raw:
        status_text = '저효율' if item.efficiency_grade == 'C' else '과부하'
        comment = get_status_comment(item.name, item.efficiency_grade)
        top_inefficient.append({
            'name': item.name,
            'grade': item.efficiency_grade,
            'status_text': status_text,
            'comment': comment,
            'saving_possible': item.saving_possible,
            'saving_amount': item.saving_amount,
            'total_kwh': item.total_kwh,
        })

    sims = SavingSimulation.query.order_by(SavingSimulation.saving_amount.desc()).limit(3).all()
    total_sim_saving = db.session.query(func.sum(SavingSimulation.saving_amount)).scalar() or 0

    upcoming_maint = MaintenanceLog.query\
        .filter(MaintenanceLog.next_date != None)\
        .filter(MaintenanceLog.next_date <= today + timedelta(days=30))\
        .filter(MaintenanceLog.next_date >= today)\
        .order_by(MaintenanceLog.next_date).limit(5).all()

    return render_template(
        'dashboard/index.html',
        total_eq=total_eq, running_eq=running_eq, check_eq=check_eq, stop_eq=stop_eq,
        month_kwh=round(month_kwh, 1), prev_kwh=round(prev_kwh, 1), kwh_diff=kwh_diff,
        total_saving=int(total_saving), total_co2=round(total_co2, 2),
        recent_logs=recent_logs, recent_maint=recent_maint,
        equip_power=equip_power, monthly_power=monthly_power,
        top_inefficient=top_inefficient, analysis_base_month=analysis_base_month,
        sims=sims, total_sim_saving=int(total_sim_saving),
        upcoming_maint=upcoming_maint, today=today
    )
