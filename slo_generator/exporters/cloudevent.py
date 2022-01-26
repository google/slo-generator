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
import requests

from cloudevents.http import CloudEvent, to_structured

LOGGER = logging.getLogger(__name__)

# pylint: disable=too-few-public-methods
class CloudeventExporter:
    """Cloudevent exporter class.

    Args:
        client (obj, optional): Existing Datadog client to pass.
        service_url (str): Cloudevent receiver service URL.
    """
    REQUIRED_FIELDS = ['service_url']

    # pylint: disable=R0201
    def export(self, data, **config):
        """Export data as CloudEvent to an HTTP service receiving cloud events.

        Args:
            data (dict): Metric data.
            config (dict): Exporter config.
        """
        attributes = {
            "source": "https://github.com/cloudevents/spec/pull",
            "type": "com.google.slo_generator.slo_report"
        }
        event = CloudEvent(attributes, data)
        headers, data = to_structured(event)
        service_url = config['service_url']
        resp = requests.post(service_url, headers=headers, data=data)
        resp.raise_for_status()
