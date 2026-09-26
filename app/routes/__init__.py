from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from sqlalchemy import text, inspect
from config import Config

db = SQLAlchemy()
login_manager = LoginManager()


def _auto_migrate(app):
    with app.app_context():
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()

        if 'users' in tables:
            existing = {c['name'] for c in inspector.get_columns('users')}
            with db.engine.begin() as conn:
                if 'last_seen' not in existing:
                    app.logger.warning('Auto-migração: users.last_seen')
                    conn.execute(text('ALTER TABLE users ADD COLUMN last_seen DATETIME'))

        if 'tasks' in tables:
            existing = {c['name'] for c in inspector.get_columns('tasks')}
            with db.engine.begin() as conn:
                if 'assignee_id' not in existing:
                    app.logger.warning('Auto-migração: tasks.assignee_id')
                    conn.execute(text(
                        'ALTER TABLE tasks ADD COLUMN assignee_id INTEGER REFERENCES users(id)'
                    ))


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Faça login para acessar.'
    login_manager.login_message_category = 'warning'

    from app.routes.auth import auth_bp
    from app.routes.main import main_bp
    from app.routes.api import api_bp
    from app.routes.reports import reports_bp          # <-- NOVO

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(reports_bp)                  # <-- NOVO

    with app.app_context():
        from app import models  # noqa: F401
        db.create_all()
        _auto_migrate(app)

    return app