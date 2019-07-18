#!/usr/bin/env bash

# Install cronjobs on deploy in a idempotent way

# If you change cronjobs, you will likely need to manually remove the old version of the cronjob!
# If you change cronjobs, you will likely need to manually remove the old version of the cronjob!
# If you change cronjobs, you will likely need to manually remove the old version of the cronjob!
# TODO: Put marker ("cronjobs below here installed by script") and delete everything below there each deploy

# https://stackoverflow.com/a/3557165
FILE='/etc/crontab'
BOILERPLATE='/app/scripts/run_one_instance_at_a_time.sh docker-compose -f /app/production.yml run --rm django python -u manage.py'
JOB_IMPORT_NEW="* * * * * root $BOILERPLATE import_new_account_recipes >> /var/log/cronlogs/import_new_account_recipes.log 2>&1"
JOB_SYNC_REGULAR="7 * * * * root $BOILERPLATE sync_recipes_from_api >> /var/log/cronlogs/sync_recipes_from_api.log 2>&1"
JOB_SYNC_REQUESTED="* * * * * root $BOILERPLATE sync_recipes_from_api --requested >> /var/log/cronlogs/sync_recipes_from_api_for_requested_accounts.log 2>&1"
grep -qxF "$JOB_IMPORT_NEW" $FILE || echo "$JOB_IMPORT_NEW" >> $FILE
grep -qxF "$JOB_SYNC_REGULAR" $FILE || echo "$JOB_SYNC_REGULAR" >> $FILE
grep -qxF "$JOB_SYNC_REQUESTED" $FILE || echo "$JOB_SYNC_REQUESTED" >> $FILE
