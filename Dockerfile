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

ARG PYTHON_VERSION

FROM python:${PYTHON_VERSION}-slim

WORKDIR /app

COPY . ./

# TODO: Is `dev` required if we decide not to run tests from the Docker image?
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
