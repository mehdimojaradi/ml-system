#! /bin/bash

set -o errexit # Exit immediately if a command exits with a non-zero status. 
# Meaning that if any command fails, the script will stop executing and return an error.

set -o nounset # Treat unset variables as an error when substituting.
# Meaning that if the script tries to use a variable that has not been defined, it will exit with an error instead of using an empty string.

set -o pipefail # Return the exit status of the last command in the pipe that failed
# Meaning that if any command in a pipeline fails, the script will return the exit status of that command instead of the last command.

exec uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload 
# desc: Start the FastAPI application using Uvicorn with auto-reload enabled for development. 
# Meaning that the server will listen on all interfaces (0.0.0.0) and automatically reload when code changes are detected.