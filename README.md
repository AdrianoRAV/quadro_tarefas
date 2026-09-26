# quadro_tarefas
Quadro de Tarefas colaborativo com drag &amp; drop, múltiplos usuários online, autenticação, painel admin e exportação de relatórios (CSV/Excel/PDF).
# 🗂️ Quadro de Tarefa 

Um Quadro de Tarefan colaborativo inspirado no Trello, construído com **Flask**, **SQLAlchemy** e **SortableJS**. 
Suporta múltiplos usuários em tempo real, autenticação, painel administrativo e exportação de relatórios.

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.0-000000?style=flat&logo=flask&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-3-003B57?style=flat&logo=sqlite&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-green)

---

## ✨ Funcionalidades

### 🎯 Quadro Tarefas
- **4 colunas**: A Fazer, Fazendo, Concluído, Ajustes
- **Drag & drop** entre colunas (SortableJS)
- **Prioridade** por cores (Baixa, Média, Alta)
- **Responsável** e **criador** visíveis em cada card
- **Destaque visual** para tarefas atribuídas a você

### 👥 Colaboração
- Quadro **compartilhado** — todos os usuários veem todas as tarefas
- **Painel de usuários online** com heartbeat em tempo real (15s)
- **Auto-refresh** das tarefas a cada 30s
- Card mostra **quem criou** e **quem está fazendo**

### 🔐 Autenticação & Permissões
- Login/registro com senha criptografada (Werkzeug)
- **Primeiro usuário vira admin automaticamente**
- Novos cadastros ficam **pendentes de aprovação**
- **Painel admin** com estatísticas, aprovação e promoção de usuários

### 📊 Relatórios
- Dashboard com estatísticas por status, prioridade e responsável
- **Exportação em 3 formatos**:
  - 📄 **CSV** — abre no Excel/Sheets
  - 📊 **Excel (.xlsx)** — 3 abas formatadas com cores
  - 📕 **PDF** — documento profissional em paisagem A4

---

## 🖼️ Screenshots

> _(adicione prints do seu projeto aqui depois)_

| Quadro | Relatório | Painel Admin |
|---|---|---|
| ![board](docs/board.png) | ![report](docs/report.png) | ![admin](docs/admin.png) |

---

## 🚀 Começando

### Pré-requisitos
- Python 3.10+
- pip

### Instalação

```bash
# 1. Clone o repositório
git clone https://github.com/SEU_USUARIO/quadro_tarefas.git
cd quadro_tarefas

# 2. Crie um ambiente virtual
python -m venv venv

# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

# 3. Instale as dependências
pip install -r requirements.txt

# 4. (Opcional) Popule com usuários e tarefas de exemplo
python seed.py

# 5. Rode o app
python run.py
