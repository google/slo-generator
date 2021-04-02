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
from os import environ
import logging
import pprint
from datetime import datetime

import yaml
from flask import jsonify

import google.cloud.storage
from slo_generator.compute import compute, export, get_exporters
from slo_generator.utils import setup_logging, parse_config

CONFIG_URL = environ['CONFIG_URL']
EXPORTERS_URL = environ.get('EXPORTERS_URL', None)
LOGGER = logging.getLogger(__name__)
TIME_FORMAT = '%Y-%m-%dT%H:%M:%SZ'
setup_logging()


def run_compute(cloudevent):
    # Get timestamp
    timestamp = int(
        datetime.strptime(cloudevent["time"], TIME_FORMAT).timestamp())

    # Get SLO config
    data = base64.b64decode(cloudevent.data).decode('utf-8')
    if 'config_url' in data:
        data = yaml.safe_load(data)
        slo_config_url = data['config_url']
        LOGGER.info(f'Downloading SLO config from {slo_config_url}')
        slo_config = parse_config(content=download_gcs(slo_config_url))
    else:
        slo_config = parse_config(content=data)

    # Get slo-generator config
    LOGGER.info(f'Downloading config from {CONFIG_URL}')
    config = parse_config(content=download_gcs(CONFIG_URL))

    # Compute SLO report
    LOGGER.debug(f'Config: {pprint.pformat(config)}')
    LOGGER.debug(f'SLO Config: {pprint.pformat(slo_config)}')
    reports = compute(slo_config,
                      config,
                      timestamp=timestamp,
                      client=None,
                      do_export=True)
    return jsonify(reports)


def run_export(cloudevent):
    # Get export data
    slo_report = yaml.safe_load(base64.b64decode(cloudevent.data))

    # Get SLO config
    LOGGER.info(f'Downloading SLO config from {CONFIG_URL}')
    config = parse_config(content=download_gcs(CONFIG_URL))

    # Get exporters list
    LOGGER.info(f'Downloading exporters config from {EXPORTERS_URL}')

    # Build exporters list
    if EXPORTERS_URL:
        exporters = parse_config(content=download_gcs(EXPORTERS_URL))
    else:
        exporters = slo_report['exporters']
    spec = {"exporters": exporters}
    exporters = get_exporters(config, spec)

    # Export data
    export(slo_report, exporters)


def decode_gcs_url(url):
    """Decode GCS URL.

    Args:
        url (str): GCS URL.

    Returns:
        tuple: (bucket_name, file_path)
    """
    split_url = url.split('/')
    bucket_name = split_url[2]
    file_path = '/'.join(split_url[3:])
    return (bucket_name, file_path)


def download_gcs(url):
    """Download config from GCS and load it with json module.

    Args:
        url: Config URL.

    Returns:
        dict: Loaded configuration.
    """
    storage_client = google.cloud.storage.Client()
    bucket, filepath = decode_gcs_url(url)
    bucket = storage_client.get_bucket(bucket)
    blob = bucket.blob(filepath)
    return blob.download_as_string(client=None).decode('utf-8')
