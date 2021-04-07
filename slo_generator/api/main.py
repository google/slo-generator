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

import yaml

try:
    import google.cloud.storage  # pylint: disable=import-error
except ImportError:
    pass

from slo_generator.compute import compute, export, get_exporters
from slo_generator.utils import setup_logging, load_config

CONFIG_PATH = os.environ['CONFIG_PATH']
EXPORTERS_URL = os.environ.get('EXPORTERS_URL', None)
LOGGER = logging.getLogger(__name__)
TIME_FORMAT = '%Y-%m-%dT%H:%M:%SZ'
setup_logging()


def run_compute(cloudevent):
    """Run slo-generator compute function. Can be configured to export data as
    well, using the `exporters` key of the SLO config.

    Args:
        cloudevent (cloudevent.CloudEvent): Cloud event object.

    Returns:
        list: List of SLO reports.
    """
    # Get timestamp
    timestamp = int(
        datetime.strptime(cloudevent["time"], TIME_FORMAT).timestamp())

    # Get SLO config
    data = base64.b64decode(cloudevent.data).decode('utf-8')
    LOGGER.info(f'Loading SLO config from Cloud Event {cloudevent["id"]}')
    slo_config = load_config(data)

    # Get slo-generator config
    LOGGER.info(f'Loading slo-generator config from {CONFIG_PATH}')
    config = load_config(CONFIG_PATH)

    # Compute SLO report
    LOGGER.debug(f'Config: {pprint.pformat(config)}')
    LOGGER.debug(f'SLO Config: {pprint.pformat(slo_config)}')
    compute(slo_config,
            config,
            timestamp=timestamp,
            client=None,
            do_export=True)


def run_export(cloudevent):
    """Run slo-generator export function. Get the SLO report data from a Cloud
    Event object.

    Args:
        cloudevent (cloudevent.CloudEvent): Cloud event object.

    Returns:
        list: List of SLO reports.
    """
    # Get export data
    slo_report = yaml.safe_load(base64.b64decode(cloudevent.data))

    # Get SLO config
    LOGGER.info(f'Downloading SLO config from {CONFIG_PATH}')
    config = load_config(CONFIG_PATH)

    # Build exporters list
    if EXPORTERS_URL:
        LOGGER.info(f'Loading exporters from {EXPORTERS_URL}')
        exporters = load_config(EXPORTERS_URL)
    else:
        LOGGER.info(f'Loading exporters from SLO report data {EXPORTERS_URL}')
        exporters = slo_report['exporters']
    spec = {"exporters": exporters}
    exporters = get_exporters(config, spec)

    # Export data
    export(slo_report, exporters)
