from app import db
from datetime import datetime

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum('admin', 'gerente', 'funcionario'), default='funcionario')
    employee = db.relationship('Employee', backref='user', uselist=False)

class Employee(db.Model):
    __tablename__ = 'employees'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    cpf = db.Column(db.String(14), unique=True, nullable=False)
    birth_date = db.Column(db.Date)
    
    # --- COLUNAS QUE ESTAVAM FALTANDO ---
    position = db.Column(db.String(100))
    admission_date = db.Column(db.Date)
    blood_type = db.Column(db.String(3))
    emergency_contact = db.Column(db.String(20))
    salary = db.Column(db.Float, default=0.0)
    # ------------------------------------

    cep = db.Column(db.String(9))
    address = db.Column(db.String(200))
    number = db.Column(db.String(10))
    city = db.Column(db.String(100))
    state = db.Column(db.String(2))
    obs = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))