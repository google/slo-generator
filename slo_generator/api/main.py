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
import json
import logging
import os
import pprint

import requests
from flask import jsonify, make_response

from slo_generator.compute import compute, export
from slo_generator.utils import get_exporters, load_config, setup_logging

CONFIG_PATH = os.environ["CONFIG_PATH"]
LOGGER = logging.getLogger(__name__)
TIME_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
API_SIGNATURE_TYPE = os.environ["GOOGLE_FUNCTION_SIGNATURE_TYPE"]
setup_logging()


def run_compute(request):
    """Run slo-generator compute function. Can be configured to export data as
    well, using the `exporters` key of the SLO config.

    Args:
        request (cloudevent.CloudEvent, flask.Request): Request object.

    Returns:
        list: List of SLO reports.
    """
    # Get slo-generator config
    LOGGER.info(f"Loading slo-generator config from {CONFIG_PATH}")
    config = load_config(CONFIG_PATH)

    # Process request
    data = process_req(request)
    batch_mode = request.args.get("batch", False)
    if batch_mode:
        if not API_SIGNATURE_TYPE == "http":
            raise ValueError(
                'Batch mode works only when --signature-type is set to "http".'
            )
        process_batch_req(request, data, config)
        return jsonify([])

    # Load SLO config
    slo_config = load_config(data)

    # Compute SLO report
    LOGGER.debug(f"Config: {pprint.pformat(config)}")
    LOGGER.debug(f"SLO Config: {pprint.pformat(slo_config)}")
    reports = compute(
        slo_config,
        config,
        client=None,
        do_export=True,
    )
    if API_SIGNATURE_TYPE == "http":
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
        return make_response(
            {
                "error": "SLO report is empty.",
            }
        )

    # Get SLO config
    LOGGER.info(f"Loading slo-generator config from {CONFIG_PATH}")
    config = load_config(CONFIG_PATH)

    # Construct exporters block
    spec = {}
    # pytype: disable=attribute-error
    # pylint: disable=fixme
    # FIXME `load_config()` returns `Optional[dict]` so `config` can be `None`
    default_exporters = config.get("default_exporters", [])
    # pytype: enable=attribute-error
    cli_exporters = os.environ.get("EXPORTERS", None)
    if cli_exporters:
        cli_exporters = cli_exporters.split(",")
    if not default_exporters and not cli_exporters:
        error = (
            "No default exporters set for `default_exporters` in shared config "
            f"at {CONFIG_PATH}; and --exporters was not passed to the CLI."
        )
        return make_response(
            {
                "error": error,
            },
            500,
        )
    if cli_exporters:
        spec = {"exporters": cli_exporters}
    else:
        spec = {"exporters": default_exporters}
    exporters = get_exporters(config, spec)

    # Export data
    errors = export(slo_report, exporters)
    if API_SIGNATURE_TYPE == "http":
        return jsonify(
            {
                "errors": errors,
            }
        )

    return errors


def process_req(request):
    """Process incoming request.

    Args:
        request (cloudevent.CloudEvent, flask.Request): Request object.

    Returns:
        str: Message content.
    """
    if API_SIGNATURE_TYPE == "cloudevent":
        LOGGER.info(f'Loading config from Cloud Event "{request["id"]}"')
        if "message" in request.data:  # PubSub enveloppe
            LOGGER.info("Unwrapping Pubsub enveloppe")
            content = base64.b64decode(request.data["message"]["data"])
            data = str(content.decode("utf-8")).strip()
        else:
            data = str(request.data)
    elif API_SIGNATURE_TYPE == "http":
        data = str(request.get_data().decode("utf-8"))
        LOGGER.info("Loading config from HTTP request")
        json_data = convert_json(data)
        if json_data and "message" in json_data:  # PubSub enveloppe
            LOGGER.info("Unwrapping Pubsub enveloppe")
            content = base64.b64decode(json_data["message"]["data"])
            data = str(content.decode("utf-8")).strip()
    LOGGER.debug(data)
    return data


def convert_json(data):
    """Convert string to JSON if possible or return None otherwise.

    Args:
        data (str): Data.

    Returns:
        dict: Loaded dict.
    """
    try:
        return json.loads(data)
    except ValueError:
        return None


def process_batch_req(request, data, config):
    """Process batch request. Split list of ;-delimited URLs and make one
    request per URL.

    Args:
        request (cloudevent.CloudEvent, flask.Request): Request object.
        data (str): Incoming data.
        config (dict): SLO generator config.

    Returns:
        list: List of API responses.
    """
    LOGGER.info(
        "Batch request detected. Splitting body and sending individual "
        "requests separately."
    )
    urls = data.split(";")
    service_url = request.base_url
    headers = {"User-Agent": "slo-generator"}
    if "Authorization" in request.headers:
        headers["Authorization"] = request.headers["Authorization"]
        service_url = service_url.replace("http:", "https:")  # force HTTPS auth
    for url in urls:
        if "pubsub_batch_handler" in config:
            LOGGER.info(f"Sending {url} to pubsub batch handler.")
            from google.cloud import pubsub_v1  # pylint: disable=C0415

            # pytype: disable=attribute-error
            # pylint: disable=fixme
            # FIXME `load_config()` returns `Optional[dict]` so `config` can be `None`
            #   so `config` can be `None`
            exporter_conf = config.get("pubsub_batch_handler")
            # pytype: enable=attribute-error
            client = pubsub_v1.PublisherClient()
            project_id = exporter_conf["project_id"]
            topic_name = exporter_conf["topic_name"]
            # pylint: disable=no-member
            topic_path = client.topic_path(project_id, topic_name)
            data = url.encode("utf-8")
            client.publish(topic_path, data=data).result()
        else:  # http
            LOGGER.info(f"Sending {url} to HTTP batch handler.")
            requests.post(service_url, headers=headers, data=url, timeout=10)
