#!/usr/bin/env bash

# Locking approach: https://unix.stackexchange.com/a/22047

cmd=$@
# Make lockfile in /var/tmp with name of the django management command + options
lockfile=/var/tmp/$(echo $cmd | sed -r 's/(python3?|manage.py)\s//g' | sed -r 's/[^A-Za-z0-9._-]/_/g')

if ( set -o noclobber; echo "$$" > "$lockfile") 2> /dev/null; then

        trap 'rm -f "$lockfile"; exit $?' INT TERM EXIT

        # do stuff here
        exec $cmd

        # clean up after yourself, and release your trap
        rm -f "$lockfile"
        trap - INT TERM EXIT
else
        echo "Lock Exists: $lockfile owned by $(cat $lockfile)"
fi
