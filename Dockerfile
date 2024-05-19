# Copyright 2024 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# As the SLO Generator is an installable package, let's build it then install it in a
# multi-stage Docker image. This way, the image has a small size and behaves exactly
# like a user installation.
#
# Usage:
#   docker build . --tag slo-generator:latest --build-arg PYTHON_VERSION=$(cat .python-version)
#   docker run slo-generator:latest
#
# References:
# - https://rye-up.com/guide/docker/#container-from-a-python-package
# - https://testdriven.io/blog/docker-best-practices/
# - https://rye-up.com/guide/publish/#build
# - https://sogo.dev/posts/2023/11/rye-with-docker

# Define the default Python version used in production.
# This is usually the latest supported version at https://devguide.python.org/versions/.
# When using `rye`, it is usually set to the contents of `.python-version`, for example
# with `docker build --build-arg PYTHON_VERSION=$(cat .python-version) <...>`.
# !! Make sure to propagate any new value to the `PYTHON_VERSION` variable in:
# GitHub > Settings > Secrets and variables > Actions > Variables > Repository variables
# FIXME Reuse the contents of `.python-version` in CI too, for a single source of truth.
ARG PYTHON_VERSION

FROM python:${PYTHON_VERSION}-slim-bookworm AS wheel_builder

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
        curl \
        make \
        build-essential \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

# Run container processes with a non-root user.
RUN useradd wheel --create-home
USER wheel
WORKDIR /home/wheel/app

# Install Rye.
ENV RYE_HOME /home/wheel/.rye
ENV PATH ${RYE_HOME}/shims:${PATH}
RUN curl -sSf https://rye-up.com/get | RYE_NO_AUTO_INSTALL=1 RYE_INSTALL_OPTION="--yes" bash

# Leverage Docker's caching by only copying the minimum files required for `rye sync`.
COPY --chown=wheel:wheel \
     pyproject.toml \
     requirements.lock \
     requirements-dev.lock \
     .python-version \
     README.md \
     Makefile \
     ./

# Prevent Python from writing `.pyc` files.
ENV PYTHONDONTWRITEBYTECODE=1
# Keep Python from buffering `stdout` and `stderr` to avoid situations where the
# application crashes without emitting any logs due to buffering.
ENV PYTHONUNBUFFERED=1

# Install dependencies in virtual environment (except dev dependencies).
RUN make install_nodev

# Copy the remaining files.
COPY --chown=wheel:wheel src ./src

# Build the wheel target in `./dist/`.
RUN make build_wheel

###########################################################

FROM python:${PYTHON_VERSION}-alpine

# Run container processes with a non-root user.
RUN adduser -D app
USER app
WORKDIR /home/app

COPY --from=wheel_builder \
     /home/wheel/app/dist/slo_generator-*-py3-none-any.whl \
     .

# Preemptively add `~/.local/bin` to PATH to avoid warnings during `pip install --user`.
ENV PATH /home/app/.local/bin:${PATH}

RUN PYTHONDONTWRITEBYTECODE=1 \
    pip install \
    --user \
    --no-cache-dir \
    "$(ls slo_generator-*-py3-none-any.whl)[ \
        api, \
        bigquery, \
        cloud_monitoring, \
        cloud_service_monitoring, \
        cloud_storage, \
        cloudevent, \
        datadog, \
        dynatrace, \
        elasticsearch, \
        opensearch, \
        prometheus, \
        pubsub, \
        splunk \
    ]"

ENTRYPOINT [ "slo-generator" ]

CMD [ "-v" ]
