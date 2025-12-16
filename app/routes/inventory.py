from flask import Blueprint, render_template, request, redirect, url_for, flash
import xml.etree.ElementTree as ET
from app.models.inventory import Product, StockIn
from app import db

inventory_bp = Blueprint('inventory', __name__, url_prefix='/inventory')

@inventory_bp.route('/products')
def list_products():
    products = Product.query.all()
    return render_template('inventory/list.html', products=products)

@inventory_bp.route('/import-xml', methods=['GET', 'POST'])
def import_xml():
    if request.method == 'POST':
        file = request.files.get('xml_file')
        
        if not file or file.filename == '':
            flash("Por favor, selecione um arquivo XML.")
            return redirect(request.url)

        try:
            # Faz a leitura do arquivo XML
            tree = ET.parse(file)
            root = tree.getroot()
            
            # Namespace padrão da NF-e (essencial para o Python encontrar as tags)
            ns = {'nfe': 'http://www.portalfiscal.inf.br/nfe'}

            # Procura todos os itens da nota (tag <det>)
            items = root.findall('.//nfe:det', ns)
            
            if not items:
                flash("Nenhum produto encontrado dentro do XML. Verifique o formato.")
                return redirect(request.url)

            for item in items:
                prod_data = item.find('nfe:prod', ns)
                
                # Extrai os dados das tags específicas
                ean = prod_data.find('nfe:cEAN', ns).text
                desc = prod_data.find('nfe:xProd', ns).text
                qtd = float(prod_data.find('nfe:qCom', ns).text)
                v_unit = float(prod_data.find('nfe:vUnCom', ns).text)

                # Busca se o produto já existe no banco pelo EAN
                product = Product.query.filter_by(code_ean=ean).first()
                
                if product:
                    # Se já existe, soma a quantidade e atualiza o preço de custo
                    product.stock_quantity += qtd
                    product.cost_price = v_unit
                else:
                    # Se não existe, cria um novo produto
                    new_product = Product(
                        code_ean=ean,
                        description=desc,
                        stock_quantity=qtd,
                        cost_price=v_unit,
                        sale_price=v_unit * 1.5 # Sugestão de venda: custo + 50%
                    )
                    db.session.add(new_product)

            db.session.commit()
            flash(f"Sucesso! {len(items)} itens processados e estoque atualizado.")
            return redirect(url_for('inventory.list_products'))

        except Exception as e:
            db.session.rollback()
            flash(f"Erro ao processar XML: {str(e)}")
            return redirect(request.url)
            
    return render_template('inventory/import.html')