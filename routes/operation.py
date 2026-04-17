from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import db, Equipment, OperationLog
from datetime import date

operation_bp = Blueprint('operation', __name__)

@operation_bp.route('/')
def index():
    eq_id  = request.args.get('eq_id', type=int)
    month  = request.args.get('month', '')
    q = OperationLog.query
    if eq_id:
        q = q.filter_by(equipment_id=eq_id)
    if month:
        q = q.filter(OperationLog.log_date.like(f'{month}%'))
    logs = q.order_by(OperationLog.log_date.desc()).all()
    equipments = Equipment.query.order_by(Equipment.name).all()
    return render_template('operation/index.html',
                           logs=logs, equipments=equipments,
                           eq_id=eq_id, month=month)

@operation_bp.route('/new', methods=['GET','POST'])
def new():
    equipments = Equipment.query.order_by(Equipment.name).all()
    if request.method == 'POST':
        def _f(key): v=request.form.get(key,''); return float(v) if v else None
        log = OperationLog(
            equipment_id = int(request.form['equipment_id']),
            log_date     = date.fromisoformat(request.form['log_date']),
            run_hours    = _f('run_hours'),
            power_kwh    = _f('power_kwh'),
            load_rate    = _f('load_rate'),
            pressure     = _f('pressure'),
            frequency    = _f('frequency'),
            memo         = request.form.get('memo',''),
        )
        db.session.add(log)
        db.session.commit()
        flash('운전 로그가 저장되었습니다.', 'success')
        return redirect(url_for('operation.index'))
    return render_template('operation/form.html', equipments=equipments,
                           log=None, today=date.today())

@operation_bp.route('/<int:log_id>/delete', methods=['POST'])
def delete(log_id):
    log = OperationLog.query.get_or_404(log_id)
    db.session.delete(log)
    db.session.commit()
    flash('삭제되었습니다.', 'warning')
    return redirect(url_for('operation.index'))
