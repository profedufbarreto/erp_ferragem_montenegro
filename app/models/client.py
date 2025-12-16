from app import db
from datetime import datetime

class Client(db.Model):
    __tablename__ = 'clients'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    document = db.Column(db.String(20), unique=True, nullable=False) # CPF ou CNPJ
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    
    # Endereço
    cep = db.Column(db.String(10))
    address = db.Column(db.String(200))
    number = db.Column(db.String(10))
    city = db.Column(db.String(100))
    state = db.Column(db.String(2))
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)