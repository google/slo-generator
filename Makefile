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

NAME = "slo_generator"

PIP=pip3
PYTHON=python3
TWINE=twine
COVERAGE=coverage
NOSE_OPTS = --with-coverage --cover-package=$(NAME) --cover-erase --nologcapture --logging-level=ERROR
SITELIB = $(shell $(PYTHON) -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")

VERSION ?= $(shell grep "version = " setup.py | cut -d\  -f3)

OS := $(shell uname)


# W503 and W504 are mutually exclusive
FLAKE8_IGNORE = E302,E203,E261,W503

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

develop:
	$(PIP) install -e .

install: clean
	$(PIP) install -e ."[api, datadog, prometheus, elasticsearch, pubsub, cloud_monitoring, bigquery, dev, prometheus_remote_write]"
ifeq ($(OS),Darwin)
	@echo "running on MacOs, installing snappy headers with brew"
	brew install snappy
else
	@echo "running on Linux, assuming Ubuntu, installing snappy headers with apt"
	sudo apt install libsnappy-dev -y
endif


test: install unit lint

unit: clean
	nosetests $(NOSE_OPTS) tests/unit/* -v

coverage:
	$(COVERAGE) report --rcfile=".coveragerc"

lint: flake8 pylint

flake8:
	flake8 --ignore=$(FLAKE8_IGNORE) --exclude slo_generator/exporters/gen/ $(NAME)/ --max-line-length=80
	flake8 --ignore=$(FLAKE8_IGNORE),E402 tests/ --max-line-length=80

pylint:
	find ./$(NAME) ./tests -name \*.py | xargs pylint --rcfile .pylintrc --ignore-patterns=test_.*?py,.*_pb2.py

integration: int_cm int_csm int_custom int_dd int_dt int_es int_prom

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

# Run API locally
run_api:
	slo-generator api --target=run_compute --signature-type=http

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
	--allow-unauthenticated \
	--project=${CLOUDRUN_PROJECT_ID}

gcloud_alpha:
	gcloud components install alpha --quiet
