from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.models.user import User, Employee
from app import db
from datetime import datetime

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.before_request
def check_permissions():
    allowed_roles = ['admin', 'gerente']
    if session.get('user_role') not in allowed_roles:
        flash("Acesso restrito. Retornando ao Dashboard.")
        return redirect(url_for('auth.dashboard'))

# --- MÓDULO RH ---
@admin_bp.route('/rh')
def hr_dashboard():
    employees = Employee.query.all()
    return render_template('admin/hr_dashboard.html', employees=employees)

@admin_bp.route('/rh/edit/<int:employee_id>', methods=['GET', 'POST'])
def edit_employee(employee_id):
    emp = Employee.query.get_or_404(employee_id)
    
    if request.method == 'POST':
        try:
            # Atualiza os dados capturando do formulário
            emp.name = request.form.get('name')
            emp.position = request.form.get('position')
            emp.blood_type = request.form.get('blood_type')
            emp.emergency_contact = request.form.get('emergency_contact')
            
            # Tratamento de salário (caso você use no RH)
            salary_val = request.form.get('salary')
            if salary_val:
                emp.salary = float(salary_val)
            
            # Tratamento da data
            date_str = request.form.get('admission_date')
            if date_str:
                emp.admission_date = datetime.strptime(date_str, '%Y-%m-%d')
            
            db.session.add(emp) # Força a inclusão do objeto na sessão
            db.session.commit()
            flash(f"Dados de {emp.name} atualizados com sucesso!")
            return redirect(url_for('admin.hr_dashboard'))
        except Exception as e:
            db.session.rollback()
            flash(f"Erro ao atualizar RH: {str(e)}")
            
    return render_template('admin/edit_employee.html', emp=emp)

# --- GERENCIAMENTO DE USUÁRIOS ---
@admin_bp.route('/users')
def list_users():
    users = User.query.all()
    return render_template('users/list.html', users=users)

@admin_bp.route('/users/create', methods=['GET', 'POST'])
def create_user():
    if request.method == 'POST':
        try:
            new_user = User(
                username=request.form['username'],
                password=request.form['password'],
                role=request.form['role']
            )
            db.session.add(new_user)
            db.session.flush() 

            new_emp = Employee(
                name=request.form.get('name'),
                cpf=request.form.get('cpf'),
                position=request.form.get('position'),
                blood_type=request.form.get('blood_type'),
                emergency_contact=request.form.get('emergency_contact'),
                salary=float(request.form.get('salary')) if request.form.get('salary') else 0.0,
                cep=request.form.get('cep'),
                address=request.form.get('address'),
                number=request.form.get('number'),
                city=request.form.get('city'),
                state=request.form.get('state'),
                obs=request.form.get('obs'),
                user_id=new_user.id
            )

            if request.form.get('admission_date'):
                new_emp.admission_date = datetime.strptime(request.form.get('admission_date'), '%Y-%m-%d')
            if request.form.get('birth_date'):
                new_emp.birth_date = datetime.strptime(request.form.get('birth_date'), '%Y-%m-%d')

            db.session.add(new_emp)
            db.session.commit()
            flash(f"Colaborador {new_emp.name} cadastrado!")
            return redirect(url_for('admin.list_users'))
        except Exception as e:
            db.session.rollback()
            flash(f"Erro ao cadastrar: {str(e)}")
    
    return render_template('users/create.html')

@admin_bp.route('/users/edit/<int:user_id>', methods=['GET', 'POST'])
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    if session.get('user_role') == 'gerente' and user.role == 'admin':
        flash("Gerentes não podem editar administradores.")
        return redirect(url_for('admin.list_users'))

    if request.method == 'POST':
        try:
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

@admin_bp.route('/users/delete/<int:user_id>')
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.username == 'admin' or (session.get('user_role') == 'gerente' and user.role == 'admin'):
        flash("Permissão negada.")
        return redirect(url_for('admin.list_users'))

    if user.employee:
        db.session.delete(user.employee)
    db.session.delete(user)
    db.session.commit()
    flash("Removido com sucesso.")
    return redirect(url_for('admin.list_users'))