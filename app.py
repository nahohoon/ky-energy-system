from flask import Flask
from config import Config
from models import db

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)

    from routes.dashboard  import dashboard_bp
    from routes.equipment  import equipment_bp
    from routes.operation  import operation_bp
    from routes.energy     import energy_bp
    from routes.simulation import simulation_bp
    from routes.maintenance import maintenance_bp
    from routes.inventory  import inventory_bp

    app.register_blueprint(dashboard_bp)
    app.register_blueprint(equipment_bp,  url_prefix='/equipment')
    app.register_blueprint(operation_bp,  url_prefix='/operation')
    app.register_blueprint(energy_bp,     url_prefix='/energy')
    app.register_blueprint(simulation_bp, url_prefix='/simulation')
    app.register_blueprint(maintenance_bp,url_prefix='/maintenance')
    app.register_blueprint(inventory_bp,  url_prefix='/inventory')

    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
