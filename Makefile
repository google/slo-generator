#!/usr/bin/env make
# WARN: gmake syntax
########################################################
# Makefile for $(NAME)
#
# useful targets:
#	make clean -- clean distutils
#	make coverage -- code coverage report
#	make test -- run linting + unit tests + audit CVEs
#	make lint -- run linting separately
#	make unit -- run unit tests separately
#	make audit -- run CVE scan separately
#	make integration -- run integration tests
########################################################

# Variables

NAME = slo_generator

HATCH = hatch
PIP = pip3
PYTHON = python3
COVERAGE = coverage

VERSION ?= $(shell grep "version = " pyproject.toml | cut -d ' ' -f 3)

########################################################

all: clean install test

##############

info:
	@echo "slo-generator version: ${VERSION}"

##############

clean:
	@echo "Cleaning up distutils stuff"
	rm -rf build
	rm -rf dist
	rm -rf MANIFEST
	rm -rf *.egg-info
	@echo "Cleaning up byte compiled python stuff"
	find . -type f -regex ".*\.py[co]$$" -delete
	@echo "Cleaning up doc builds"
	rm -rf docs/_build
	rm -rf docs/api_modules
	rm -rf docs/client_modules
	@echo "Cleaning up test reports"
	rm -rf report/*

##############

build: clean
	$(HATCH) build

deploy: build
	$(HATCH) publish

##############

#TODO: Replace with Hatch.
install: clean
#FIXME: Are all dependencies and features requested for all these targets?
	$(PIP) install -e ."[api, datadog, prometheus, elasticsearch, opensearch, splunk, pubsub, cloud_monitoring, bigquery, dev]"

uninstall: clean
	$(HATCH) env prune

##############

#TODO: How to handle pre-commit with Hatch environments? 
develop: install
	pre-commit install

##############

format:
	$(HATCH) fmt

##############

#FIXME: Are all dependencies and features requested for all these targets?
test: install unit lint audit

##############

unit: clean
	$(HATCH) run test:unit

coverage:
	$(HATCH) run test:cov

##############

lint: ruff pytype mypy

ruff:
	$(HATCH) fmt

pytype:
	$(HATCH) run lint:pytype

mypy:
	$(HATCH) run lint:mypy

##############

audit: bandit safety

audit: bandit safety

bandit:
	bandit -r $(NAME)

safety:
	# Ignore CVE-2018-20225 with Vulnerability ID 67599.
	# We do not use the `--extra-index-url` option, and the behavior is intended anyway.
	safety check --ignore 67599

##############

integration: int_cm int_csm int_custom int_dd int_dt int_es int_prom int_sp int_os

int_cm:
	slo-generator compute -f samples/cloud_monitoring -c samples/config.yaml

int_csm:
	slo-generator compute -f samples/cloud_service_monitoring -c samples/config.yaml

int_custom:
	slo-generator compute -f samples/custom -c samples/config.yaml

int_dd:
	slo-generator compute -f samples/datadog -c samples/config.yaml

int_dt:
	slo-generator compute -f samples/dynatrace -c samples/config.yaml

int_es:
	slo-generator compute -f samples/elasticsearch -c samples/config.yaml

int_prom:
	slo-generator compute -f samples/prometheus -c samples/config.yaml

int_sp:
	slo-generator compute -f samples/splunk -c samples/config.yaml

int_os:
	slo-generator compute -f samples/opensearch -c samples/config.yaml

##############

# Run API locally
run_api:
	slo-generator api --target=run_compute --signature-type=http -c samples/config.yaml

# Build Docker image locally
docker_build:
	DOCKER_BUILDKIT=1
	docker build \
		-t slo-generator:latest \
		--build-arg PYTHON_VERSION=3.9 \
		.

# Build Docker image with Cloud Build
cloud_build:
	gcloud builds submit \
		--config=cloudbuild.yaml \
		--project=${CLOUDBUILD_PROJECT_ID} \
		--substitutions=_GCR_PROJECT_ID=${GCR_PROJECT_ID},_VERSION=${VERSION}

# Cloud Run
cloud_run:
	gcloud run deploy slo-generator \
		--image gcr.io/${GCR_PROJECT_ID}/slo-generator:${VERSION} \
		--region=${REGION} \
		--platform managed \
		--set-env-vars CONFIG_PATH=${CONFIG_URL} \
		--service-account=${SERVICE_ACCOUNT} \
		--project=${CLOUDRUN_PROJECT_ID} \
		--command="slo-generator" \
		--args=api \
		--args=--signature-type="${SIGNATURE_TYPE}" \
		--min-instances 1 \
		--allow-unauthenticated

# Cloud Run - Export Mode Only
cloud_run_export_only:
	gcloud run deploy slo-generator-export \
		--image gcr.io/${GCR_PROJECT_ID}/slo-generator:${VERSION} \
		--region=${REGION} \
		--platform managed \
		--set-env-vars CONFIG_PATH=${CONFIG_URL} \
		--service-account=${SERVICE_ACCOUNT} \
		--project=${CLOUDRUN_PROJECT_ID} \
		--command="slo-generator" \
		--args=api \
		--args=--signature-type="cloudevent" \
		--args=--target="run_export" \
		--min-instances 1 \
		--allow-unauthenticated
