
ARG PYTHON_VERSION=3.12.7

FROM python:${PYTHON_VERSION}-alpine as builder

ADD . /app
WORKDIR /app

#COPY . ./

RUN apk add psmisc
RUN apk add bash
RUN apk add curl
RUN apk add vim
RUN apk add gcc
RUN apk add musl-dev
RUN apk add libc-dev
RUN apk add make

RUN cd /app/slo_generator/exporters/gen && make generate

RUN pip install --upgrade pip
RUN pip install -U setuptools

RUN pip install --no-cache-dir ."[ \
        api, \
        prometheus, \
        prometheus_remote_write \
    ]"

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


FROM python:${PYTHON_VERSION}-alpine

RUN apk add bash
RUN apk add curl
RUN apk add vim

WORKDIR /

COPY --from=builder /usr/local /usr/local

ENTRYPOINT [ "slo-generator" ]

CMD [ "-v" ]