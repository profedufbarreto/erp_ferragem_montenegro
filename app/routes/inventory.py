from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
import xml.etree.ElementTree as ET
from app.models.inventory import Product, StockIn
from app import db

inventory_bp = Blueprint('inventory', __name__, url_prefix='/inventory')

# --- 1. DASHBOARD ESTRATÉGICO ---
@inventory_bp.route('/dashboard')
def inventory_dashboard():
    # Busca produtos reais do banco
    products = Product.query.all()
    
    # Cálculos Patrimoniais Reais
    total_cost = sum((p.stock or 0) * float(p.cost_price or 0) for p in products)
    total_sale = sum((p.stock or 0) * float(p.price or 0) for p in products)
    
    # Filtra itens com estoque baixo (entre 1 e 5)
    low_stock = [p for p in products if 0 < (p.stock or 0) <= 5]
    
    # Ranking de produtos (Top 5 por quantidade em estoque)
    top_products = Product.query.filter(Product.stock > 0).order_by(Product.stock.desc()).limit(5).all()

    # Formas de Pagamento (Iniciam zeradas - serão alimentadas pelo módulo de vendas)
    payment_stats = [
        {'method': 'Pix', 'count': 0, 'color': '#00ff88'},
        {'method': 'Dinheiro', 'count': 0, 'color': '#ffcc00'},
        {'method': 'Cartão Crédito', 'count': 0, 'color': '#3498db'},
        {'method': 'Cartão Débito', 'count': 0, 'color': '#9b59b6'}
    ]

    return render_template('inventory/dashboard.html', 
                           total_cost=total_cost, 
                           total_sale=total_sale, 
                           low_stock=low_stock,
                           top_products=top_products,
                           payment_stats=payment_stats,
                           potential_profit=total_sale - total_cost)

# --- 2. LISTAGEM PRINCIPAL ---
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

# --- 3. API PARA BUSCA DINÂMICA (Autocomplete) ---
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

# --- 4. CADASTRO MANUAL ---
@inventory_bp.route('/add', methods=['GET', 'POST'])
def add_product():
    if request.method == 'POST':
        try:
            name = request.form.get('name')
            # Se não digitar código, o sistema gera o próximo (001, 002...)
            code = request.form.get('code') or Product.generate_next_code()
            
            new_prod = Product(
                name=name,
                code=code,
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
            flash(f"Produto '{name}' cadastrado com sucesso!")
            return redirect(url_for('inventory.list_products'))
        except Exception as e:
            db.session.rollback()
            flash(f"Erro ao cadastrar: {str(e)}")
            
    return render_template('inventory/add_product.html')

# --- 5. IMPORTAÇÃO XML ---
@inventory_bp.route('/import-xml', methods=['GET', 'POST'])
def import_xml():
    if request.method == 'POST':
        file = request.files.get('xml_file')
        if not file: 
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
                        el = node.find(tag, ns)
                        return el.text if el is not None else None

                    ean = get_text(prod_data, 'nfe:cEAN') or "SEM_GTIN"
                    product_name = get_text(prod_data, 'nfe:xProd')
                    
                    # Tenta encontrar o produto pelo EAN ou pelo Nome exato
                    product = Product.query.filter(
                        (Product.code == ean) | (Product.name == product_name)
                    ).first()
                    
                    q_com = int(float(get_text(prod_data, 'nfe:qCom') or 0))
                    v_un = float(get_text(prod_data, 'nfe:vUnCom') or 0)
                    xml_ncm = get_text(prod_data, 'nfe:NCM') or '00000000'
                    xml_cfop = get_text(prod_data, 'nfe:CFOP') or '5102'

                    if product:
                        # Se já existe, atualiza estoque e custo
                        product.stock += q_com
                        product.cost_price = v_un
                        product.ncm = xml_ncm
                    else:
                        # Se não existe, cria novo
                        new_p = Product(
                            code=ean, 
                            name=product_name,
                            stock=q_com, 
                            cost_price=v_un, 
                            price=v_un * 1.5, # Margem padrão 50%
                            unit=get_text(prod_data, 'nfe:uCom') or 'UN',
                            ncm=xml_ncm, 
                            cfop=xml_cfop
                        )
                        db.session.add(new_p)
            
            db.session.commit()
            flash("Importação de XML concluída!")
            return redirect(url_for('inventory.list_products'))
        except Exception as e:
            db.session.rollback()
            flash(f"Erro ao processar XML: {str(e)}")
            
    return render_template('inventory/import.html')

# --- 6. EDIÇÃO E EXCLUSÃO ---
@inventory_bp.route('/edit/<int:product_id>', methods=['GET', 'POST'])
def edit_product(product_id):
    product = Product.query.get_or_404(product_id)
    if request.method == 'POST':
        try:
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
            flash("Produto atualizado com sucesso!")
            return redirect(url_for('inventory.list_products'))
        except Exception as e:
            db.session.rollback()
            flash(f"Erro ao atualizar: {str(e)}")
            
    return render_template('inventory/edit.html', product=product)

@inventory_bp.route('/delete/<int:product_id>')
def delete_product(product_id):
    try:
        product = Product.query.get_or_404(product_id)
        db.session.delete(product)
        db.session.commit()
        flash("Produto removido do sistema.")
    except Exception as e:
        db.session.rollback()
        flash(f"Erro ao remover: {str(e)}")
    return redirect(url_for('inventory.list_products'))