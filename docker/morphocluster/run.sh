#!/bin/bash

# Handle authorized_keys - create empty file if directory doesn't exist
if [ -f /authorized_keys ]; then
    cp /authorized_keys /root/.ssh/authorized_keys
    chmod 600 /root/.ssh/authorized_keys
else
    touch /root/.ssh/authorized_keys
    chmod 600 /root/.ssh/authorized_keys
fi

# Activate Python virtual environment
source /opt/venv/bin/activate

export FLASK_APP=morphocluster
export MORPHOCLUSTER_SETTINGS=config_docker.py

echo Waiting for Postgres...
./wait-for postgres:5432
# echo Waiting for Redis
# ./wait-for redis:6379

flask db upgrade

/usr/bin/supervisord --nodaemon -c /etc/supervisor/supervisord.conf