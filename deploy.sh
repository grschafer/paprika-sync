#!/usr/bin/env bash
# References:
# - https://alexanderzeitler.com/articles/docker-machine-and-docker-compose-developer-workflows/
# - https://stackoverflow.com/questions/45090766/running-docker-compose-on-a-docker-machine

docker-machine ssh paprika-sync -- mkdir -p /app

# SCP too slow, copies everything (incl .git, venv)
# docker-machine scp -rd "$(pwd)/*" paprika-sync:/app/
rsync -avzhe "ssh -i $(docker-machine env paprika-sync | grep CERT | cut -d'=' -f2 | sed 's/"//g')/id_rsa -l root" --include=".envs/" --include=".envs/.production/" --include=".envs/.production/.*" --exclude=".*" --exclude="venv" --exclude="__pycache__" . $(docker-machine ip paprika-sync):/app
docker-machine ssh paprika-sync -- chown -R root:root /app

PLAT="$(docker-machine ssh paprika-sync -- uname -s)"
ARCH="$(docker-machine ssh paprika-sync -- uname -m)"
docker-machine ssh paprika-sync -- "which docker-compose || curl -L \"https://github.com/docker/compose/releases/download/1.24.0/docker-compose-$PLAT-$ARCH\" -o /usr/local/bin/docker-compose && chmod +x /usr/local/bin/docker-compose"

docker-machine ssh paprika-sync -- docker-compose -f /app/production.yml build
docker-machine ssh paprika-sync -- docker-compose -f /app/production.yml stop django
docker-machine ssh paprika-sync -- docker-compose -f /app/production.yml up -d

# TODO: set up supervisorctl
