from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import db, SavingSimulation, Equipment

simulation_bp = Blueprint('simulation', __name__)

@simulation_bp.route('/')
def index():
    sims = SavingSimulation.query.order_by(SavingSimulation.id.desc()).all()
    return render_template('simulation/index.html', sims=sims)

@simulation_bp.route('/new', methods=['GET','POST'])
def new():
    equipments = Equipment.query.order_by(Equipment.name).all()
    if request.method == 'POST':
        def _f(k): v=request.form.get(k,''); return float(v) if v else 0
        before = _f('before_kwh')
        after  = _f('after_kwh')
        price  = _f('unit_price') or 130
        saving_kwh = round(before - after, 2)
        saving_amt = round(saving_kwh * price, 0)
        co2        = round(saving_kwh * 0.4594 / 1000, 3)   # tCO2 환산계수
        eq_id_str  = request.form.get('equipment_id','')
        sim = SavingSimulation(
            title        = request.form.get('title',''),
            equipment_id = int(eq_id_str) if eq_id_str else None,
            before_kwh   = before,
            after_kwh    = after,
            unit_price   = price,
            saving_kwh   = saving_kwh,
            saving_amount= saving_amt,
            co2_saving   = co2,
            memo         = request.form.get('memo',''),
        )
        db.session.add(sim)
        db.session.commit()
        flash('시뮬레이션이 저장되었습니다.', 'success')
        return redirect(url_for('simulation.index'))
    return render_template('simulation/form.html', equipments=equipments, sim=None)

@simulation_bp.route('/<int:sim_id>')
def detail(sim_id):
    sim = SavingSimulation.query.get_or_404(sim_id)
    return render_template('simulation/detail.html', sim=sim)

@simulation_bp.route('/<int:sim_id>/delete', methods=['POST'])
def delete(sim_id):
    sim = SavingSimulation.query.get_or_404(sim_id)
    db.session.delete(sim)
    db.session.commit()
    flash('삭제되었습니다.', 'warning')
    return redirect(url_for('simulation.index'))
