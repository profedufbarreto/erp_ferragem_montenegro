from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
import xml.etree.ElementTree as ET
from app.models.inventory import Product, StockIn
from app import db

inventory_bp = Blueprint('inventory', __name__, url_prefix='/inventory')

# 1. LISTAGEM PRINCIPAL COM FILTRO VIA URL
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

# 2. API PARA BUSCA DINÂMICA (Para o Autocomplete enquanto digita)
@inventory_bp.route('/api/search')
def api_search():
    query = request.args.get('q', '')
    if len(query) < 2:
        return jsonify([])
    
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

# 3. IMPORTAÇÃO XML BLINDADA
@inventory_bp.route('/import-xml', methods=['GET', 'POST'])
def import_xml():
    if request.method == 'POST':
        file = request.files.get('xml_file')
        if not file or file.filename == '':
            flash("Selecione um arquivo XML.")
            return redirect(request.url)
        try:
            tree = ET.parse(file)
            root = tree.getroot()
            ns = {'nfe': 'http://www.portalfiscal.inf.br/nfe'}
            items = root.findall('.//nfe:det', ns)
            
            with db.session.no_autoflush:
                for item in items:
                    prod_data = item.find('nfe:prod', ns)
                    if prod_data is None: continue

                    def get_text(node, tag):
                        element = node.find(tag, ns)
                        return element.text if element is not None else None

                    ean = get_text(prod_data, 'nfe:cEAN') or "SEM_GTIN"
                    name = get_text(prod_data, 'nfe:xProd') or "PRODUTO SEM NOME"
                    
                    try:
                        qtd = int(float(get_text(prod_data, 'nfe:qCom') or 0))
                        v_unit = float(get_text(prod_data, 'nfe:vUnCom') or 0)
                    except: qtd, v_unit = 0, 0.0

                    product = Product.query.filter_by(code=ean).first()
                    if product:
                        product.stock += qtd
                        product.cost_price = v_unit
                    else:
                        new_product = Product(
                            code=ean, name=name, stock=qtd,
                            cost_price=v_unit, price=v_unit * 1.5, 
                            unit=get_text(prod_data, 'nfe:uCom') or 'UN'
                        )
                        db.session.add(new_product)
            db.session.commit()
            flash("Importação concluída com sucesso!")
            return redirect(url_for('inventory.list_products'))
        except Exception as e:
            db.session.rollback()
            flash(f"Erro: {str(e)}")
    return render_template('inventory/import.html')

# 4. EDIÇÃO DE PRODUTO (VERSÃO ÚNICA E COMPLETA)
@inventory_bp.route('/edit/<int:product_id>', methods=['GET', 'POST'])
def edit_product(product_id):
    product = Product.query.get_or_404(product_id)
    if request.method == 'POST':
        try:
            name = request.form.get('name')
            if not name:
                flash("Nome obrigatório!")
                return redirect(url_for('inventory.edit_product', product_id=product_id))
            
            product.name = name
            product.code = request.form.get('code')
            product.cost_price = float(request.form.get('cost_price') or 0)
            product.price = float(request.form.get('price') or 0)
            product.discount = float(request.form.get('discount') or 0)
            product.stock = int(request.form.get('stock') or 0)
            product.unit = request.form.get('unit')
            
            db.session.commit()
            flash(f"Produto '{product.name}' atualizado!")
            return redirect(url_for('inventory.list_products'))
        except Exception as e:
            db.session.rollback()
            flash(f"Erro ao salvar: {str(e)}")
            
    return render_template('inventory/edit.html', product=product)

# 5. EXCLUSÃO DE PRODUTO
@inventory_bp.route('/delete/<int:product_id>')
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    flash("Removido!")
    return redirect(url_for('inventory.list_products'))