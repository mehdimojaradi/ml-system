#!/bin/bash

# this file serves as the entrypoint for the Celery worker container, 
# ensuring that any necessary cleanup tasks are performed before starting the worker process.
# worker is responsible for executing asynchronous tasks defined in the Celery app.
# asynchronous tasks are typically used for background processing, such as sending emails, processing data, or performing long-running computations.

set -o errexit

set -o nounset

set -o pipefail

# python -c "from backend.app.core.ml.cleanup import cleanup_mlflow_runs; cleanup_mlflow_runs()"

exec watchfiles --filter python celery.__main__.main --args '-A backend.app.core.celery_app worker -l INFO'
