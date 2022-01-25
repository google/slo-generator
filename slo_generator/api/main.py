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
from flask import jsonify, make_response

from slo_generator.compute import compute, export
from slo_generator.utils import setup_logging, load_config, get_exporters

CONFIG_PATH = os.environ['CONFIG_PATH']
EXPORTERS = os.environ.get('EXPORTERS', '').split(',')
LOGGER = logging.getLogger(__name__)
TIME_FORMAT = '%Y-%m-%dT%H:%M:%SZ'
API_SIGNATURE_TYPE = os.environ['GOOGLE_FUNCTION_SIGNATURE_TYPE']
setup_logging()

def process_req(request):
    """Process incoming request.

    Args:  
        request (cloudevent.CloudEvent, flask.Request): Request object.

    Returns:
        tuple: Tuple (data: dict, timestamp: int)
    """
    if API_SIGNATURE_TYPE == 'cloudevent':
        timestamp = int(
            datetime.strptime(request["time"], TIME_FORMAT).timestamp())
        data = base64.b64decode(request.data).decode('utf-8')
        LOGGER.info(f'Loading SLO config from Cloud Event "{request["id"]}"')
    elif API_SIGNATURE_TYPE == 'http':
        timestamp = None
        data = str(request.get_data().decode('utf-8'))
        LOGGER.info('Loading SLO config from HTTP request')
    return data, timestamp

def run_compute(request):
    """Run slo-generator compute function. Can be configured to export data as
    well, using the `exporters` key of the SLO config.

    Args:
        request (cloudevent.CloudEvent, flask.Request): Request object.

    Returns:
        list: List of SLO reports.
    """
    # Get SLO config
    data, timestamp = process_req(request)
    slo_config = load_config(data)

    # Get slo-generator config
    LOGGER.info(f'Loading slo-generator config from {CONFIG_PATH}')
    config = load_config(CONFIG_PATH)

    # Compute SLO report
    LOGGER.info(f'Config: {pprint.pformat(config)}')
    LOGGER.info(f'SLO Config: {pprint.pformat(slo_config)}')
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
    if request.method != 'POST':
        return make_response({
            "error": "Endpoint allows only POST requests"
        }, 500)

    # Get export data
    data, timestamp = process_req(request)
    slo_report = load_config(data)
    if not slo_report:
        return make_response({
            "error": "SLO report is empty."
        })

    # Get SLO config
    LOGGER.info(f'Loading slo-generator config from {CONFIG_PATH}')
    config = load_config(CONFIG_PATH)
    default_exporters = config.get('default_exporters', [])

    # Construct exporters block
    spec = {}
    if not default_exporters and not EXPORTERS:
        error = (
            'No default exporters set for `default_exporters` in shared config '
            f'at {CONFIG_PATH}; and --exporters was not passed to the CLI.'
        )
        return make_response({
            'error': error
        }, 500)
    elif not EXPORTERS:
        spec = {'exporters': EXPORTERS}
    else:
        spec = {'exporters': default_exporters}
    exporters = get_exporters(config, spec)

    # Export data
    errors = export(slo_report, exporters)
    name = slo_report['metadata']['name']
    step = slo_report['error_budget_policy_step_name']
    exporters_str = exporters.split(',')
    if errors:
        errors_str = errors.split(';')
        LOGGER.error(f"{name} | {step} | Export to {exporters_str} failed. | {errors_str}")
    else:
        LOGGER.info(f"{name} | {step} | Export to {exporters_str} successful.")

    if API_SIGNATURE_TYPE == 'http':
        return jsonify({
            "errors": errors
        })

    return errors
