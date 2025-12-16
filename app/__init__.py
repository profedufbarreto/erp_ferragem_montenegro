from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import Config

# Inicializa o SQLAlchemy fora da função para ser acessível em outros arquivos
db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Inicializa o banco de dados com as configurações do app
    db.init_app(app)

    # Importa os Blueprints (Rotas)
    from app.routes.auth import auth_bp
    from app.routes.admin import admin_bp

    # Registra o Blueprint de Autenticação (Login, Logout, etc)
    # url_prefix='/' significa que as rotas começam direto na raiz (ex: /login)
    app.register_blueprint(auth_bp, url_prefix='/') 

    # Registra o Blueprint de Administração (Usuários, RH, Edição)
    # Como definimos url_prefix='/admin' no arquivo admin.py, 
    # as rotas aqui serão acessadas como /admin/users, /admin/users/create, etc.
    app.register_blueprint(admin_bp)

    return app