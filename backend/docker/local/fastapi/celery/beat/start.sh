#!/bin/bash

# this file serves as the entrypoint for the Celery beat container,
# ensuring that the Celery beat scheduler is started with the correct configuration.
# Celery beat is a scheduler that kicks off tasks at regular intervals, which are then executed by the Celery workers. 
# It is used for periodic task scheduling, such as running tasks every hour
# for example, to perform routine maintenance, send out notifications, or update data on a regular basis.

set -o errexit

set -o nounset

set -o pipefail

mkdir -p /tmp

exec watchfiles --filter python celery.__main__.main --args '-A backend.app.core.celery_app beat --scheduler=celery.beat.PersistentScheduler --schedule=/tmp/celerybeat-schedule -l INFO'
