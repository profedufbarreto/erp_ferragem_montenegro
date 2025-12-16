from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.models.user import User
from app import db

auth_bp = Blueprint('auth', __name__)

# Alteramos aqui para que a raiz do site seja o login
@auth_bp.route('/')
def index():
    return redirect(url_for('auth.login'))

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.password == password:
            session['user_id'] = user.id
            session['user_role'] = user.role
            return redirect(url_for('auth.dashboard'))
        
        flash('Usuário ou senha incorretos.')
    
    return render_template('auth/login.html')

@auth_bp.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    return render_template('dashboard/index.html')