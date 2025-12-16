from app import db
from datetime import datetime

class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True)
    code_ean = db.Column(db.String(13), unique=True)
    description = db.Column(db.String(200), nullable=False)
    ncm = db.Column(db.String(8))
    unit = db.Column(db.String(10))
    cost_price = db.Column(db.Float, default=0.0)
    sale_price = db.Column(db.Float, default=0.0)
    stock_quantity = db.Column(db.Float, default=0.0)
    category = db.Column(db.String(50))

class StockIn(db.Model):
    __tablename__ = 'stock_in'
    id = db.Column(db.Integer, primary_key=True)
    invoice_number = db.Column(db.String(20))
    date_entry = db.Column(db.DateTime, default=datetime.utcnow)
    xml_filename = db.Column(db.String(100))