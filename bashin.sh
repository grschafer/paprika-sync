#!/usr/bin/env bash
docker exec -it paprikasync_django_1 /bin/sh -c "export COLUMNS=`tput cols`; export LINES=`tput lines`; exec sh"
