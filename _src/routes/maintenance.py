from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import db, MaintenanceLog, Equipment
from datetime import date

maintenance_bp = Blueprint('maintenance', __name__)

@maintenance_bp.route('/')
def index():
    eq_id = request.args.get('eq_id', type=int)
    q = MaintenanceLog.query
    if eq_id:
        q = q.filter_by(equipment_id=eq_id)
    logs = q.order_by(MaintenanceLog.maint_date.desc()).all()
    equipments = Equipment.query.order_by(Equipment.name).all()

    # 점검 임박 설비 (next_date 기준 30일 이내)
    today = date.today()
    upcoming = MaintenanceLog.query\
        .filter(MaintenanceLog.next_date != None)\
        .filter(MaintenanceLog.next_date <= date.fromordinal(today.toordinal() + 30))\
        .order_by(MaintenanceLog.next_date).all()

    return render_template('maintenance/index.html',
                           logs=logs, equipments=equipments,
                           eq_id=eq_id, upcoming=upcoming, today=today)

@maintenance_bp.route('/new', methods=['GET','POST'])
def new():
    equipments = Equipment.query.order_by(Equipment.name).all()
    if request.method == 'POST':
        def _d(k): v=request.form.get(k,''); return date.fromisoformat(v) if v else None
        def _f(k): v=request.form.get(k,''); return float(v) if v else 0
        log = MaintenanceLog(
            equipment_id = int(request.form['equipment_id']),
            maint_date   = _d('maint_date'),
            maint_type   = request.form.get('maint_type',''),
            description  = request.form.get('description',''),
            cost         = _f('cost'),
            worker       = request.form.get('worker',''),
            next_date    = _d('next_date'),
        )
        db.session.add(log)
        db.session.commit()
        flash('정비 이력이 저장되었습니다.', 'success')
        return redirect(url_for('maintenance.index'))
    return render_template('maintenance/form.html', equipments=equipments,
                           log=None, today=date.today())

@maintenance_bp.route('/<int:log_id>/delete', methods=['POST'])
def delete(log_id):
    log = MaintenanceLog.query.get_or_404(log_id)
    db.session.delete(log)
    db.session.commit()
    flash('삭제되었습니다.', 'warning')
    return redirect(url_for('maintenance.index'))
