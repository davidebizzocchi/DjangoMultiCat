# DjangoCat 😺

Integrating CheshireCat in Django

> [!IMPORTANT]
>
> - **Agent Provider**: [Cheshire Cat AI](https://github.com/cheshire-cat-ai/core)  
>   The core framework for building conversational AI agents.
>
> - **Plugin**: [MultiCat](https://github.com/davidebizzocchi/multicat)  
>   Enables efficient communication with the Cheshire Cat AI framework.
>

**Django integration for the Cheshire Cat AI framework**

A Django project integrating the [Cheshire Cat AI](https://github.com/cheshire-cat-ai/core) framework with built-in support for:

- Qdrant vector database
- [MultiCat](https://github.com/davidebizzocchi/multicat) plugin (pre-installed)
- Dockerized development environment
- Managment for libraries (vectorstore), files and chats

## 🚀 Features

- Full Docker integration (Compose files included)
- Pre-configured Qdrant vector memory
- Version management system
- Development tools with Makefile
- Sample environment configuration
- Integrated CI/CD-ready versioning

### Built-in Supports

- 🐱 Cheshire Cat AI Framework
- 📦 Qdrant Vector Database
- 🤖 MultiCat Plugin (pre-installed)
- 📚 **Vectorstore Management** (libraries, files, and chat history)
- 🐳 Dockerized Environment
- 🔄 Version Control System

### 📚 Data Management

- 📚 Library/Collection organization
- 📁 File upload & document processing
- 💬 Chat history persistence
- 🔍 Vector similarity search
- 🗂️ Metadata tagging system

## ⚙️ Prerequisites

- Docker & Docker Compose
- Python 3.11+
- UV package manager (`pip install uv`)
- Make (optional but recommended)

## 🛠️ Installation

### 1. Environment Setup

```sh
# Clone repository
git clone https://github.com/yourusername/djangocat.git
cd djangocat

# Copy environment template
cp env-sample/.env env/.env
```

Edit `env/.env` with your configuration:

```ini
# Minimum required settings
SECRET_KEY='your-django-secret-key'
DEBUG=1
SQL_DATABASE=mydatabase
SQL_USER=myuser
SQL_PASSWORD="mypassword"
```

### 2. Virtual Environment

```sh
# Create and activate virtual environment
uv venv
source .venv/bin/activate  # Linux/macOS

# Install dependencies
make requirements
```

### 3. Start Services

```sh
# Start Docker containers
make up-local

# Verify containers
docker ps
```

## 🐳 Docker Management

| Command               | Description                                  |
|-----------------------|----------------------------------------------|
| `make up-local`       | Start containers with local config          |
| `make upd`            | Start containers in background              |
| `make down`           | Stop and remove containers                  |
| `make shell-bash`     | Access Django container shell               |
| `make shell-django`   | Open Django management shell                |
| `make django-log`     | View Django container logs                  |

## 🔄 Cheshire Cat Configuration

Configure in `env/.env`:

```ini
CCAT_CORE_HOST=cheshire-cat-core
CCAT_CORE_PORT=1865
CCAT_QDRANT_HOST=cheshire-cat-vector-memory
CCAT_QDRANT_PORT=6333
```

## 🌐 Web Interface

After starting containers, access:

- Django: <http://localhost:8000>
- Cheshire Cat Admin: <http://localhost:1865/admin>

## Utilities

- `make git-sync-branches` - Synchronize local branches with remote

## 🔧 Troubleshooting

**Common Issues:**

1. **Docker not starting**:
   - Ensure Docker Desktop is running
   - Check `docker ps` works in terminal

2. **Migration conflicts**:

```sh
make remove-all
docker exec django_cat-app-1 python manage.py migrate
```

3. **Missing dependencies**:

```sh
make requirements
make build-local-cat
```

## 🗄️ Database Operations

> ⚠️ **Warning**: The following commands are potentially destructive and irreversible!

- `make remove-migrations` - Remove all migration files
  > Deletes all Django migrations. Development use only.

- `make destroy-database` - Delete local database
  > Completely removes the Docker database volume. All data will be lost.

- `make remove-all` - Remove migrations and database
  > ⚠️ **DANGER**: Executes both operations above. Use only for complete environment resets.

## 📦 Version Management

| Command             | Description                      |
|---------------------|----------------------------------|
| `make bump-patch`   | Increment patch version (0.0.X)  |
| `make bump-minor`   | Increment minor version (0.X.0)  |
| `make bump-major`   | Increment major version (X.0.0)  |
| `make release`      | Create new production release    |
