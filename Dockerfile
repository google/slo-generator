# Copyright 2019 Google LLC

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Define the default Python version used in production.
# This is usually the most recent supported version at https://devguide.python.org/versions/.
# !! Make sure to propagate any new value to the `PYTHON_VERSION` variable in:
# GitHub > Settings > Secrets and variables > Actions > Variables > Repository variables
ARG PYTHON_VERSION=3.11

FROM python:${PYTHON_VERSION}-alpine

WORKDIR /app

COPY . ./

RUN pip install --no-cache-dir ."[ \
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
