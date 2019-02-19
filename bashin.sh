#!/usr/bin/env bash
docker exec -it paprikasync_django_1 /bin/sh -c "export COLUMNS=`tput cols`; export LINES=`tput lines`; exec sh"


# docker-compose -f local.yml run django pytest paprika_sync/core
# docker-compose -f local.yml run django python manage.py shell_plus
