from flask import Blueprint, render_template, request
from models import db, Equipment, EnergyAnalysis, OperationLog
from sqlalchemy import func
from datetime import date, timedelta

energy_bp = Blueprint('energy', __name__)

@energy_bp.route('/')
def index():
    # 설비 목록
    equipments = Equipment.query.order_by(Equipment.name).all()
    eq_id  = request.args.get('eq_id', type=int)
    month  = request.args.get('month', date.today().strftime('%Y-%m'))

    q = EnergyAnalysis.query.filter_by(analysis_month=month)
    if eq_id:
        q = q.filter_by(equipment_id=eq_id)
    analyses = q.all()

    # 설비별 효율 비교 (차트용 - 현재 월)
    eff_data = db.session.query(
        Equipment.name,
        EnergyAnalysis.total_kwh,
        EnergyAnalysis.efficiency_grade,
        EnergyAnalysis.saving_possible,
    ).join(EnergyAnalysis, Equipment.id == EnergyAnalysis.equipment_id)\
     .filter(EnergyAnalysis.analysis_month == month).all()

    # 월별 전력사용 추이 (최근 6개월)
    trend = db.session.query(
        EnergyAnalysis.analysis_month,
        func.sum(EnergyAnalysis.total_kwh).label('kwh'),
        func.sum(EnergyAnalysis.saving_possible).label('saving'),
    ).group_by(EnergyAnalysis.analysis_month)\
     .order_by(EnergyAnalysis.analysis_month).limit(12).all()

    # 요약 집계
    total_kwh     = sum(a.total_kwh or 0 for a in analyses)
    total_saving  = sum(a.saving_possible or 0 for a in analyses)
    total_saving_amt = sum(a.saving_amount or 0 for a in analyses)

    # 월 목록 (드롭다운용)
    months = db.session.query(EnergyAnalysis.analysis_month)\
        .distinct().order_by(EnergyAnalysis.analysis_month.desc()).all()
    months = [m[0] for m in months]

    return render_template('energy/index.html',
        equipments=equipments, analyses=analyses,
        eff_data=eff_data, trend=trend,
        total_kwh=round(total_kwh,1),
        total_saving=round(total_saving,1),
        total_saving_amt=int(total_saving_amt),
        eq_id=eq_id, month=month, months=months,
    )
