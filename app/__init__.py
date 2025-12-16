# app/__init__.py
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import Config

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)

    from app.routes.auth import auth_bp
    # Se deixarmos url_prefix='/', o login será acessado em /login
    app.register_blueprint(auth_bp, url_prefix='/') 

    return app