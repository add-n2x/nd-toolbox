FROM python:3.13-slim

# Set version label
ARG BUILD_DATE
ARG VERSION
LABEL build_version="Navidrome Toolbox version:- ${VERSION} Build-date:- ${BUILD_DATE}"
LABEL maintainer="David Trattnig <david@subsquare.at>"

# Configure poetry
ENV POETRY_VERSION=1.8.5
ENV POETRY_HOME=/opt/poetry
ENV POETRY_VENV=/opt/poetry-venv
ENV POETRY_CACHE_DIR=/opt/.cache

# Setup poetry
RUN python3 -m venv $POETRY_VENV \
    && $POETRY_VENV/bin/pip install -U pip setuptools \
    && $POETRY_VENV/bin/pip install poetry==${POETRY_VERSION}
ENV PATH="${PATH}:${POETRY_VENV}/bin"

# Install dependencies
RUN echo "Installing dependencies..." && \
    apt-get update && apt-get -y install \
    apt-utils \
    build-essential \
    pip

# Add local files
RUN mkdir -p /app
COPY . /app/

# Linux Server conventions
RUN ln -s /app/config /config
RUN ln -s /app/music /music
RUN ln -s /app/data /data

# Init application
WORKDIR /app
RUN cp -n ./config/beets/sample-config.yaml ./config/beets/config.yaml
RUN poetry config virtualenvs.create false
RUN poetry install --no-interaction --no-ansi
ENTRYPOINT ["/bin/bash"]