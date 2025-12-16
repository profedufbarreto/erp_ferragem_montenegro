from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import Config

# Inicializa o banco de dados
db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)

    # 1. Importa os Blueprints (Módulos do Sistema)
    from app.routes.auth import auth_bp
    from app.routes.admin import admin_bp
    from app.routes.inventory import inventory_bp
    from app.routes.client import client_bp  # <--- NOVA LINHA PARA CLIENTES

    # 2. Registra os Blueprints no App
    app.register_blueprint(auth_bp, url_prefix='/') 
    app.register_blueprint(admin_bp)
    app.register_blueprint(inventory_bp)
    app.register_blueprint(client_bp)        # <--- NOVA LINHA PARA CLIENTES

    return app