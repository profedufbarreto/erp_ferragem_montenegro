# config.py
import os

class Config:
    # Ajuste aqui com o que funcionou no teste.py
    # Se foi sem senha, deixe root:@localhost
    SQLALCHEMY_DATABASE_URI = 'mysql+mysqlconnector://root:root@localhost/erp_agroferragem_montenegro'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = 'root'