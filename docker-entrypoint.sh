#!/bin/sh
# wait-for-postgres.sh

################################################################################
# An entrypoint script for DUCT which waits for the database to start, then    #
# runs migrations and then executes given startup command for a Docker service #
################################################################################

set -e

cmd="$@"

until PGPASSWORD=$POSTGRES_PASSWORD psql -h $POSTGRES_HOST -U $POSTGRES_USER -c '\q'; do
  >&2 echo "Postgres is unavailable - sleeping"
  sleep 1
done

>&2 echo "Running migrations . . ."
/usr/bin/python3.6 /src/ZOOM/manage.py migrate

>&2 echo "Postgres is up - executing command . . ."
exec $cmd
