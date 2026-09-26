from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models import User

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.board'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        user = User.query.filter_by(username=username).first()

        if not user or not user.check_password(password):
            flash('Usuário ou senha inválidos.', 'danger')
            return render_template('login.html')

        if not user.is_approved:
            flash('⏳ Sua conta ainda não foi aprovada por um administrador.', 'warning')
            return render_template('login.html')

        user.last_seen = datetime.utcnow()
        db.session.commit()
        login_user(user, remember=True)
        flash('Login realizado com sucesso!', 'success')
        next_page = request.args.get('next')
        return redirect(next_page or url_for('main.board'))

    return render_template('login.html')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.board'))

    # 🔑 Detecta se é o primeiro cadastro do sistema → vira admin automaticamente
    is_first_user = User.query.count() == 0

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm = request.form.get('confirm_password', '')

        if not username or not email or not password:
            flash('Preencha todos os campos.', 'danger')
            return redirect(url_for('auth.register'))

        if password != confirm:
            flash('As senhas não coincidem.', 'danger')
            return redirect(url_for('auth.register'))

        if User.query.filter_by(username=username).first():
            flash('Usuário já existe.', 'danger')
            return redirect(url_for('auth.register'))

        if User.query.filter_by(email=email).first():
            flash('Email já cadastrado.', 'danger')
            return redirect(url_for('auth.register'))

        # O primeiro usuário do sistema já nasce admin + aprovado
        user = User(
            username=username,
            email=email,
            is_admin=is_first_user,
            is_approved=is_first_user,
        )
        if is_first_user:
            user.approved_at = datetime.utcnow()

        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        if is_first_user:
            flash('🎉 Primeiro usuário criado como ADMINISTRADOR! Faça login.', 'success')
        else:
            flash('✅ Conta criada! Aguarde aprovação de um administrador.', 'info')

        return redirect(url_for('auth.login'))

    return render_template('register.html', is_first_user=is_first_user)


@auth_bp.route('/logout')
@login_required
def logout():
    current_user.last_seen = None
    db.session.commit()
    logout_user()
    flash('Você saiu da sua conta.', 'info')
    return redirect(url_for('auth.login'))