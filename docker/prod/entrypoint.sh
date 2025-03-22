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

# Controlla se il comando è sphinx-autobuild
if [ "$1" = 'sphinx-autobuild' ]; then
    exec "$@"
else
    # Logica esistente per l'avvio dell'applicazione
    if [ "$DATABASE" = "postgres" ]; then
        wait_for_db
    fi

    # Esegui il comando fornito
    exec "$@"
fi