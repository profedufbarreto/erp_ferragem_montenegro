from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.models.user import User, Employee
from app import db
from datetime import datetime

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# Proteção de Rota: Apenas Admin e Gerente entram no módulo Admin
@admin_bp.before_request
def check_permissions():
    allowed_roles = ['admin', 'gerente']
    if session.get('user_role') not in allowed_roles:
        flash("Acesso restrito. Retornando ao Dashboard.")
        return redirect(url_for('inventory.inventory_dashboard'))

# --- 1. MÓDULO RH (DASHBOARD) ---
@admin_bp.route('/rh')
def hr_dashboard():
    employees = Employee.query.all()
    return render_template('admin/hr_dashboard.html', employees=employees)

# --- 2. GERENCIAMENTO DE USUÁRIOS (LISTAGEM) ---
@admin_bp.route('/users')
def list_users():
    users = User.query.all()
    # Note: O template deve estar em templates/users/list.html
    return render_template('users/list.html', users=users)

# --- 3. CRIAR USUÁRIO E COLABORADOR (UNIFICADO) ---
@admin_bp.route('/users/create', methods=['GET', 'POST'])
def create_user():
    if request.method == 'POST':
        try:
            # 1. Criar o Usuário (Senha em texto puro conforme solicitado)
            new_user = User(
                username=request.form['username'],
                password=request.form['password'],
                role=request.form['role']
            )
            db.session.add(new_user)
            db.session.flush() # Gera o ID do usuário para vincular ao Employee

            # 2. Criar o registro de RH (Employee)
            new_emp = Employee(
                name=request.form.get('name'),
                cpf=request.form.get('cpf'),
                position=request.form.get('position'),
                blood_type=request.form.get('blood_type'),
                emergency_contact=request.form.get('emergency_contact'),
                user_id=new_user.id
            )

            # Tratamento de Datas
            if request.form.get('admission_date'):
                new_emp.admission_date = datetime.strptime(request.form.get('admission_date'), '%Y-%m-%d')
            
            if request.form.get('birth_date'):
                new_emp.birth_date = datetime.strptime(request.form.get('birth_date'), '%Y-%m-%d')

            db.session.add(new_emp)
            db.session.commit()
            
            flash(f"Colaborador {new_emp.name} e usuário {new_user.username} cadastrados com sucesso!")
            return redirect(url_for('admin.list_users'))
            
        except Exception as e:
            db.session.rollback()
            flash(f"Erro ao cadastrar: {str(e)}")
            
    return render_template('users/create.html')

# --- 4. EDIÇÃO DE USUÁRIO E RH ---
@admin_bp.route('/users/edit/<int:user_id>', methods=['GET', 'POST'])
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    
    # Bloqueio: Gerente não edita Admin
    if session.get('user_role') == 'gerente' and user.role == 'admin':
        flash("Gerentes não podem editar administradores.")
        return redirect(url_for('admin.list_users'))

    if request.method == 'POST':
        try:
            user.username = request.form['username']
            user.role = request.form['role']
            
            # Se preencher a senha, atualiza (texto puro)
            if request.form.get('password'):
                user.password = request.form['password']
            
            # Atualiza dados de RH vinculados
            if user.employee:
                emp = user.employee
                emp.name = request.form.get('name')
                emp.position = request.form.get('position')
                emp.blood_type = request.form.get('blood_type')
                emp.emergency_contact = request.form.get('emergency_contact')
                
                date_adm = request.form.get('admission_date')
                if date_adm:
                    emp.admission_date = datetime.strptime(date_adm, '%Y-%m-%d')
            
            db.session.commit()
            flash("Dados atualizados com sucesso!")
            return redirect(url_for('admin.list_users'))
        except Exception as e:
            db.session.rollback()
            flash(f"Erro ao salvar: {str(e)}")
    
    return render_template('users/edit.html', user=user)

# --- 5. EXCLUSÃO ---
@admin_bp.route('/users/delete/<int:user_id>')
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    
    # Proteção para não deletar o admin principal
    if user.username == 'admin':
        flash("O administrador principal não pode ser removido.")
        return redirect(url_for('admin.list_users'))

    try:
        # Devido ao cascade="all, delete-orphan" no model, 
        # deletar o user já deleta o employee automaticamente.
        db.session.delete(user)
        db.session.commit()
        flash("Usuário e registro de RH removidos.")
    except Exception as e:
        db.session.rollback()
        flash(f"Erro ao remover: {str(e)}")
        
    return redirect(url_for('admin.list_users'))