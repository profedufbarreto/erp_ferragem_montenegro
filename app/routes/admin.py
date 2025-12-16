from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.models.user import User, Employee
from app import db
from datetime import datetime

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.before_request
def check_permissions():
    """Proteção Global: Bloqueia qualquer rota deste arquivo para quem não é Admin ou Gerente"""
    allowed_roles = ['admin', 'gerente']
    if session.get('user_role') not in allowed_roles:
        flash("Acesso restrito. Retornando ao Dashboard.")
        return redirect(url_for('auth.dashboard'))

# --- MÓDULO RH ---
@admin_bp.route('/rh')
def hr_dashboard():
    """Painel Geral de RH para visualização de dados sensíveis"""
    employees = Employee.query.all()
    return render_template('admin/hr_dashboard.html', employees=employees)

# --- GERENCIAMENTO DE USUÁRIOS ---
@admin_bp.route('/users')
def list_users():
    users = User.query.all()
    return render_template('users/list.html', users=users)

@admin_bp.route('/users/create', methods=['GET', 'POST'])
def create_user():
    if request.method == 'POST':
        try:
            # 1. Criação do Login (Tabela Users)
            new_user = User(
                username=request.form['username'],
                password=request.form['password'],
                role=request.form['role']
            )
            db.session.add(new_user)
            db.session.flush() 

            # 2. Criação da Ficha de RH (Tabela Employees)
            new_emp = Employee(
                name=request.form.get('name'),
                cpf=request.form.get('cpf'),
                # Dados de RH
                position=request.form.get('position'),
                blood_type=request.form.get('blood_type'),
                admission_date=datetime.strptime(request.form.get('admission_date'), '%Y-%m-%d') if request.form.get('admission_date') else None,
                emergency_contact=request.form.get('emergency_contact'),
                salary=float(request.form.get('salary')) if request.form.get('salary') else 0.0,
                # Dados Pessoais/Endereço
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
            flash(f"Colaborador {new_emp.name} cadastrado com sucesso no sistema e RH!")
            return redirect(url_for('admin.list_users'))
        except Exception as e:
            db.session.rollback()
            flash(f"Erro ao cadastrar: {str(e)}")
    
    return render_template('users/create.html')

@admin_bp.route('/users/edit/<int:user_id>', methods=['GET', 'POST'])
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    
    # Proteção: Gerente não mexe no Admin Mestre
    if session.get('user_role') == 'gerente' and user.role == 'admin':
        flash("Gerentes não podem editar administradores.")
        return redirect(url_for('admin.list_users'))

    if request.method == 'POST':
        user.username = request.form['username']
        user.role = request.form['role']
        if request.form.get('password'):
            user.password = request.form['password']
        
        if user.employee:
            emp = user.employee
            emp.name = request.form.get('name')
            emp.position = request.form.get('position')
            emp.blood_type = request.form.get('blood_type')
            emp.emergency_contact = request.form.get('emergency_contact')
            emp.address = request.form.get('address')
            emp.number = request.form.get('number')
            # ... outros campos podem ser adicionados aqui
            
        db.session.commit()
        flash("Dados atualizados com sucesso!")
        return redirect(url_for('admin.list_users'))
    
    return render_template('users/edit.html', user=user)

@admin_bp.route('/users/delete/<int:user_id>')
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    
    if user.username == 'admin' or (session.get('user_role') == 'gerente' and user.role == 'admin'):
        flash("Permissão negada para excluir este perfil.")
        return redirect(url_for('admin.list_users'))

    if user.employee:
        db.session.delete(user.employee)
    db.session.delete(user)
    db.session.commit()
    flash("Usuário removido.")
    return redirect(url_for('admin.list_users'))