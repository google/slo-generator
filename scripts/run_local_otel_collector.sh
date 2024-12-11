#!/usr/bin/env bash
set -x
set -eo pipefail

# If an OpenTelemetry Collector container is already running, kill it.
RUNNING_OTEL_COLLECTOR_CONTAINER=$(docker ps --filter 'name=otel_collector' --format '{{.ID}}')
if [[ -n ${RUNNING_OTEL_COLLECTOR_CONTAINER} ]]; then
    docker kill "${RUNNING_OTEL_COLLECTOR_CONTAINER}"
fi

# Run the OpenTelemetry Collector in a new container.
# The `--mount` and `--env` options mount the local Default Application Credentials fetched after
# `gcloud auth login --update-adc` to ensure the OpenTelemetry Collector is able to authenticate to
# GCP from inside the Docker container. The `--user` option overrides the ID of the default user
# running the processes inside the container, to ensure `/etc/gcp/creds.json` is readable. Otherwise
# the default user of the Docker almost certainly has a different ID than the local user on the
# Docker host, and `~/.config/gcloud/application_default_credentials.json` can only be read by the
# current local user (600 permissions = rw-------). Finally, the `OTEL_BACKEND_PROJECT_ID` environment
# variable, used in `config.yaml`, tells the OpenTelemetry Collector which GCP project to export to.
# Define it prior to running this script, for example in `.env`, next to the other variables.
# Published ports:
#   - 4317 = gRPC
#   - 4318 = HTTP
docker run \
    --mount type=bind,source=${HOME}/.config/gcloud/application_default_credentials.json,target=/etc/gcp/creds.json,readonly \
    --env GOOGLE_APPLICATION_CREDENTIALS=/etc/gcp/creds.json \
    --user $(id --user) \
    --mount type=bind,source=$(pwd)/traces.yaml,target=/etc/otelcol-contrib/config.yaml,readonly \
    --env OTEL_BACKEND_PROJECT_ID \
    --publish 4317:4317 \
    --publish 4318:4318 \
    --name "otel_collector_$(date '+%s')" \
    --detach \
    otel/opentelemetry-collector-contrib

# Configure the SLO Generator to send traces to the OpenTelemetry Collector...
export SEND_TRACES_TO_OTLP_EXPORTER=1

# ... and tail the OpenTelemetry Collector logs.
docker logs --follow $(docker ps --filter 'name=otel_collector' --format '{{.ID}}')
