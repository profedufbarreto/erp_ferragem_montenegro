from flask import Blueprint, render_template, request, redirect, url_for, flash
import xml.etree.ElementTree as ET
from app.models.inventory import Product, StockIn
from app import db

inventory_bp = Blueprint('inventory', __name__, url_prefix='/inventory')

# 1. LISTAGEM DE PRODUTOS
@inventory_bp.route('/products')
def list_products():
    products = Product.query.all()
    return render_template('inventory/list.html', products=products)

# 2. IMPORTAÇÃO DE XML (Nota Fiscal)
@inventory_bp.route('/import-xml', methods=['GET', 'POST'])
def import_xml():
    if request.method == 'POST':
        file = request.files.get('xml_file')
        
        if not file or file.filename == '':
            flash("Por favor, selecione um arquivo XML.")
            return redirect(request.url)

        try:
            tree = ET.parse(file)
            root = tree.getroot()
            ns = {'nfe': 'http://www.portalfiscal.inf.br/nfe'}
            items = root.findall('.//nfe:det', ns)
            
            if not items:
                flash("Nenhum produto encontrado no XML.")
                return redirect(request.url)

            for item in items:
                prod_data = item.find('nfe:prod', ns)
                ean = prod_data.find('nfe:cEAN', ns).text
                desc = prod_data.find('nfe:xProd', ns).text
                qtd = float(prod_data.find('nfe:qCom', ns).text)
                v_unit = float(prod_data.find('nfe:vUnCom', ns).text)

                product = Product.query.filter_by(code_ean=ean).first()
                
                if product:
                    product.stock_quantity += qtd
                    product.cost_price = v_unit
                else:
                    new_product = Product(
                        code_ean=ean,
                        description=desc,
                        stock_quantity=qtd,
                        cost_price=v_unit,
                        sale_price=v_unit * 1.5
                    )
                    db.session.add(new_product)

            db.session.commit()
            flash(f"Sucesso! {len(items)} itens processados.")
            return redirect(url_for('inventory.list_products'))

        except Exception as e:
            db.session.rollback()
            flash(f"Erro ao processar XML: {str(e)}")
            return redirect(request.url)
            
    return render_template('inventory/import.html')

# 3. EDIÇÃO DE PRODUTO (Para ajustar preço de venda manualmente)
@inventory_bp.route('/products/edit/<int:product_id>', methods=['GET', 'POST'])
def edit_product(product_id):
    product = Product.query.get_or_404(product_id)
    
    if request.method == 'POST':
        try:
            product.description = request.form.get('description')
            product.code_ean = request.form.get('code_ean')
            product.cost_price = float(request.form.get('cost_price'))
            product.sale_price = float(request.form.get('sale_price'))
            product.stock_quantity = float(request.form.get('stock_quantity'))
            product.category = request.form.get('category')
            product.unit = request.form.get('unit')

            db.session.commit()
            flash(f"Produto '{product.description}' atualizado com sucesso!")
            return redirect(url_for('inventory.list_products'))
        except Exception as e:
            db.session.rollback()
            flash(f"Erro ao atualizar: {str(e)}")
    
    return render_template('inventory/edit.html', product=product)

# 4. EXCLUSÃO DE PRODUTO
@inventory_bp.route('/products/delete/<int:product_id>')
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    flash("Produto removido do estoque.")
    return redirect(url_for('inventory.list_products'))