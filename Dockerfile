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

# FROM python:3.7-slim
# RUN apt-get update && \
#     apt-get install -y \
#     build-essential \
#     make \
#     gcc \
#     locales
# ADD . /app
# WORKDIR /app
# RUN pip install -U setuptools
# RUN pip install ."[api, datadog, dynatrace, prometheus, elasticsearch, pubsub, cloud_monitoring, cloud_service_monitoring, cloud_storage, bigquery, dev, prometheus_remote_write]"
# ENTRYPOINT [ "slo-generator" ]
# CMD ["-v"]

#ARG PYTHON_VERSION=3.11
ARG PYTHON_VERSION=3.7

FROM python:${PYTHON_VERSION}-alpine

ADD . /app
WORKDIR /app

COPY . ./

RUN apk add nginx
RUN apk add psmisc
RUN apk add bash
RUN apk add curl
RUN apk add vim
RUN apk add gcc
RUN apk add musl-dev
RUN apk add libc-dev

# ADD . /app
# WORKDIR /app

# COPY . ./

RUN pip install --upgrade pip
RUN pip install -U setuptools
RUN pip install ."[api, datadog, dynatrace, prometheus, elasticsearch, pubsub, cloud_monitoring, cloud_service_monitoring, cloud_storage, bigquery, dev, prometheus_remote_write]"
# RUN pip install --no-cache-dir ."[ \
#         api, \
#         prometheus, \
#         prometheus_remote_write \
#     ]"

ENTRYPOINT [ "slo-generator" ]

CMD [ "-v" ]


# RUN pip install --no-cache-dir ."[ \
#         api, \
#         bigquery, \
#         cloud_monitoring, \
#         cloud_service_monitoring, \
#         cloud_storage, \
#         cloudevent, \
#         datadog, \
#         dynatrace, \
#         elasticsearch, \
#         opensearch, \
#         prometheus, \
#         pubsub, \
#         splunk, \
#         prometheus_remote_write \
#     ]"

# ENTRYPOINT [ "slo-generator" ]


# FROM python:3.9-slim
# RUN apt-get update && \
#     apt-get install -y \
#     build-essential \
#     make \
#     gcc \
#     locales
# ADD . /app
# WORKDIR /app
# RUN pip install -U setuptools
# RUN pip install ."[api, datadog, dynatrace, prometheus, elasticsearch, pubsub, cloud_monitoring, cloud_service_monitoring, cloud_storage, bigquery, cloudevent, dev, prometheus_remote_write]"
# ENTRYPOINT [ "slo-generator" ]
# CMD ["-v"]
