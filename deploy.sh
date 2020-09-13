#!/usr/bin/env bash
# References:
# - https://alexanderzeitler.com/articles/docker-machine-and-docker-compose-developer-workflows/
# - https://stackoverflow.com/questions/45090766/running-docker-compose-on-a-docker-machine

# Note that paprika-sync is set up in ~/.ssh/config to use correct keys and HostName
# Use ControlMaster/ControlPath/ControlPersist settings to multiplex ssh connections
# Host paprika_sync
#   User username
#   IdentityFile /path/to/identity/file
#   HostName ip-address-or-domain-name
#   ControlMaster auto
#   ControlPath ~/.ssh/%r@%h:%p
#   ControlPersist 10m


set -x

ssh paprika_sync -- mkdir -p /app

# SCP too slow, copies everything (incl .git, venv)
# scp -rd "$(pwd)/*" paprika_sync:/app/
# so, we use rsync
rsync -avzh --include=".envs/" --include=".envs/.production/" --include=".envs/.production/.*" --exclude=".*" --exclude="venv" --exclude="backups" --exclude="__pycache__" --exclude="tmp" . paprika_sync:/app
ssh paprika_sync -- chown -R root:root /app

# Install docker-compose if it's not installed already
PLAT="$(ssh paprika_sync -- uname -s)"
ARCH="$(ssh paprika_sync -- uname -m)"
ssh paprika_sync -- "which docker-compose || curl -L \"https://github.com/docker/compose/releases/download/1.24.0/docker-compose-$PLAT-$ARCH\" -o /usr/local/bin/docker-compose && chmod +x /usr/local/bin/docker-compose"

# Build image on remote machine
ssh paprika_sync -- docker-compose -f /app/production.yml build
# Make directories where cronjobs will store logs
ssh paprika_sync -- mkdir -p /var/log/cronlogs
# Add cronjobs to /etc/crontab
ssh paprika_sync -- bash /app/scripts/install_crontab.sh
# Logrotate cronjob logs
ssh paprika_sync -- cp -f /app/scripts/paprika-sync.logrotate /etc/logrotate.d/paprika-sync
# Add systemd service so paprika-sync starts on boot
ssh paprika_sync -- cp -f /app/scripts/paprika-sync.service /etc/systemd/system
# Reload systemd to see new paprika-sync service
ssh paprika_sync -- systemctl daemon-reload
# Enable starting paprika-sync on boot
ssh paprika_sync -- systemctl enable paprika-sync
# Restart paprika-sync (or start it if it's not running)
ssh paprika_sync -- systemctl restart paprika-sync
