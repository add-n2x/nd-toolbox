FROM python:3.13-alpine

# Set version label
ARG BUILD_DATE
ARG VERSION
LABEL build_version="Navidrome Toolbox version:- ${VERSION} Build-date:- ${BUILD_DATE}"
LABEL maintainer="David Trattnig <david@subsquare.at>"

#
# APP CONFIGURATION
#

ENV TZ=Vienna/Europe
ENV LOG_LEVEL=INFO
ENV DRY_RUN=true

# This is used by Beets and Navidrome.
# Files with these extensions will be removed from the music directory. 
ENV UNSUPPORTED_EXTENSIONS="m4p mp4 mp2"
# Local directory where the music files are stored. 
ENV MUSIC_DIR=/music
# Folder to access logs and other processing data
ENV DATA_DIR=/data
# Beets configuration directory. 
ENV BEETSDIR=/app/config/beets
# Beets library base path. 
ENV BEETS_BASE_PATH=/music
# Point to the configuration dir for Navidrome. 
# This directory should contain the navidrome.db 
ENV ND_DIR=/navidrome
# Base path of the music library in the Navidrome database.
# If you run Navidrom with Docker, it's the path inside the container.
ENV ND_BASE_PATH=/music/library

# Volumes
VOLUME /app/config/beets
VOLUME /app/data

# Install dependencies
RUN echo "Installing dependencies..." && \
    apk add --no-cache make
    # apk add --update

# Configure Poetry
ENV POETRY_VERSION=1.8.5
ENV POETRY_HOME=/opt/poetry
ENV POETRY_VENV=/opt/poetry-venv
ENV POETRY_CACHE_DIR=/opt/.cache

# Setup Poetry
RUN python3 -m venv $POETRY_VENV \
    && $POETRY_VENV/bin/pip install -U pip setuptools \
    && $POETRY_VENV/bin/pip install poetry==${POETRY_VERSION}
ENV PATH="${PATH}:${POETRY_VENV}/bin"

# Add local files
RUN mkdir -p /app /config /music /data \
    && chown -R 1000:1000 /app /config /music /data
COPY . /app/

# Init application
WORKDIR /app
RUN cp .env.docker .env
RUN cp -n ./config/beets/docker.config.yaml ./config/beets/config.yaml
RUN poetry config virtualenvs.create false
RUN poetry install --no-interaction --no-ansi
ENTRYPOINT ["/bin/bash"]