from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from functools import wraps

from app import db
from app.models import User, Task


admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


# ============================================================
# DECORATOR: só admins
# ============================================================
def admin_required(f):
    @wraps(f)
    @login_required
    def wrapper(*args, **kwargs):
        if not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return wrapper


# ============================================================
# LISTAGEM
# ============================================================
@admin_bp.route('/')
@admin_required
def dashboard():
    pending = User.query.filter_by(is_approved=False)\
                        .order_by(User.created_at.desc()).all()
    approved = User.query.filter_by(is_approved=True)\
                         .order_by(User.username).all()

    stats = {
        'total_users': User.query.count(),
        'pending': len(pending),
        'approved': len(approved),
        'admins': User.query.filter_by(is_admin=True).count(),
        'total_tasks': Task.query.count(),
    }

    return render_template(
        'admin/dashboard.html',
        pending=pending,
        approved=approved,
        stats=stats
    )


# ============================================================
# APROVAR / REJEITAR
# ============================================================
@admin_bp.route('/approve/<int:user_id>', methods=['POST'])
@admin_required
def approve_user(user_id):
    user = db.session.get(User, user_id)
    if not user:
        flash('Usuário não encontrado.', 'danger')
        return redirect(url_for('admin.dashboard'))

    if user.is_approved:
        flash(f'"{user.username}" já está aprovado.', 'info')
        return redirect(url_for('admin.dashboard'))

    user.is_approved = True
    user.approved_at = datetime.utcnow()
    user.approved_by_id = current_user.id
    db.session.commit()

    flash(f'✅ Usuário "{user.username}" aprovado!', 'success')
    return redirect(url_for('admin.dashboard'))


@admin_bp.route('/reject/<int:user_id>', methods=['POST'])
@admin_required
def reject_user(user_id):
    user = db.session.get(User, user_id)
    if not user:
        flash('Usuário não encontrado.', 'danger')
        return redirect(url_for('admin.dashboard'))

    if user.id == current_user.id:
        flash('Você não pode remover a si mesmo.', 'danger')
        return redirect(url_for('admin.dashboard'))

    if user.is_admin:
        flash('Remova primeiro a permissão de admin.', 'warning')
        return redirect(url_for('admin.dashboard'))

    username = user.username
    db.session.delete(user)
    db.session.commit()
    flash(f'❌ Usuário "{username}" removido.', 'info')
    return redirect(url_for('admin.dashboard'))


# ============================================================
# PROMOVER / REBAIXAR ADMIN
# ============================================================
@admin_bp.route('/toggle-admin/<int:user_id>', methods=['POST'])
@admin_required
def toggle_admin(user_id):
    user = db.session.get(User, user_id)
    if not user:
        flash('Usuário não encontrado.', 'danger')
        return redirect(url_for('admin.dashboard'))

    if user.id == current_user.id:
        flash('Você não pode alterar sua própria permissão.', 'danger')
        return redirect(url_for('admin.dashboard'))

    user.is_admin = not user.is_admin
    # Ao virar admin, garante aprovação também
    if user.is_admin:
        user.is_approved = True
        user.approved_at = datetime.utcnow()
        user.approved_by_id = current_user.id

    db.session.commit()

    estado = 'promovido a admin' if user.is_admin else 'rebaixado a usuário comum'
    flash(f'🔄 "{user.username}" {estado}.', 'success')
    return redirect(url_for('admin.dashboard'))