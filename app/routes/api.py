from datetime import datetime, timedelta
from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from app import db
from app.models import Task, ActivityLog, User

api_bp = Blueprint('api', __name__)


def log_activity(user_id, task_id, action, details=''):
    log = ActivityLog(user_id=user_id, task_id=task_id, action=action, details=details)
    db.session.add(log)


def touch_user():
    current_user.last_seen = datetime.utcnow()
    db.session.commit()


# ============================================================
# PRESENÇA / USUÁRIOS
# ============================================================

@api_bp.route('/me', methods=['GET'])
@login_required
def me():
    touch_user()
    return jsonify({'id': current_user.id, 'username': current_user.username})


@api_bp.route('/users', methods=['GET'])
@login_required
def list_users():
    touch_user()
    users = User.query.order_by(User.username).all()
    return jsonify([{'id': u.id, 'username': u.username} for u in users])


@api_bp.route('/online', methods=['GET'])
@login_required
def online_users():
    touch_user()

    cutoff = datetime.utcnow() - timedelta(seconds=60)
    online = User.query.filter(User.last_seen >= cutoff)\
                       .order_by(User.username).all()

    return jsonify({
        'online': [
            {
                'id': u.id,
                'username': u.username,
                'is_me': u.id == current_user.id,
            }
            for u in online
        ],
        'count': len(online),
        'server_time': datetime.utcnow().strftime('%H:%M:%S'),
    })


# ============================================================
# TAREFAS (COMPARTILHADAS)
# ============================================================

@api_bp.route('/tasks', methods=['GET'])
@login_required
def list_tasks():
    tasks = Task.query.order_by(Task.status, Task.position).all()
    return jsonify([t.to_dict(current_user_id=current_user.id) for t in tasks])


@api_bp.route('/tasks', methods=['POST'])
@login_required
def create_task():
    data = request.get_json() or {}
    title = (data.get('title') or '').strip()

    if not title:
        return jsonify({'error': 'Título é obrigatório'}), 400

    status = data.get('status', 'todo')
    if status not in ('todo', 'doing', 'done', 'adjust'):
        status = 'todo'

    last = Task.query.filter_by(status=status)\
                     .order_by(Task.position.desc()).first()
    position = (last.position + 1) if last else 0

    assignee_id = data.get('assignee_id')
    if assignee_id:
        try:
            assignee_id = int(assignee_id)
            if not db.session.get(User, assignee_id):
                assignee_id = None
        except (ValueError, TypeError):
            assignee_id = None

    task = Task(
        title=title,
        description=data.get('description', '') or '',
        status=status,
        priority=data.get('priority', 'media') or 'media',
        position=position,
        user_id=current_user.id,
        assignee_id=assignee_id
    )
    db.session.add(task)
    db.session.flush()
    log_activity(current_user.id, task.id, 'criada', f'Tarefa "{title}" criada')
    db.session.commit()

    return jsonify(task.to_dict(current_user_id=current_user.id)), 201


@api_bp.route('/tasks/<int:task_id>', methods=['PUT'])
@login_required
def update_task(task_id):
    task = db.session.get(Task, task_id)
    if not task:
        return jsonify({'error': 'Tarefa não encontrada'}), 404

    data = request.get_json() or {}
    old_status = task.status

    if 'title' in data:
        new_title = (data['title'] or '').strip()
        if new_title:
            task.title = new_title
    if 'description' in data:
        task.description = data['description'] or ''
    if 'priority' in data:
        task.priority = data['priority'] or 'media'
    if 'assignee_id' in data:
        aid = data['assignee_id']
        if aid:
            try:
                aid = int(aid)
                task.assignee_id = aid if db.session.get(User, aid) else None
            except (ValueError, TypeError):
                task.assignee_id = None
        else:
            task.assignee_id = None
    if 'status' in data:
        new_status = data['status']
        if new_status in ('todo', 'doing', 'done', 'adjust'):
            task.status = new_status
            if task.status == 'done' and old_status != 'done':
                task.completed_at = datetime.utcnow()
            elif task.status != 'done':
                task.completed_at = None

    task.updated_at = datetime.utcnow()

    if old_status != task.status:
        log_activity(current_user.id, task.id, 'movida',
                     f'De "{old_status}" para "{task.status}"')
    else:
        log_activity(current_user.id, task.id, 'editada', '')

    db.session.commit()
    return jsonify(task.to_dict(current_user_id=current_user.id))


@api_bp.route('/tasks/<int:task_id>', methods=['DELETE'])
@login_required
def delete_task(task_id):
    task = db.session.get(Task, task_id)
    if not task:
        return jsonify({'error': 'Tarefa não encontrada'}), 404

    log_activity(current_user.id, None, 'excluida', f'Tarefa "{task.title}" excluída')
    db.session.delete(task)
    db.session.commit()
    return jsonify({'success': True})


@api_bp.route('/tasks/reorder', methods=['POST'])
@login_required
def reorder_tasks():
    data = request.get_json() or {}
    task_id = data.get('task_id')
    new_status = data.get('status')
    new_position = data.get('position', 0)

    if new_status not in ('todo', 'doing', 'done', 'adjust'):
        return jsonify({'error': 'Status inválido'}), 400

    task = db.session.get(Task, task_id)
    if not task:
        return jsonify({'error': 'Tarefa não encontrada'}), 404

    old_status = task.status
    task.status = new_status
    task.position = new_position
    task.updated_at = datetime.utcnow()

    if new_status == 'done' and old_status != 'done':
        task.completed_at = datetime.utcnow()
    elif new_status != 'done':
        task.completed_at = None

    if old_status != new_status:
        log_activity(current_user.id, task.id, 'movida',
                     f'De "{old_status}" para "{new_status}"')

    db.session.commit()
    return jsonify(task.to_dict(current_user_id=current_user.id))