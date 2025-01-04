# DjangoCat

Integrating CheshireCat in Django

## First Setup

### 1. Virtual Environment

1. Create a new virtual environment:

   ```sh
   uv venv
   ```

2. Activate the virtual environment:
   - On macOS/Linux:

     ```sh
     source .venv/bin/activate
     ```

   - On Windows:

     ```sh
     .\.venv\Scripts\activate
     ```

3. Install dependencies:

   ```sh
   make requirements
   ```

### 2. Django Configuration

1. Start Docker containers:

   ```sh
   make up-local
   ```

2. Open a bash shell in Django container:

   ```sh
   make shell-bash
   ```

3. Open Django shell:

   ```sh
   make shell-django
   ```

## Main Commands

### Environment Management

- `make requirements` - Update and install dependencies

### Docker and Development

- `make up-local` - Start containers in local environment
- `make shell-bash` - Open a bash shell in Django container
- `make shell-django` - Open Django shell to interact with the application
- `make django-log` - View Django container logs

### Database and Migrations

> ⚠️ **Warning**: The following commands are potentially destructive and irreversible!

- `make remove-migrations` - Remove all migration files
  > Deletes all Django migrations. Development use only.

- `make destroy-database` - Delete local database
  > Completely removes the Docker database volume. All data will be lost.

- `make remove-all` - Remove migrations and database
  > ⚠️ **DANGER**: Executes both operations above. Use only for complete environment resets.

### Versioning and Release

- `make bump-patch` - Increment patch version (x.x.X)
- `make bump-minor` - Increment minor version (x.X.0)
- `make bump-major` - Increment major version (X.0.0)
- `make release` - Execute a complete new release

### Utilities

- `make git-sync-branches` - Synchronize local branches with remote
- `make up-ngrok` - Start ngrok tunnel on port 8000
