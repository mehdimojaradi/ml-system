#!/bin/bash
# This file serves as the entrypoint for the FastAPI application container, 
# ensuring that PostgreSQL is ready before starting the app.
# Exit immediately if any command returns a non-zero status.
set -o errexit

# Treat use of undefined variables as an error.
set -o nounset

# Make pipelines fail if any command in the pipeline fails.
set -o pipefail

# Run inline Python to wait until PostgreSQL is reachable.
python <<END
# Used to write retry and error messages to stderr.
import sys
# Used for timeout and retry interval timing.
import time
# PostgreSQL client used for connectivity checks.
import psycopg

# Maximum total seconds to wait for PostgreSQL.
MAX_WAIT_SECONDS = 30
# Seconds to sleep between connection attempts.
RETRY_INTERVAL = 5
# Timestamp used to measure elapsed wait time.
start_time = time.time()

# Try connecting to PostgreSQL and report whether it is ready.
def check_database():
	try:
		# Attempt a connection using environment-provided DB settings.
		psycopg.connect(
			dbname="${POSTGRES_DB}",
			user="${POSTGRES_USER}",
			password="${POSTGRES_PASSWORD}",
			host="${POSTGRES_HOST}",
			port="${POSTGRES_PORT}",
		)
		# Connection succeeded.
		return True
	except psycopg.OperationalError as error:
		# Log connection failure with elapsed wait time.
		elapsed = int(time.time() - start_time)
		sys.stderr.write(f"Database connection attempt failed after {elapsed} seconds: {error}\n")
		# Connection failed; caller should retry.
		return False

# Retry until database is available or timeout is reached.
while True:
	# Exit loop as soon as a connection succeeds.
	if check_database():
		break

	# Stop waiting and fail startup after timeout.
	if time.time() - start_time > MAX_WAIT_SECONDS:
		sys.stderr.write("Error: Database connection could not be established after 30 seconds\n")
		# Exit with error code so the container startup fails clearly.
		sys.exit(1)

	# Emit retry message and pause before next attempt.
	sys.stderr.write(f"Waiting {RETRY_INTERVAL} seconds before retrying...\n")
	time.sleep(RETRY_INTERVAL)
END


# Inform logs that PostgreSQL is ready.
echo >&2 'PostgreSQL is ready to accept connections'

# Apply all pending Alembic migrations.
# alembic upgrade head

# Replace shell with the final command provided by container runtime.
# it allows the container to run the specified command (like starting the FastAPI server) 
# while ensuring that the entrypoint script has completed its tasks (like waiting for the database and applying migrations) 
# before handing control over to the main application process.
exec "$@"
