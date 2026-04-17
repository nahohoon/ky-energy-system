from flask import Blueprint, render_template, request
from models import db, Equipment, EnergyAnalysis, OperationLog
from sqlalchemy import func
from datetime import date

energy_bp = Blueprint('energy', __name__)

@energy_bp.route('/')
def index():
    equipments = Equipment.query.order_by(Equipment.name).all()
    eq_id = request.args.get('eq_id', type=int)
    today = date.today()

    months = db.session.query(EnergyAnalysis.analysis_month)\
        .distinct().order_by(EnergyAnalysis.analysis_month.desc()).all()
    months = [m[0] for m in months]
    month = request.args.get('month', months[0] if months else today.strftime('%Y-%m'))

    q = EnergyAnalysis.query.filter_by(analysis_month=month)
    if eq_id:
        q = q.filter_by(equipment_id=eq_id)
    analyses = q.all()

    total_kwh = sum(a.total_kwh or 0 for a in analyses)
    total_saving = sum(a.saving_possible or 0 for a in analyses)
    total_saving_amt = sum(a.saving_amount or 0 for a in analyses)
    avg_unit_kwh = round(sum(a.unit_kwh or 0 for a in analyses) / len(analyses), 4) if analyses else 0

    inefficient = [a for a in analyses if a.efficiency_grade in ('C', 'D')]

    eff_data = db.session.query(
        Equipment.name,
        EnergyAnalysis.total_kwh,
        EnergyAnalysis.efficiency_grade,
        EnergyAnalysis.saving_possible,
        EnergyAnalysis.unit_kwh
    ).join(EnergyAnalysis, Equipment.id == EnergyAnalysis.equipment_id)\
     .filter(EnergyAnalysis.analysis_month == month).all()

    trend = db.session.query(
        EnergyAnalysis.analysis_month,
        func.sum(EnergyAnalysis.total_kwh).label('kwh'),
        func.sum(EnergyAnalysis.saving_possible).label('saving')
    ).group_by(EnergyAnalysis.analysis_month)\
     .order_by(EnergyAnalysis.analysis_month).limit(12).all()

    run_hours_map = {}
    for eq in equipments:
        rh = db.session.query(func.sum(OperationLog.run_hours))\
            .filter(OperationLog.equipment_id == eq.id)\
            .filter(OperationLog.log_date.like(f'{month}%')).scalar() or 0
        run_hours_map[eq.id] = round(rh, 1)

    enriched_analyses = []
    for a in analyses:
        run_hours = run_hours_map.get(a.equipment_id, 0)
        actual_unit = round((a.total_kwh / run_hours), 2) if run_hours else 0
        is_inefficient = a.efficiency_grade in ('C', 'D')
        enriched_analyses.append({
            'analysis': a,
            'run_hours': run_hours,
            'actual_unit': actual_unit,
            'is_inefficient': is_inefficient,
        })

    return render_template(
        'energy/index.html',
        equipments=equipments,
        analyses=analyses,
        enriched_analyses=enriched_analyses,
        eff_data=eff_data,
        trend=trend,
        total_kwh=round(total_kwh, 1),
        total_saving=round(total_saving, 1),
        total_saving_amt=int(total_saving_amt),
        avg_unit_kwh=avg_unit_kwh,
        inefficient=inefficient,
        eq_id=eq_id,
        month=month,
        months=months
    )
