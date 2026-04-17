import os
import sys
from flask import Flask
from config import Config
from models import db


def get_resource_path(relative_path):
    """
    PyInstaller 번들 환경과 일반 환경 모두에서 올바른 리소스 경로 반환
    - frozen(EXE): sys._MEIPASS 내부 임시 디렉토리
    - 일반 환경: 현재 파일 기준 경로
    """
    if getattr(sys, 'frozen', False):
        base = sys._MEIPASS
    else:
        base = os.environ.get('KY_ENERGY_BUNDLE_DIR',
                              os.path.abspath(os.path.dirname(__file__)))
    return os.path.join(base, relative_path)


def create_app():
    template_folder = get_resource_path('templates')
    static_folder = get_resource_path('static')

    app = Flask(
        __name__,
        template_folder=template_folder,
        static_folder=static_folder
    )
    app.config.from_object(Config)
    db.init_app(app)

    from routes.dashboard   import dashboard_bp
    from routes.equipment   import equipment_bp
    from routes.operation   import operation_bp
    from routes.energy      import energy_bp
    from routes.simulation  import simulation_bp
    from routes.maintenance import maintenance_bp
    from routes.inventory   import inventory_bp

    app.register_blueprint(dashboard_bp)
    app.register_blueprint(equipment_bp,   url_prefix='/equipment')
    app.register_blueprint(operation_bp,   url_prefix='/operation')
    app.register_blueprint(energy_bp,      url_prefix='/energy')
    app.register_blueprint(simulation_bp,  url_prefix='/simulation')
    app.register_blueprint(maintenance_bp, url_prefix='/maintenance')
    app.register_blueprint(inventory_bp,   url_prefix='/inventory')

    return app


app = create_app()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
