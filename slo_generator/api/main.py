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

from flask import jsonify, make_response

from slo_generator.compute import compute, export
from slo_generator.utils import setup_logging, load_config, get_exporters

CONFIG_PATH = os.environ['CONFIG_PATH']
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
    data = process_req(request)
    slo_config = load_config(data)

    # Get slo-generator config
    LOGGER.info(f'Loading slo-generator config from {CONFIG_PATH}')
    config = load_config(CONFIG_PATH)

    # Compute SLO report
    LOGGER.debug(f'Config: {pprint.pformat(config)}')
    LOGGER.debug(f'SLO Config: {pprint.pformat(slo_config)}')
    reports = compute(slo_config,
                      config,
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
    data = process_req(request)
    slo_report = load_config(data)
    if not slo_report:
        return make_response({
            "error": "SLO report is empty."
        })

    # Get SLO config
    LOGGER.info(f'Loading slo-generator config from {CONFIG_PATH}')
    config = load_config(CONFIG_PATH)

    # Construct exporters block
    spec = {}
    default_exporters = config.get('default_exporters', [])
    cli_exporters = os.environ.get('EXPORTERS', None)
    if cli_exporters:
        cli_exporters = cli_exporters.split(',')
    if not default_exporters and not cli_exporters:
        error = (
            'No default exporters set for `default_exporters` in shared config '
            f'at {CONFIG_PATH}; and --exporters was not passed to the CLI.'
        )
        return make_response({
            'error': error
        }, 500)
    if cli_exporters:
        spec = {'exporters': cli_exporters}
    else:
        spec = {'exporters': default_exporters}
    exporters = get_exporters(config, spec)

    # Export data
    errors = export(slo_report, exporters)
    if API_SIGNATURE_TYPE == 'http':
        return jsonify({
            "errors": errors
        })

    return errors

def process_req(request):
    """Process incoming request.

    Args:
        request (cloudevent.CloudEvent, flask.Request): Request object.

    Returns:
        str: Message content.
    """
    if API_SIGNATURE_TYPE == 'cloudevent':
        cloudevent = request
        if 'message' in cloudevent.data: # PubSub enveloppe
            content = base64.b64decode(cloudevent.data['message']['data'])
            data = str(content.decode('utf-8'))
        else:
            data = str(cloudevent.data)
        LOGGER.info(f'Loading config from Cloud Event "{cloudevent["id"]}"')
    elif API_SIGNATURE_TYPE == 'http':
        data = str(request.get_data().decode('utf-8'))
        LOGGER.info('Loading config from HTTP request')
    return data
