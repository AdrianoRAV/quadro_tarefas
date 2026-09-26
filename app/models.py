from datetime import datetime, timedelta
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login_manager


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)

    # 🔑 Novos campos
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    is_approved = db.Column(db.Boolean, default=False, nullable=False)
    approved_at = db.Column(db.DateTime, nullable=True)
    approved_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    tasks = db.relationship(
        'Task',
        foreign_keys='Task.user_id',
        backref='owner',
        lazy=True,
        cascade='all, delete-orphan'
    )

    assigned_tasks = db.relationship(
        'Task',
        foreign_keys='Task.assignee_id',
        backref='assignee',
        lazy=True
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_online(self):
        if not self.last_seen:
            return False
        return (datetime.utcnow() - self.last_seen) < timedelta(seconds=60)

    def can_login(self):
        """Só entra quem está aprovado."""
        return self.is_approved


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


class Task(db.Model):
    __tablename__ = 'tasks'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, default='')
    status = db.Column(db.String(20), default='todo', nullable=False)
    priority = db.Column(db.String(20), default='media')
    position = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    assignee_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    def to_dict(self, current_user_id=None):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description or '',
            'status': self.status,
            'priority': self.priority,
            'position': self.position,
            'created_at': self.created_at.strftime('%d/%m/%Y %H:%M'),
            'updated_at': self.updated_at.strftime('%d/%m/%Y %H:%M') if self.updated_at else '',
            'completed_at': self.completed_at.strftime('%d/%m/%Y %H:%M') if self.completed_at else None,
            'user_id': self.user_id,
            'owner_name': self.owner.username if self.owner else '—',
            'assignee_id': self.assignee_id,
            'assignee_name': self.assignee.username if self.assignee else None,
            'is_mine': (current_user_id is not None and self.assignee_id == current_user_id),
            'is_created_by_me': (current_user_id is not None and self.user_id == current_user_id),
        }


class ActivityLog(db.Model):
    __tablename__ = 'activity_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'), nullable=True)
    action = db.Column(db.String(100), nullable=False)
    details = db.Column(db.String(255), default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)