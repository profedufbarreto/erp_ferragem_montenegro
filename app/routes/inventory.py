from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
import xml.etree.ElementTree as ET
from app.models.inventory import Product, StockIn
from app import db

inventory_bp = Blueprint('inventory', __name__, url_prefix='/inventory')

# 1. LISTAGEM COM BUSCA
@inventory_bp.route('/products')
def list_products():
    search = request.args.get('search')
    if search:
        products = Product.query.filter(
            (Product.name.ilike(f'%{search}%')) | (Product.code == search)
        ).all()
    else:
        products = Product.query.all()
    return render_template('inventory/list.html', products=products)

# 2. DASHBOARD PATRIMONIAL (Valor do Estoque)
@inventory_bp.route('/dashboard')
def inventory_dashboard():
    products = Product.query.all()
    total_cost = sum((p.stock or 0) * float(p.cost_price or 0) for p in products)
    total_sale = sum((p.stock or 0) * float(p.price or 0) for p in products)
    low_stock = [p for p in products if (p.stock or 0) <= 5]
    
    return render_template('inventory/dashboard.html', 
                           total_cost=total_cost, 
                           total_sale=total_sale, 
                           low_stock=low_stock,
                           potential_profit=total_sale - total_cost)

# 3. API PARA BUSCA DINÂMICA
@inventory_bp.route('/api/search')
def api_search():
    query = request.args.get('q', '')
    if len(query) < 2: return jsonify([])
    products = Product.query.filter(
        (Product.name.ilike(f'%{query}%')) | (Product.code.ilike(f'%{query}%'))
    ).limit(10).all()
    return jsonify([{
        'id': p.id, 
        'code': p.code, 
        'name': p.name, 
        'price': float(p.final_price), 
        'stock': p.stock
    } for p in products])

# 4. CADASTRO MANUAL
@inventory_bp.route('/add', methods=['GET', 'POST'])
def add_product():
    if request.method == 'POST':
        try:
            new_prod = Product(
                name=request.form.get('name'),
                code=request.form.get('code') or Product.generate_next_code(),
                cost_price=float(request.form.get('cost_price') or 0),
                price=float(request.form.get('price') or 0),
                stock=int(request.form.get('stock') or 0),
                category=request.form.get('category'),
                unit=request.form.get('unit') or 'UN',
                ncm=request.form.get('ncm') or '00000000',
                cfop=request.form.get('cfop') or '5102'
            )
            db.session.add(new_prod)
            db.session.commit()
            flash("Produto cadastrado com sucesso!")
            return redirect(url_for('inventory.list_products'))
        except Exception as e:
            db.session.rollback()
            flash(f"Erro ao cadastrar: {str(e)}")
    return render_template('inventory/add_product.html')

# 5. IMPORTAÇÃO XML
@inventory_bp.route('/import-xml', methods=['GET', 'POST'])
def import_xml():
    if request.method == 'POST':
        file = request.files.get('xml_file')
        if not file: return redirect(request.url)
        try:
            tree = ET.parse(file)
            root = tree.getroot()
            ns = {'nfe': 'http://www.portalfiscal.inf.br/nfe'}
            items = root.findall('.//nfe:det', ns)
            with db.session.no_autoflush:
                for item in items:
                    prod_data = item.find('nfe:prod', ns)
                    def get_text(node, tag):
                        el = node.find(tag, ns)
                        return el.text if el is not None else None

                    ean = get_text(prod_data, 'nfe:cEAN') or "SEM_GTIN"
                    product = Product.query.filter_by(code=ean).first()
                    
                    q_com = int(float(get_text(prod_data, 'nfe:qCom') or 0))
                    v_un = float(get_text(prod_data, 'nfe:vUnCom') or 0)

                    if product:
                        product.stock += q_com
                        product.cost_price = v_un
                    else:
                        new_p = Product(
                            code=ean, 
                            name=get_text(prod_data, 'nfe:xProd'),
                            stock=q_com, 
                            cost_price=v_un, 
                            price=v_un * 1.5,
                            unit=get_text(prod_data, 'nfe:uCom') or 'UN',
                            ncm=get_text(prod_data, 'nfe:NCM') or '00000000',
                            cfop=get_text(prod_data, 'nfe:CFOP') or '5102'
                        )
                        db.session.add(new_p)
            db.session.commit()
            flash("Importação concluída!")
            return redirect(url_for('inventory.list_products'))
        except Exception as e:
            db.session.rollback()
            flash(f"Erro: {str(e)}")
    return render_template('inventory/import.html')

# 6. EDIÇÃO E EXCLUSÃO
@inventory_bp.route('/edit/<int:product_id>', methods=['GET', 'POST'])
def edit_product(product_id):
    product = Product.query.get_or_404(product_id)
    if request.method == 'POST':
        product.name = request.form.get('name')
        product.code = request.form.get('code')
        product.cost_price = float(request.form.get('cost_price') or 0)
        product.price = float(request.form.get('price') or 0)
        product.discount = float(request.form.get('discount') or 0)
        product.stock = int(request.form.get('stock') or 0)
        product.unit = request.form.get('unit')
        product.ncm = request.form.get('ncm')
        product.cfop = request.form.get('cfop')
        db.session.commit()
        flash("Atualizado!")
        return redirect(url_for('inventory.list_products'))
    return render_template('inventory/edit.html', product=product)

@inventory_bp.route('/delete/<int:product_id>')
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    flash("Removido!")
    return redirect(url_for('inventory.list_products'))