# Set the Python version used by the base image.
ARG PYTHON_VERSION=3.13.1

# Create a reusable slim Python base image.
FROM python:${PYTHON_VERSION}-slim-bookworm AS python

# Stage 1: build dependency wheels
# Start the build stage from the shared Python base.
FROM python AS python-build-stage

# Install system packages needed to compile Python dependencies.
RUN apt-get update && apt-get install \
    # Avoid installing optional packages to keep image smaller. \
    --no-install-recommends -y \
    # Provide compiler toolchain for building Python deps. \
    build-essential \
    # Provide PostgreSQL client headers for psycopg builds. \
    libpq-dev 

# Copy Python dependency list into the build stage.
COPY ./backend/requirements.txt .

# Build wheel files for all Python dependencies.
RUN pip wheel --wheel-dir /usr/src/app/wheels \
    # Read dependencies from requirements file. \
    -r requirements.txt \
    # Do not keep pip cache in the image layer. \
    --no-cache-dir

# Stage 2: Python run stage
# Start the runtime stage from the shared Python base.
FROM python AS python-run-stage

# Define application home directory.
ARG APP_HOME=/src
# Define non-root user name.
ARG APP_USER=fastapi
# Define non-root group name.
ARG APP_GROUP=fastapi

# Prevent .pyc files and enable unbuffered logs.
# unbuffered logs are kind of logs that are written directly to the console without being buffered, 
# which can be helpful for real-time monitoring and debugging in containerized environments.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Set working directory inside the container.
WORKDIR ${APP_HOME}

# Install runtime tools, then clean apt cache to reduce image size.
RUN apt-get update && apt-get install --no-install-recommends -y \
    # Install common shell and debugging tools. \
    sudo git bash-completion vim ssh \
    # Install gettext utilities used by startup scripts. \
    # gettext utilities help with internationalization and localization.
    # Meaning they provide support for translating messages in different languages. \
    gettext \
    # Remove auto-installed packages not needed afterward. \
    && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
    # Delete apt package lists to shrink image size. \
    && rm -rf /var/lib/apt/lists/*

# Create a dedicated non-root group and user.
RUN groupadd -r ${APP_GROUP} && \
    # Create app user linked to app group and home directory. \
    useradd -r -g ${APP_GROUP} -d ${APP_HOME} -m ${APP_USER}

# Create log directory and set permissions for the app user.
RUN mkdir -p ${APP_HOME}/backend/app/logs && \
    # Set ownership so app user can write logs. \
    chown -R ${APP_USER}:${APP_GROUP} ${APP_HOME}/backend/app/logs && \
    # Keep directory writable by owner/group at runtime. \
    chmod 775 ${APP_HOME}/backend/app/logs

# Copy prebuilt dependency wheels from build stage.
COPY --from=python-build-stage /usr/src/app/wheels /wheels/

# Install dependencies from local wheels only, then remove wheels.
RUN pip install --no-cache-dir --no-index --find-links=/wheels/ /wheels/* \
    # Remove wheel artifacts after installation. \
    && rm -rf /wheels/

# Copy container entrypoint script.
COPY --chown=${APP_USER}:{APP_GROUP} ./backend/docker/local/fastapi/entrypoint.sh /entrypoint.sh
# Copy main app start script.
COPY --chown=${APP_USER}:{APP_GROUP} ./backend/docker/local/fastapi/start.sh /start.sh

# Normalize line endings and make scripts executable.
# for example, if the scripts were created on Windows, they might have CRLF line endings which can cause issues in Unix-based environments.
RUN sed -i 's/\r$//g' /entrypoint.sh /start.sh && \
    # Mark all startup scripts as executable. \
    chmod +x /entrypoint.sh /start.sh

# Copy application source code into the image.
COPY --chown=${APP_USER}:${APP_GROUP} . ${APP_HOME}

# Run container processes as non-root user.
# Running as a non-root user enhances security by limiting the permissions of processes inside the container, 
# reducing the risk of potential exploits or accidental damage to the host system.
USER ${APP_USER}

# Start container with the entrypoint script.
ENTRYPOINT [ "/entrypoint.sh" ]