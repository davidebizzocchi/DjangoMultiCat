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


# Logica esistente per l'avvio dell'applicazione
# if [ "$DATABASE" = "postgres" ]; then
#     wait_for_db
# fi
echo "Waiting for postgres..."
sleep 2.0
echo "PostgreSQL started"
# Esegui il comando fornito
exec "$@"