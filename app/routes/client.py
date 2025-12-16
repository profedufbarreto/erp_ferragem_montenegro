from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.models.client import Client
from app import db

client_bp = Blueprint('client', __name__, url_prefix='/clients')

@client_bp.route('/')
def list_clients():
    clients = Client.query.all()
    return render_template('clients/list.html', clients=clients)

@client_bp.route('/create', methods=['GET', 'POST'])
def create_client():
    if request.method == 'POST':
        try:
            new_client = Client(
                name=request.form.get('name'),
                document=request.form.get('document'),
                email=request.form.get('email'),
                phone=request.form.get('phone'),
                cep=request.form.get('cep'),
                address=request.form.get('address'),
                number=request.form.get('number'),
                city=request.form.get('city'),
                state=request.form.get('state')
            )
            db.session.add(new_client)
            db.session.commit()
            flash(f"Cliente {new_client.name} cadastrado com sucesso!")
            return redirect(url_for('client.list_clients'))
        except Exception as e:
            db.session.rollback()
            flash(f"Erro ao cadastrar cliente: {str(e)}")
            
    return render_template('clients/create.html')