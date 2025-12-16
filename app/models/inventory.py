from app import db
from datetime import datetime

class Product(db.Model):
    __tablename__ = 'products'
    __table_args__ = {'extend_existing': True} 

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False) # Aceita EAN de 13 dígitos
    name = db.Column(db.String(100), nullable=False)
    cost_price = db.Column(db.Numeric(10, 2), default=0.00)
    price = db.Column(db.Numeric(10, 2), nullable=False, default=0.00)
    discount = db.Column(db.Float, default=0.0) 
    stock = db.Column(db.Integer, default=0)
    category = db.Column(db.String(50))
    unit = db.Column(db.String(10), default='UN')
    
    stock_history = db.relationship('StockIn', backref='product', lazy=True)

    @property
    def final_price(self):
        """Preço calculado para venda após o desconto"""
        if self.discount > 0:
            return float(self.price) * (1 - (self.discount / 100))
        return float(self.price)

    @staticmethod
    def generate_next_code():
        last_product = Product.query.order_by(Product.id.desc()).first()
        if not last_product or not last_product.code or not last_product.code.isdigit():
            return "001"
        next_code = int(last_product.code) + 1
        return f"{next_code:03d}"

class StockIn(db.Model):
    __tablename__ = 'stock_ins'
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    date = db.Column(db.DateTime, default=datetime.now)