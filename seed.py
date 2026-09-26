"""
Cria usuários de teste e aprova todos + admin.
    python seed.py
"""
from datetime import datetime
from app import create_app, db
from app.models import User, Task

app = create_app()

USERS = [
    {'username': 'admin', 'email': 'admin@local.com', 'password': 'admin123',
     'is_admin': True,  'is_approved': True},
    {'username': 'joao',  'email': 'joao@local.com',  'password': 'joao123',
     'is_admin': False, 'is_approved': True},
    {'username': 'maria', 'email': 'maria@local.com', 'password': 'maria123',
     'is_admin': False, 'is_approved': True},
    {'username': 'pedro', 'email': 'pedro@local.com', 'password': 'pedro123',
     'is_admin': False, 'is_approved': False},   # fica pendente pra você testar
]

TASKS = [
    {'title': 'Configurar servidor',  'description': 'Instalar ambiente',
     'status': 'todo',   'priority': 'alta',  'assignee': 'admin'},
    {'title': 'Criar layout do site', 'description': 'HTML/CSS base',
     'status': 'doing',  'priority': 'media', 'assignee': 'joao'},
    {'title': 'Revisar documentação', 'description': 'Conferir textos',
     'status': 'adjust', 'priority': 'baixa', 'assignee': 'maria'},
    {'title': 'Deploy inicial',       'description': 'Publicar v1.0',
     'status': 'done',   'priority': 'alta',  'assignee': 'admin'},
]


def run():
    with app.app_context():
        created = {}
        for u in USERS:
            existing = User.query.filter_by(username=u['username']).first()
            if existing:
                # Garante que admin esteja como admin e aprovado
                if u['is_admin']:
                    existing.is_admin = True
                    existing.is_approved = True
                    if not existing.approved_at:
                        existing.approved_at = datetime.utcnow()
                print(f"ℹ️  '{u['username']}' já existe.")
                created[u['username']] = existing
                continue

            user = User(
                username=u['username'],
                email=u['email'],
                is_admin=u['is_admin'],
                is_approved=u['is_approved'],
            )
            if u['is_approved']:
                user.approved_at = datetime.utcnow()
            user.set_password(u['password'])
            db.session.add(user)
            db.session.flush()

            tag = 'ADMIN' if u['is_admin'] else ('pendente' if not u['is_approved'] else 'aprovado')
            print(f"✅ '{u['username']}' criado [{tag}] (senha: {u['password']})")
            created[u['username']] = user

        db.session.commit()

        if Task.query.count() == 0:
            admin = created['admin']
            for idx, t in enumerate(TASKS):
                assignee = created.get(t['assignee'])
                db.session.add(Task(
                    title=t['title'], description=t['description'],
                    status=t['status'], priority=t['priority'], position=idx,
                    user_id=admin.id,
                    assignee_id=assignee.id if assignee else None,
                ))
            db.session.commit()
            print(f"✅ {len(TASKS)} tarefas criadas.")

        print("\n🎉 Login:")
        for u in USERS:
            status = 'ADMIN' if u['is_admin'] else ('PENDENTE' if not u['is_approved'] else 'aprovado')
            print(f"   - {u['username']:8s} / {u['password']:10s} [{status}]")


if __name__ == '__main__':
    run()