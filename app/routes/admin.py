from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.models.user import User, Employee
from app import db
from datetime import datetime

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.before_request
def check_permissions():
    # Agora permitimos 'admin' OU 'gerente'
    allowed_roles = ['admin', 'gerente']
    if session.get('user_role') not in allowed_roles:
        flash("Acesso restrito. Você não possui permissão para gerenciar usuários.")
        return redirect(url_for('auth.dashboard'))

@admin_bp.route('/users')
def list_users():
    users = User.query.all()
    return render_template('users/list.html', users=users)

@admin_bp.route('/users/create', methods=['GET', 'POST'])
def create_user():
    if request.method == 'POST':
        try:
            # Criação do Usuário
            new_user = User(
                username=request.form['username'],
                password=request.form['password'],
                role=request.form['role']
            )
            db.session.add(new_user)
            db.session.flush() 

            # Criação do Funcionário vinculado
            # Usamos .get() para evitar erros se algum campo opcional vier vazio
            new_emp = Employee(
                name=request.form.get('name'),
                cpf=request.form.get('cpf'),
                birth_date=datetime.strptime(request.form.get('birth_date'), '%Y-%m-%d') if request.form.get('birth_date') else None,
                cep=request.form.get('cep'),
                address=request.form.get('address'),
                number=request.form.get('number'),
                city=request.form.get('city'),
                state=request.form.get('state'),
                obs=request.form.get('obs'),
                user_id=new_user.id
            )
            db.session.add(new_emp)
            db.session.commit()
            flash("Usuário e Colaborador criados com sucesso!")
            return redirect(url_for('admin.list_users'))
        except Exception as e:
            db.session.rollback()
            flash(f"Erro ao cadastrar: {str(e)}")
            return redirect(url_for('admin.create_user'))
    
    return render_template('users/create.html')

@admin_bp.route('/users/edit/<int:user_id>', methods=['GET', 'POST'])
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    
    # Segurança extra: Gerente não pode editar o Admin Mestre
    if session.get('user_role') == 'gerente' and user.role == 'admin':
        flash("Gerentes não podem editar usuários administradores.")
        return redirect(url_for('admin.list_users'))

    if request.method == 'POST':
        user.username = request.form['username']
        user.role = request.form['role']
        
        if request.form.get('password'):
            user.password = request.form['password']
        
        if user.employee:
            user.employee.name = request.form.get('name')
            user.employee.cpf = request.form.get('cpf')
            user.employee.cep = request.form.get('cep')
            user.employee.address = request.form.get('address')
            user.employee.number = request.form.get('number')
            user.employee.city = request.form.get('city')
            user.employee.state = request.form.get('state')
            user.employee.obs = request.form.get('obs')
            
        db.session.commit()
        flash("Dados atualizados com sucesso!")
        return redirect(url_for('admin.list_users'))
    
    return render_template('users/edit.html', user=user)

@admin_bp.route('/users/delete/<int:user_id>')
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    
    # Proteções de exclusão
    if user.username == 'admin':
        flash("O administrador mestre não pode ser removido.")
        return redirect(url_for('admin.list_users'))
    
    if session.get('user_role') == 'gerente' and user.role == 'admin':
        flash("Gerentes não podem excluir administradores.")
        return redirect(url_for('admin.list_users'))

    if user.employee:
        db.session.delete(user.employee)
    
    db.session.delete(user)
    db.session.commit()
    flash("Usuário excluído permanentemente.")
    return redirect(url_for('admin.list_users'))