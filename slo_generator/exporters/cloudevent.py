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
`cloudevents.py`
CloudEvents exporter class.
"""
import logging

import google.auth.transport.requests
import requests
from cloudevents.http import CloudEvent, to_structured
from google.oauth2.id_token import fetch_id_token

LOGGER = logging.getLogger(__name__)


# pylint: disable=too-few-public-methods
class CloudeventExporter:
    """Cloudevent exporter class.

    Args:
        client (obj, optional): Existing Datadog client to pass.
        service_url (str): Cloudevent receiver service URL.
    """

    REQUIRED_FIELDS = ["service_url"]
    OPTIONAL_FIELDS = ["auth"]

    def export(self, data, **config):
        """Export data as CloudEvent to an HTTP service receiving cloud events.

        Args:
            data (dict): Metric data.
            config (dict): Exporter config.
        """
        attributes = {
            "source": "https://github.com/cloudevents/spec/pull",
            "type": "com.google.slo_generator.slo_report",
        }
        event = CloudEvent(attributes, data)
        headers, data = to_structured(event)
        service_url = config["service_url"]
        if "auth" in config:
            auth = config["auth"]
            id_token = None
            if "token" in auth:
                id_token = auth["token"]
            elif auth.get("google_service_account_auth", False):  # Google oauth
                auth = google.auth.transport.requests.Request()
                id_token = fetch_id_token(auth, service_url)
            if id_token:
                headers["Authorization"] = f"Bearer {id_token}"
        resp = requests.post(
            service_url,
            headers=headers,
            data=data,
            timeout=10,
        )
        resp.raise_for_status()
        return resp
