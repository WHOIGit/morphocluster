#!/bin/bash

# Activate Python virtual environment (uv creates .venv in project root)
source /code/.venv/bin/activate

export FLASK_APP=morphocluster
export MORPHOCLUSTER_SETTINGS=config_docker.py

echo Waiting for Postgres...
./wait-for postgres:5432
# echo Waiting for Redis
# ./wait-for redis:6379

# Set working directory to project root where migrations folder is
cd /code
flask db upgrade

/usr/bin/supervisord --nodaemon -c /etc/supervisor/supervisord.conf