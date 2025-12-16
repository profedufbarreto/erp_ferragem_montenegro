from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.models.user import User, Employee
from app import db
from datetime import datetime

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.before_request
def check_admin():
    if session.get('user_role') != 'admin':
        flash("Acesso restrito ao administrador.")
        return redirect(url_for('auth.dashboard'))

@admin_bp.route('/users')
def list_users():
    users = User.query.all()
    return render_template('users/list.html', users=users)

@admin_bp.route('/users/create', methods=['GET', 'POST'])
def create_user():
    if request.method == 'POST':
        # Criação do Usuário
        new_user = User(
            username=request.form['username'],
            password=request.form['password'],
            role=request.form['role']
        )
        db.session.add(new_user)
        db.session.flush() 

        # Criação do Funcionário vinculado
        new_emp = Employee(
            name=request.form['name'],
            cpf=request.form['cpf'],
            birth_date=datetime.strptime(request.form['birth_date'], '%Y-%m-%d'),
            cep=request.form['cep'],
            address=request.form['address'],
            number=request.form['number'],
            city=request.form['city'],
            state=request.form['state'],
            obs=request.form['obs'],
            user_id=new_user.id
        )
        db.session.add(new_emp)
        db.session.commit()
        flash("Usuário e Colaborador criados com sucesso!")
        return redirect(url_for('admin.list_users'))
    
    return render_template('users/create.html')

@admin_bp.route('/users/edit/<int:user_id>', methods=['GET', 'POST'])
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    if request.method == 'POST':
        user.username = request.form['username']
        user.role = request.form['role']
        
        # Só altera a senha se o campo não estiver vazio
        if request.form['password']:
            user.password = request.form['password']
        
        if user.employee:
            user.employee.name = request.form['name']
            user.employee.cpf = request.form['cpf']
            user.employee.cep = request.form['cep']
            user.employee.address = request.form['address']
            user.employee.number = request.form['number']
            user.employee.city = request.form['city']
            user.employee.state = request.form['state']
            user.employee.obs = request.form['obs']
            
        db.session.commit()
        flash("Dados atualizados com sucesso!")
        return redirect(url_for('admin.list_users'))
    
    return render_template('users/edit.html', user=user)

@admin_bp.route('/users/delete/<int:user_id>')
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    
    # Proteção: não deixa deletar o admin principal logado
    if user.username == 'admin':
        flash("O administrador mestre não pode ser removido.")
        return redirect(url_for('admin.list_users'))

    if user.employee:
        db.session.delete(user.employee)
    
    db.session.delete(user)
    db.session.commit()
    flash("Usuário excluído permanentemente.")
    return redirect(url_for('admin.list_users'))