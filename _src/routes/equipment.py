from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import db, Equipment
from datetime import date

equipment_bp = Blueprint('equipment', __name__)

@equipment_bp.route('/')
def index():
    status_filter = request.args.get('status', '')
    q = Equipment.query
    if status_filter:
        q = q.filter_by(status=status_filter)
    equipments = q.order_by(Equipment.id).all()
    return render_template('equipment/index.html', equipments=equipments, status_filter=status_filter)

@equipment_bp.route('/new', methods=['GET','POST'])
def new():
    if request.method == 'POST':
        install_date_str = request.form.get('install_date')
        install_date = date.fromisoformat(install_date_str) if install_date_str else None
        hp_str = request.form.get('horsepower','')
        pw_str = request.form.get('rated_power','')
        eq = Equipment(
            name        = request.form['name'],
            model       = request.form.get('model',''),
            horsepower  = float(hp_str) if hp_str else None,
            rated_power = float(pw_str) if pw_str else None,
            install_loc = request.form.get('install_loc',''),
            status      = request.form.get('status','가동중'),
            install_date= install_date,
            memo        = request.form.get('memo',''),
        )
        db.session.add(eq)
        db.session.commit()
        flash('설비가 등록되었습니다.', 'success')
        return redirect(url_for('equipment.index'))
    return render_template('equipment/form.html', eq=None, action='등록')

@equipment_bp.route('/<int:eq_id>')
def detail(eq_id):
    eq = Equipment.query.get_or_404(eq_id)
    return render_template('equipment/detail.html', eq=eq)

@equipment_bp.route('/<int:eq_id>/edit', methods=['GET','POST'])
def edit(eq_id):
    eq = Equipment.query.get_or_404(eq_id)
    if request.method == 'POST':
        eq.name         = request.form['name']
        eq.model        = request.form.get('model','')
        hp_str = request.form.get('horsepower','')
        pw_str = request.form.get('rated_power','')
        eq.horsepower   = float(hp_str) if hp_str else None
        eq.rated_power  = float(pw_str) if pw_str else None
        eq.install_loc  = request.form.get('install_loc','')
        eq.status       = request.form.get('status','가동중')
        install_date_str= request.form.get('install_date','')
        eq.install_date = date.fromisoformat(install_date_str) if install_date_str else None
        eq.memo         = request.form.get('memo','')
        db.session.commit()
        flash('설비 정보가 수정되었습니다.', 'success')
        return redirect(url_for('equipment.detail', eq_id=eq.id))
    return render_template('equipment/form.html', eq=eq, action='수정')

@equipment_bp.route('/<int:eq_id>/delete', methods=['POST'])
def delete(eq_id):
    eq = Equipment.query.get_or_404(eq_id)
    db.session.delete(eq)
    db.session.commit()
    flash('설비가 삭제되었습니다.', 'warning')
    return redirect(url_for('equipment.index'))
