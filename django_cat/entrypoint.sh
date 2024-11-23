#!/bin/sh

# entrypoint.sh

# Funzione per attendere il database
wait_for_db() {
    echo "Waiting for postgres..."
    while ! nc -z $SQL_HOST $SQL_PORT; do
        sleep 0.1
    done
    echo "PostgreSQL started"
}

# Funzione per eseguire le migrazioni
run_migrations() {
    python manage.py makemigrations
    python manage.py migrate
}


# Logica esistente per l'avvio dell'applicazione
if [ "$DATABASE" = "postgres" ]; then
    wait_for_db
fi

# Esegui le migrazioni
run_migrations

# Esegui il comando fornito
exec "$@"
