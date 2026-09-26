document.addEventListener('DOMContentLoaded', () => {
    const STATUSES = ['todo', 'doing', 'done', 'adjust'];
    const HEARTBEAT_MS = 15000;      // atualiza presença a cada 15s
    const TASKS_REFRESH_MS = 30000;  // recarrega tarefas a cada 30s

    // ============================================
    // 1. CARREGA USUÁRIOS PARA OS SELECTS
    // ============================================
    async function loadUsers() {
        try {
            const res = await fetch('/api/users');
            if (!res.ok) return;
            const users = await res.json();

            const options = users.map(u =>
                `<option value="${u.id}">${u.username}</option>`
            ).join('');

            const selectNew = document.getElementById('new-assignee');
            const selectEdit = document.getElementById('edit-assignee');

            if (selectNew) selectNew.innerHTML = '<option value="">— Sem responsável —</option>' + options;
            if (selectEdit) selectEdit.innerHTML = '<option value="">— Sem responsável —</option>' + options;
        } catch (err) {
            console.error('Erro ao carregar usuários:', err);
        }
    }
    loadUsers();

    // ============================================
    // 2. USUÁRIOS ONLINE (heartbeat)
    // ============================================
    async function refreshOnline() {
        try {
            const res = await fetch('/api/online');
            if (!res.ok) return;
            const data = await res.json();

            const countEl = document.getElementById('online-count');
            const timeEl = document.getElementById('server-time');
            const list = document.getElementById('online-list');

            if (countEl) countEl.textContent = data.count;
            if (timeEl) timeEl.textContent = data.server_time;
            if (!list) return;

            if (data.online.length === 0) {
                list.innerHTML = '<li class="list-group-item text-muted small text-center">Ninguém online</li>';
                return;
            }

            list.innerHTML = data.online.map(u => `
                <li class="list-group-item d-flex align-items-center gap-2 py-2">
                    <span class="online-dot"></span>
                    <span class="${u.is_me ? 'fw-bold text-success' : ''}">
                        ${escapeHtml(u.username)}
                        ${u.is_me ? '<small>(você)</small>' : ''}
                    </span>
                </li>
            `).join('');
        } catch (err) {
            console.error('Erro ao buscar online:', err);
        }
    }
    refreshOnline();
    setInterval(refreshOnline, HEARTBEAT_MS);

    // ============================================
    // 3. DRAG & DROP
    // ============================================
    const columns = document.querySelectorAll('.kanban-column-body');
    columns.forEach(col => {
        new Sortable(col, {
            group: 'kanban',
            animation: 150,
            ghostClass: 'sortable-ghost',
            onEnd: async (evt) => {
                const taskId = evt.item.dataset.id;
                const newStatus = evt.to.dataset.status;
                const newPosition = evt.newIndex;
                const oldStatus = evt.from.dataset.status;

                updateCounts();

                if (oldStatus === newStatus && evt.oldIndex === evt.newIndex) return;

                try {
                    const res = await fetch('/api/tasks/reorder', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            task_id: parseInt(taskId),
                            status: newStatus,
                            position: newPosition
                        })
                    });
                    if (!res.ok) throw new Error('Falha ao mover');
                    showToast('Tarefa movida!', 'success');
                } catch (err) {
                    console.error(err);
                    showToast('Erro ao mover tarefa', 'danger');
                    location.reload();
                }
            }
        });
    });

    function updateCounts() {
        STATUSES.forEach(status => {
            const col = document.getElementById(`col-${status}`);
            const counter = document.getElementById(`count-${status}`);
            if (!col || !counter) return;
            counter.textContent = col.querySelectorAll('.task-card').length;
        });
    }

    // ============================================
    // 4. RENDERIZA CARD (após criar/editar)
    // ============================================
    function renderTaskCard(task) {
        const priorityClass = task.priority === 'alta' ? 'danger' :
                              task.priority === 'media' ? 'warning text-dark' : 'info text-dark';

        const assigneeHtml = task.assignee_name
            ? `<span class="badge ${task.is_mine ? 'bg-success' : 'bg-primary-subtle text-primary-emphasis border border-primary-subtle'}">
                   <i class="bi bi-person-fill"></i>
                   ${escapeHtml(task.assignee_name)}
                   ${task.is_mine ? '(você)' : ''}
               </span>`
            : `<span class="badge bg-light text-muted border">
                   <i class="bi bi-person-dash"></i> Sem responsável
               </span>`;

        const descHtml = task.description
            ? `<div class="task-desc">${escapeHtml(task.description)}</div>`
            : '';

        const mineClass = task.is_mine ? 'task-mine' : '';

        return `
            <div class="task-card ${mineClass}" data-id="${task.id}" data-priority="${task.priority}">
                <div class="task-header">
                    <span class="badge bg-${priorityClass} badge-sm">${capitalize(task.priority)}</span>
                    <button type="button" class="btn btn-sm btn-link p-0 edit-btn" data-id="${task.id}">
                        <i class="bi bi-pencil"></i>
                    </button>
                </div>
                <div class="task-title">${escapeHtml(task.title)}</div>
                ${descHtml}
                <div class="task-assignee mt-2">${assigneeHtml}</div>
                <div class="task-footer">
                    <small class="text-muted">
                        <i class="bi bi-person-plus"></i> criado por
                        <strong>${escapeHtml(task.owner_name)}</strong>
                        ${task.is_created_by_me ? '(você)' : ''}
                    </small>
                    <br>
                    <small class="text-muted">
                        <i class="bi bi-clock"></i> ${task.created_at}
                    </small>
                </div>
            </div>
        `;
    }

    // ============================================
    // 5. CRIAR TAREFA
    // ============================================
    const btnCreate = document.getElementById('btn-create-task');
    if (btnCreate) {
        btnCreate.addEventListener('click', async () => {
            const title = document.getElementById('new-title').value.trim();
            const description = document.getElementById('new-description').value.trim();
            const priority = document.getElementById('new-priority').value;
            const status = document.getElementById('new-status').value;
            const assigneeRaw = document.getElementById('new-assignee').value;
            const assignee_id = assigneeRaw ? parseInt(assigneeRaw) : null;

            if (!title) {
                showToast('Digite um título', 'warning');
                return;
            }

            try {
                const res = await fetch('/api/tasks', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ title, description, priority, status, assignee_id })
                });
                if (!res.ok) throw new Error('Erro ao criar');
                const task = await res.json();

                const col = document.getElementById(`col-${task.status}`);
                col.insertAdjacentHTML('beforeend', renderTaskCard(task));
                updateCounts();
                bindEditButtons();

                document.getElementById('new-title').value = '';
                document.getElementById('new-description').value = '';
                document.getElementById('new-assignee').value = '';

                const modalEl = document.getElementById('newTaskModal');
                const modal = bootstrap.Modal.getInstance(modalEl) || new bootstrap.Modal(modalEl);
                modal.hide();

                showToast('Tarefa criada!', 'success');
            } catch (err) {
                console.error(err);
                showToast('Erro ao criar tarefa', 'danger');
            }
        });
    }

    // ============================================
    // 6. EDITAR / EXCLUIR
    // ============================================
    let editModalInstance = null;
    function getEditModal() {
        if (!editModalInstance) {
            editModalInstance = new bootstrap.Modal(document.getElementById('editTaskModal'));
        }
        return editModalInstance;
    }

    async function openEditModal(id) {
        try {
            const res = await fetch('/api/tasks');
            const tasks = await res.json();
            const task = tasks.find(t => t.id == id);
            if (!task) {
                showToast('Tarefa não encontrada', 'danger');
                return;
            }

            document.getElementById('edit-id').value = task.id;
            document.getElementById('edit-title').value = task.title;
            document.getElementById('edit-description').value = task.description || '';
            document.getElementById('edit-priority').value = task.priority;
            document.getElementById('edit-assignee').value = task.assignee_id || '';

            getEditModal().show();
        } catch (err) {
            console.error(err);
            showToast('Erro ao abrir tarefa', 'danger');
        }
    }

    function bindEditButtons() {
        document.querySelectorAll('.edit-btn').forEach(btn => {
            btn.onclick = (e) => {
                e.preventDefault();
                e.stopPropagation();
                openEditModal(btn.dataset.id);
            };
        });
    }
    bindEditButtons();

    // Salvar edição
    const btnSave = document.getElementById('btn-save-task');
    if (btnSave) {
        btnSave.addEventListener('click', async () => {
            const id = document.getElementById('edit-id').value;
            const title = document.getElementById('edit-title').value.trim();
            const description = document.getElementById('edit-description').value.trim();
            const priority = document.getElementById('edit-priority').value;
            const assigneeRaw = document.getElementById('edit-assignee').value;
            const assignee_id = assigneeRaw ? parseInt(assigneeRaw) : null;

            if (!title) {
                showToast('Título não pode ser vazio', 'warning');
                return;
            }

            try {
                const res = await fetch(`/api/tasks/${id}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ title, description, priority, assignee_id })
                });
                if (!res.ok) throw new Error('Erro ao atualizar');
                const task = await res.json();

                const card = document.querySelector(`.task-card[data-id="${id}"]`);
                if (card) card.outerHTML = renderTaskCard(task);
                bindEditButtons();

                getEditModal().hide();
                showToast('Tarefa atualizada!', 'success');
            } catch (err) {
                console.error(err);
                showToast('Erro ao atualizar', 'danger');
            }
        });
    }

    // Excluir
    const btnDelete = document.getElementById('btn-delete-task');
    if (btnDelete) {
        btnDelete.addEventListener('click', async () => {
            const id = document.getElementById('edit-id').value;
            if (!confirm('Tem certeza que deseja excluir esta tarefa?')) return;

            try {
                const res = await fetch(`/api/tasks/${id}`, { method: 'DELETE' });
                if (!res.ok) throw new Error('Erro ao excluir');

                const card = document.querySelector(`.task-card[data-id="${id}"]`);
                if (card) card.remove();

                updateCounts();
                getEditModal().hide();
                showToast('Tarefa excluída!', 'success');
            } catch (err) {
                console.error(err);
                showToast('Erro ao excluir', 'danger');
            }
        });
    }

    // ============================================
    // 7. AUTO-REFRESH DAS TAREFAS (opcional, mantém o quadro sincronizado)
    // ============================================
    async function refreshTasks() {
        try {
            const res = await fetch('/api/tasks');
            if (!res.ok) return;
            const tasks = await res.json();

            // Remove cards que não existem mais
            const ids = new Set(tasks.map(t => String(t.id)));
            document.querySelectorAll('.task-card').forEach(card => {
                if (!ids.has(card.dataset.id)) card.remove();
            });

            // Atualiza/adiciona cards existentes
            tasks.forEach(task => {
                const existing = document.querySelector(`.task-card[data-id="${task.id}"]`);
                if (existing) {
                    const currentCol = existing.closest('.kanban-column-body')?.dataset.status;
                    if (currentCol !== task.status) {
                        // Moveu em outro lugar (outro usuário moveu) -> move no DOM
                        const newCol = document.getElementById(`col-${task.status}`);
                        if (newCol) newCol.appendChild(existing);
                    }
                } else {
                    const col = document.getElementById(`col-${task.status}`);
                    if (col) col.insertAdjacentHTML('beforeend', renderTaskCard(task));
                }
            });

            updateCounts();
            bindEditButtons();
        } catch (err) {
            console.error('Erro ao atualizar tarefas:', err);
        }
    }
    setInterval(refreshTasks, TASKS_REFRESH_MS);

    // ============================================
    // 8. HELPERS
    // ============================================
    function capitalize(s) {
        if (!s) return '';
        return s.charAt(0).toUpperCase() + s.slice(1);
    }

    function escapeHtml(text) {
        if (text == null) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    function showToast(msg, type) {
        const toast = document.createElement('div');
        toast.className = `alert alert-${type} position-fixed top-0 end-0 m-3 shadow`;
        toast.style.zIndex = '9999';
        toast.textContent = msg;
        document.body.appendChild(toast);
        setTimeout(() => toast.remove(), 2500);
    }
});