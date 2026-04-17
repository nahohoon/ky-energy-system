from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import db, Part, InventoryLog
from datetime import date

inventory_bp = Blueprint('inventory', __name__)

@inventory_bp.route('/')
def index():
    parts = Part.query.order_by(Part.id).all()
    low_stock = [p for p in parts if p.stock_qty <= p.safe_qty]
    return render_template('inventory/index.html', parts=parts, low_stock=low_stock)

@inventory_bp.route('/new_part', methods=['GET','POST'])
def new_part():
    if request.method == 'POST':
        def _f(k): v=request.form.get(k,''); return float(v) if v else 0
        def _i(k): v=request.form.get(k,''); return int(v) if v else 0
        p = Part(
            name       = request.form['name'],
            part_no    = request.form.get('part_no',''),
            unit       = request.form.get('unit','EA'),
            stock_qty  = _i('stock_qty'),
            safe_qty   = _i('safe_qty'),
            unit_price = _f('unit_price'),
            location   = request.form.get('location',''),
            memo       = request.form.get('memo',''),
        )
        db.session.add(p)
        db.session.commit()
        flash('부품이 등록되었습니다.', 'success')
        return redirect(url_for('inventory.index'))
    return render_template('inventory/part_form.html', part=None)

@inventory_bp.route('/inout', methods=['GET','POST'])
def inout():
    parts = Part.query.order_by(Part.name).all()
    if request.method == 'POST':
        part_id = int(request.form['part_id'])
        in_out  = request.form['in_out']
        qty     = int(request.form.get('qty', 1))
        part = Part.query.get_or_404(part_id)
        if in_out == '입고':
            part.stock_qty += qty
        else:
            if part.stock_qty < qty:
                flash('재고가 부족합니다.', 'danger')
                return redirect(url_for('inventory.inout'))
            part.stock_qty -= qty
        log = InventoryLog(
            part_id  = part_id,
            log_date = date.today(),
            in_out   = in_out,
            qty      = qty,
            reason   = request.form.get('reason',''),
            worker   = request.form.get('worker',''),
        )
        db.session.add(log)
        db.session.commit()
        flash(f'{in_out} 처리되었습니다.', 'success')
        return redirect(url_for('inventory.index'))
    return render_template('inventory/inout_form.html', parts=parts)

@inventory_bp.route('/logs')
def logs():
    part_id = request.args.get('part_id', type=int)
    q = InventoryLog.query
    if part_id:
        q = q.filter_by(part_id=part_id)
    logs = q.order_by(InventoryLog.log_date.desc(), InventoryLog.id.desc()).all()
    parts = Part.query.order_by(Part.name).all()
    return render_template('inventory/logs.html', logs=logs, parts=parts, part_id=part_id)
