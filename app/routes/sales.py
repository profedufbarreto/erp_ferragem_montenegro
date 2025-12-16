from flask import Blueprint, render_template, request, jsonify
from app.models.inventory import Product
from app import db

sales_bp = Blueprint('sales', __name__, url_prefix='/vendas')

@sales_bp.route('/')
def pos():
    return render_template('sales/pos.html')

@sales_bp.route('/buscar')
def search_product():
    query = request.args.get('q', '')
    product = Product.query.filter((Product.code == query) | (Product.name.ilike(f'%{query}%'))).first()
    if product:
        return jsonify({
            'code': product.code,
            'name': product.name,
            'price': float(product.final_price),
            'stock': product.stock
        })
    return jsonify({'error': 'Não encontrado'}), 404

@sales_bp.route('/finalizar', methods=['POST'])
def finalize_sale():
    data = request.get_json()
    cart = data.get('cart', [])
    
    try:
        for item in cart:
            p = Product.query.filter_by(code=item['code']).first()
            if p:
                if p.stock < item['qty']:
                    return jsonify({'error': f'Estoque insuficiente para: {p.name}'}), 400
                
                # AQUI ACONTECE A BAIXA
                p.stock -= int(item['qty'])
        
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500