#!/bin/bash

# SSH setup removed - not needed for production

# Activate Python virtual environment
source /opt/venv/bin/activate

export FLASK_APP=morphocluster.server

echo Waiting for Postgres...
./wait-for postgres:5432
# echo Waiting for Redis
# ./wait-for redis:6379

flask db upgrade

/usr/bin/supervisord --nodaemon -c /etc/supervisor/supervisord.conf