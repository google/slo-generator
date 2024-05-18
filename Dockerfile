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

# As the SLO Generator is an installable package, let's build it locally then install it
# inside the Docker image. This way, the image behaves exactly like a user installation.
# As an added benefit, this method does not use any `COPY` statement for the source code
# itself before `pip install`. As a result, there is no need to write and maintain a
# `.dockerignore` file, and the image ends up as small as possible.
#
# Usage:
#   rye build --wheel --clean
#   docker build . --tag slo-generator:latest
#   docker run slo-generator
# Source:
#   https://rye-up.com/guide/docker/#container-from-a-python-package

# Define the default Python version used in production.
# This is usually the latest supported version at https://devguide.python.org/versions/.
# !! Make sure to propagate any new value to the `PYTHON_VERSION` variable in:
# GitHub > Settings > Secrets and variables > Actions > Variables > Repository variables
ARG PYTHON_VERSION=3.11

FROM python:${PYTHON_VERSION}-alpine

# For the next command to work, the `dist/` folder must NOT be in `.dockerignore`.
RUN --mount=source=dist,destination=/dist \
    PYTHONDONTWRITEBYTECODE=1 \
    pip install --no-cache-dir "$(dist/*.whl)[ \
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

ENTRYPOINT [ "slo-generator"]

CMD [ "-v"]
