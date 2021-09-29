# Copyright 2021 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#            http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
`main.py`
Functions Framework API (Flask).
See https://github.com/GoogleCloudPlatform/functions-framework-python for
details on the Functions Framework.
"""
import base64
import os
import logging
import pprint

from datetime import datetime
from flask import jsonify

import yaml

from slo_generator.compute import compute, export
from slo_generator.utils import setup_logging, load_config, get_exporters

CONFIG_PATH = os.environ['CONFIG_PATH']
EXPORTERS_PATH = os.environ.get('EXPORTERS_PATH', None)
LOGGER = logging.getLogger(__name__)
TIME_FORMAT = '%Y-%m-%dT%H:%M:%SZ'
API_SIGNATURE_TYPE = os.environ['GOOGLE_FUNCTION_SIGNATURE_TYPE']
setup_logging()


def run_compute(request):
    """Run slo-generator compute function. Can be configured to export data as
    well, using the `exporters` key of the SLO config.

    Args:
        request (cloudevent.CloudEvent, flask.Request): Request object.

    Returns:
        list: List of SLO reports.
    """
    # Get SLO config
    if API_SIGNATURE_TYPE == 'http':
        timestamp = None
        data = str(request.get_data().decode('utf-8'))
        LOGGER.info('Loading SLO config from Flask request')
    elif API_SIGNATURE_TYPE == 'cloudevent':
        timestamp = int(
            datetime.strptime(request["time"], TIME_FORMAT).timestamp())
        data = base64.b64decode(request.data).decode('utf-8')
        LOGGER.info(f'Loading SLO config from Cloud Event "{request["id"]}"')
    slo_config = load_config(data)

    # Get slo-generator config
    LOGGER.info(f'Loading slo-generator config from {CONFIG_PATH}')
    config = load_config(CONFIG_PATH)

    # Compute SLO report
    LOGGER.debug(f'Config: {pprint.pformat(config)}')
    LOGGER.debug(f'SLO Config: {pprint.pformat(slo_config)}')
    reports = compute(slo_config,
                      config,
                      timestamp=timestamp,
                      client=None,
                      do_export=True)
    if API_SIGNATURE_TYPE == 'http':
        reports = jsonify(reports)
    return reports


def run_export(request):
    """Run slo-generator export function. Get the SLO report data from a request
    object.

    Args:
        request (cloudevent.CloudEvent, flask.Request): Request object.

    Returns:
        list: List of SLO reports.
    """
    # Get export data
    if API_SIGNATURE_TYPE == 'http':
        slo_report = request.get_json()
    elif API_SIGNATURE_TYPE == 'cloudevent':
        slo_report = yaml.safe_load(base64.b64decode(request.data))

    # Get SLO config
    LOGGER.info(f'Downloading SLO config from {CONFIG_PATH}')
    config = load_config(CONFIG_PATH)

    # Build exporters list
    if EXPORTERS_PATH:
        LOGGER.info(f'Loading exporters from {EXPORTERS_PATH}')
        exporters = load_config(EXPORTERS_PATH)
    else:
        LOGGER.info(f'Loading exporters from SLO report data {EXPORTERS_PATH}')
        exporters = slo_report['exporters']
    spec = {"exporters": exporters}
    exporters = get_exporters(config, spec)

    # Export data
    export(slo_report, exporters)
