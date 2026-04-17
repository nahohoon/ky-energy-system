from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Company(db.Model):
    __tablename__ = 'companies'
    id         = db.Column(db.Integer, primary_key=True)
    name       = db.Column(db.String(100), nullable=False)
    bizno      = db.Column(db.String(20))
    address    = db.Column(db.String(200))
    contact    = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    equipments = db.relationship('Equipment', backref='company', lazy=True)

class Equipment(db.Model):
    __tablename__ = 'equipments'
    id           = db.Column(db.Integer, primary_key=True)
    company_id   = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=True)
    name         = db.Column(db.String(100), nullable=False)
    model        = db.Column(db.String(100))
    horsepower   = db.Column(db.Float)           # HP
    rated_power  = db.Column(db.Float)           # kW
    install_loc  = db.Column(db.String(100))
    status       = db.Column(db.String(20), default='가동중')  # 가동중/정지/점검중
    install_date = db.Column(db.Date)
    memo         = db.Column(db.Text)
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)
    op_logs      = db.relationship('OperationLog', backref='equipment', lazy=True)
    maint_logs   = db.relationship('MaintenanceLog', backref='equipment', lazy=True)
    energy_data  = db.relationship('EnergyAnalysis', backref='equipment', lazy=True)

class OperationLog(db.Model):
    __tablename__ = 'operation_logs'
    id           = db.Column(db.Integer, primary_key=True)
    equipment_id = db.Column(db.Integer, db.ForeignKey('equipments.id'), nullable=False)
    log_date     = db.Column(db.Date, nullable=False)
    run_hours    = db.Column(db.Float)   # 가동시간(h)
    power_kwh    = db.Column(db.Float)   # 전력사용량(kWh)
    load_rate    = db.Column(db.Float)   # 부하율(%)
    pressure     = db.Column(db.Float)   # 압력(kgf/cm²)
    frequency    = db.Column(db.Float)   # 주파수(Hz)
    memo         = db.Column(db.Text)
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)

class EnergyAnalysis(db.Model):
    __tablename__ = 'energy_analysis'
    id              = db.Column(db.Integer, primary_key=True)
    equipment_id    = db.Column(db.Integer, db.ForeignKey('equipments.id'), nullable=False)
    analysis_month  = db.Column(db.String(7))   # YYYY-MM
    total_kwh       = db.Column(db.Float)
    unit_kwh        = db.Column(db.Float)        # 단위소비전력
    efficiency_grade= db.Column(db.String(10))  # A/B/C/D
    saving_possible = db.Column(db.Float)        # 절감 가능량(kWh)
    saving_amount   = db.Column(db.Float)        # 절감 예상금액(원)
    created_at      = db.Column(db.DateTime, default=datetime.utcnow)

class SavingSimulation(db.Model):
    __tablename__ = 'saving_simulations'
    id              = db.Column(db.Integer, primary_key=True)
    title           = db.Column(db.String(200))
    equipment_id    = db.Column(db.Integer, db.ForeignKey('equipments.id'), nullable=True)
    before_kwh      = db.Column(db.Float)
    after_kwh       = db.Column(db.Float)
    unit_price      = db.Column(db.Float, default=130)   # 원/kWh
    saving_kwh      = db.Column(db.Float)
    saving_amount   = db.Column(db.Float)
    co2_saving      = db.Column(db.Float)   # tCO2
    memo            = db.Column(db.Text)
    created_at      = db.Column(db.DateTime, default=datetime.utcnow)

class MaintenanceLog(db.Model):
    __tablename__ = 'maintenance_logs'
    id           = db.Column(db.Integer, primary_key=True)
    equipment_id = db.Column(db.Integer, db.ForeignKey('equipments.id'), nullable=False)
    maint_date   = db.Column(db.Date, nullable=False)
    maint_type   = db.Column(db.String(50))   # 필터교체/오일교체/점검/수리
    description  = db.Column(db.Text)
    cost         = db.Column(db.Float, default=0)
    worker       = db.Column(db.String(50))
    next_date    = db.Column(db.Date)
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)

class Part(db.Model):
    __tablename__ = 'parts'
    id           = db.Column(db.Integer, primary_key=True)
    name         = db.Column(db.String(100), nullable=False)
    part_no      = db.Column(db.String(50))
    unit         = db.Column(db.String(20), default='EA')
    stock_qty    = db.Column(db.Integer, default=0)
    safe_qty     = db.Column(db.Integer, default=2)   # 안전재고
    unit_price   = db.Column(db.Float, default=0)
    location     = db.Column(db.String(50))
    memo         = db.Column(db.Text)
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)
    inv_logs     = db.relationship('InventoryLog', backref='part', lazy=True)

class InventoryLog(db.Model):
    __tablename__ = 'inventory_logs'
    id         = db.Column(db.Integer, primary_key=True)
    part_id    = db.Column(db.Integer, db.ForeignKey('parts.id'), nullable=False)
    log_date   = db.Column(db.Date, nullable=False)
    in_out     = db.Column(db.String(10))   # 입고/출고
    qty        = db.Column(db.Integer)
    reason     = db.Column(db.String(100))
    worker     = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
