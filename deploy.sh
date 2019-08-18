#!/usr/bin/env bash
# References:
# - https://alexanderzeitler.com/articles/docker-machine-and-docker-compose-developer-workflows/
# - https://stackoverflow.com/questions/45090766/running-docker-compose-on-a-docker-machine

docker-machine ssh paprika-sync -- mkdir -p /app

# SCP too slow, copies everything (incl .git, venv)
# docker-machine scp -rd "$(pwd)/*" paprika-sync:/app/
# so, we use rsync
rsync -avzhe "ssh -i $(docker-machine env paprika-sync | grep CERT | cut -d'=' -f2 | sed 's/"//g')/id_rsa -l root" --include=".envs/" --include=".envs/.production/" --include=".envs/.production/.*" --exclude=".*" --exclude="venv" --exclude="backups" --exclude="__pycache__" --exclude="tmp" . $(docker-machine ip paprika-sync):/app
docker-machine ssh paprika-sync -- chown -R root:root /app

# Install docker-compose if it's not installed already
PLAT="$(docker-machine ssh paprika-sync -- uname -s)"
ARCH="$(docker-machine ssh paprika-sync -- uname -m)"
docker-machine ssh paprika-sync -- "which docker-compose || curl -L \"https://github.com/docker/compose/releases/download/1.24.0/docker-compose-$PLAT-$ARCH\" -o /usr/local/bin/docker-compose && chmod +x /usr/local/bin/docker-compose"

# Build image on remote machine
docker-machine ssh paprika-sync -- docker-compose -f /app/production.yml build
# Make directories where cronjobs will store logs
docker-machine ssh paprika-sync -- mkdir -p /var/log/cronlogs
# Add cronjobs to /etc/crontab
docker-machine ssh paprika-sync -- bash /app/scripts/install_crontab.sh
# Logrotate cronjob logs
docker-machine ssh paprika-sync -- cp -f /app/scripts/paprika-sync.logrotate /etc/logrotate.d/paprika-sync
# Add systemd service so paprika-sync starts on boot
docker-machine ssh paprika-sync -- cp -f /app/scripts/paprika-sync.service /etc/systemd/system
# Reload systemd to see new paprika-sync service
docker-machine ssh paprika-sync -- systemctl daemon-reload
# Enable starting paprika-sync on boot
docker-machine ssh paprika-sync -- systemctl enable paprika-sync
# Restart paprika-sync (or start it if it's not running)
docker-machine ssh paprika-sync -- systemctl restart paprika-sync
