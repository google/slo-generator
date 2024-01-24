#!/usr/bin/make
# WARN: gmake syntax
########################################################
# Makefile for $(NAME)
#
# useful targets:
#	make clean -- clean distutils
#	make coverage -- code coverage report
#	make test -- run lint + unit tests
#	make lint -- run lint tests separately
#	make unit -- runs unit tests separately
#   make integration -- runs integration tests
########################################################
# variable section

NAME = slo_generator

PIP = pip3
PYTHON = python3
TWINE = twine
COVERAGE = coverage
SITELIB = $(shell $(PYTHON) -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")

VERSION ?= $(shell grep "version = " setup.cfg | cut -d ' ' -f 3)

########################################################

all: clean install test

info:
	@echo "slo-generator version: ${VERSION}"

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

build: clean
	$(PYTHON) setup.py sdist bdist_wheel

deploy: clean install_twine build
	$(TWINE) upload dist/*

install_twine:
	$(PIP) install twine

develop: install
	pre-commit install

install: clean
	$(PIP) install -U setuptools pip
	$(PIP) install -e ."[api, datadog, prometheus, elasticsearch, opensearch, splunk, pubsub, cloud_monitoring, bigquery, dev]"

uninstall: clean
	$(PIP) freeze --exclude-editable | xargs $(PIP) uninstall -y

test: install unit lint

unit: clean
	pytest --cov=$(NAME) tests -p no:warnings

coverage:
	$(COVERAGE) report --rcfile=".coveragerc"

format:
	isort .
	black .

lint: black isort flake8 pylint pytype mypy bandit safety

black:
	black . --check

isort:
	isort . --check-only

flake8:
	flake8 $(NAME)/
	flake8 tests/

pylint:
	find ./$(NAME) ./tests -type f -name "*.py" | xargs pylint

pytype:
	pytype

mypy:
	mypy --show-error-codes $(NAME)

bandit:
	bandit .

safety:
	safety check

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

# Run API locally
run_api:
	slo-generator api --target=run_compute --signature-type=http -c samples/config.yaml

# Local Docker build / push
docker_build:
	DOCKER_BUILDKIT=1
	docker build -t slo-generator:latest .

docker_test: docker_build
	docker run --entrypoint "make" \
		-e GOOGLE_APPLICATION_CREDENTIALS=tests/unit/fixtures/fake_credentials.json \
		slo-generator test

# Cloudbuild
cloudbuild: gcloud_alpha
	gcloud alpha builds submit \
	--config=cloudbuild.yaml \
	--project=${CLOUDBUILD_PROJECT_ID} \
	--substitutions=_GCR_PROJECT_ID=${GCR_PROJECT_ID},_VERSION=${VERSION}

# Cloudrun
cloudrun:
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

# Cloudrun - export mode only
cloudrun_export_only:
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

gcloud_alpha:
	gcloud components install alpha --quiet
