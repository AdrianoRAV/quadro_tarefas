from datetime import datetime
from flask import Blueprint, render_template
from flask_login import login_required, current_user
from app import db
from app.models import Task

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
@login_required
def board():
    current_user.last_seen = datetime.utcnow()
    db.session.commit()

    # Quadro COMPARTILHADO: todos veem todas as tarefas
    tasks = Task.query.order_by(Task.position).all()

    columns = {
        'todo': [t for t in tasks if t.status == 'todo'],
        'doing': [t for t in tasks if t.status == 'doing'],
        'done': [t for t in tasks if t.status == 'done'],
        'adjust': [t for t in tasks if t.status == 'adjust'],
    }

    return render_template('board.html', columns=columns)


@main_bp.route('/report')
@login_required
def report():
    current_user.last_seen = datetime.utcnow()
    db.session.commit()

    tasks = Task.query.order_by(Task.created_at.desc()).all()

    total = len(tasks)
    by_status = {
        'todo': len([t for t in tasks if t.status == 'todo']),
        'doing': len([t for t in tasks if t.status == 'doing']),
        'done': len([t for t in tasks if t.status == 'done']),
        'adjust': len([t for t in tasks if t.status == 'adjust']),
    }
    by_priority = {
        'alta': len([t for t in tasks if t.priority == 'alta']),
        'media': len([t for t in tasks if t.priority == 'media']),
        'baixa': len([t for t in tasks if t.priority == 'baixa']),
    }

    grouped = {}
    for t in tasks:
        key = t.assignee.username if t.assignee else 'Sem responsável'
        if key not in grouped:
            grouped[key] = {'total': 0, 'todo': 0, 'doing': 0, 'done': 0, 'adjust': 0}
        grouped[key]['total'] += 1
        grouped[key][t.status] += 1

    creators = {}
    for t in tasks:
        key = t.owner.username if t.owner else '—'
        creators[key] = creators.get(key, 0) + 1

    return render_template(
        'report.html',
        total=total,
        by_status=by_status,
        by_priority=by_priority,
        grouped=grouped,
        creators=creators,
        tasks=tasks
    )