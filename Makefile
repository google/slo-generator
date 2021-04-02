#!/usr/bin/make
# WARN: gmake syntax
########################################################
# Makefile for $(NAME)
#
# useful targets:
#	make clean -- clean distutils
#	make coverage_report -- code coverage report
#	make flake8 -- flake8 checks
#	make pylint -- source code checks
#	make tests -- run all of the tests
#	make unittest -- runs the unit tests
########################################################
# variable section

NAME = "slo_generator"

PIP=pip3

PYTHON=python3
TWINE=twine
COVERAGE=coverage
NOSE_OPTS = --with-coverage --cover-package=$(NAME) --cover-erase
SITELIB = $(shell $(PYTHON) -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")

VERSION := $(shell grep "version = " setup.py | cut -d\  -f3)

FLAKE8_IGNORE = E302,E203,E261

########################################################

all: clean install install_test test

info:
	@echo "slo-generator version: ${VERSION}"

flake8:
	flake8 --ignore=$(FLAKE8_IGNORE) $(NAME)/ --max-line-length=80
	flake8 --ignore=$(FLAKE8_IGNORE),E402 tests/ --max-line-length=80

pylint:
	find ./$(NAME) ./tests -name \*.py | xargs pylint --rcfile .pylintrc --ignore-patterns=test_.*?py

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
	$(PIP) install ."[api, datadog, prometheus, elasticsearch, pubsub, cloud_monitoring, bigquery]"

test: install flake8 pylint unittest

unittest: clean
	nosetests $(NOSE_OPTS) tests/unit/* -v

coverage_report:
	$(COVERAGE) report --rcfile=".coveragerc"

# Docker
docker_build:
	DOCKER_BUILDKIT=1
	docker build -t slo-generator:latest .

docker_test: docker_build
	docker run --entrypoint "make" \
		-e MIN_VALID_EVENTS=10 \
		-e GOOGLE_APPLICATION_CREDENTIALS=tests/unit/fixtures/fake_credentials.json \
		slo-generator test

# API 
run_api:
	functions-framework --source=slo_generator/api/main.py --target=run_compute --signature-type=cloudevent

docker_build_api:
	cd slo_generator/api && \
	pack build \
	--builder gcr.io/buildpacks/builder:v1 \
	--env GOOGLE_FUNCTION_SIGNATURE_TYPE=cloudevent \
	--env GOOGLE_FUNCTION_TARGET=run_compute \
	slo-generator-api

docker_push:
	gcloud auth configure-docker -q
	docker tag slo-generator-api gcr.io/${PROJECT_ID}/slo-generator-api:${VERSION}
	docker push gcr.io/${PROJECT_ID}/slo-generator-api

cloudbuild_api: 
	cd slo_generator/api && \
	gcloud alpha builds submit --pack image=gcr.io/${PROJECT_ID}/slo-generator-api:${VERSION},env=GOOGLE_FUNCTION_SIGNATURE_TYPE=cloudevent,env=GOOGLE_FUNCTION_TARGET=run_compute

deploy_api:
	gcloud run deploy --image gcr.io/${PROJECT_ID}/slo-generator-api:${VERSION} --platform managed --set-env-vars CONFIG_URL=${CONFIG_URL} --service-account=${SERVICE_ACCOUNT}
