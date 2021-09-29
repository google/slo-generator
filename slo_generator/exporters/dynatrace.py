# Copyright 2020 Google Inc.
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
`dynatrace.py`
Dynatrace exporter implementation.
"""
import logging
import time

from slo_generator.backends.dynatrace import DynatraceClient

from .base import MetricsExporter

LOGGER = logging.getLogger(__name__)
DEFAULT_DEVICE_ID = "slo_report"

class DynatraceExporter(MetricsExporter):
    """Backend for querying metrics from Dynatrace.

    Args:
        client (obj, optional): Existing Dynatrace client to pass.
        api_url (str): Dynatrace API URL.
        api_token (str): Dynatrace token.
    """
    METRIC_PREFIX = 'custom:'
    REQUIRED_FIELDS = ['api_url', 'api_token']

    def __init__(self):
        self.client = None

    def export_metric(self, data):
        """Export SLO data to Dynatrace.

        Args:
            data (dict): Metric data.

        Returns:
            object: Dynatrace API response.
        """
        api_url, api_token = data['api_url'], data['api_token']
        self.client = DynatraceClient(api_url, api_token)
        metric = self.get_custom_metric(data)
        code = int(metric.get('error', {}).get('code', '200'))
        if code == 404:
            LOGGER.warning("Custom metric doesn't exist. Creating it.")
            metric = self.create_custom_metric(data)
        LOGGER.debug(f'Custom metric: {metric}')
        response = self.create_timeseries(data)
        LOGGER.debug(f'API Response: {response}')
        return response

    def create_timeseries(self, data):
        """Create Dynatrace timeseries.

        Args:
            data (dict): Metric data.

        Returns:
            object: Dynatrace API response.
        """
        name = data['name']
        labels = data['labels']
        value = data['value']
        tags = data.get('tags', [])
        device_id = data.get('device_id', DEFAULT_DEVICE_ID)
        timestamp_ms = time.time() * 1000
        timeseries = {
            "type":
            DEFAULT_DEVICE_ID,
            "tags":
            tags,
            "properties": {},
            "series": [{
                "timeseriesId": name,
                "dimensions": labels,
                "dataPoints": [[timestamp_ms, value]]
            }]
        }
        return self.client.request('post',
                                   'entity/infrastructure/custom',
                                   name=device_id,
                                   post_data=timeseries)

    def create_custom_metric(self, data):
        """Create a metric descriptor in Dynatrace API.

        Args:
            data (dict): Metric data.

        Returns:
            obj: Dynatrace API response.
        """
        name = data['name']
        device_ids = [data.get('device_id', DEFAULT_DEVICE_ID)]
        labelkeys = list(data['labels'].keys())
        metric = {
            "displayName": name,
            "unit": "Count",
            "dimensions": labelkeys,
            "types": device_ids
        }
        return self.client.request('put',
                                   'timeseries',
                                   name=name,
                                   post_data=metric)

    def get_custom_metric(self, data):
        """Get a custom metric descriptor from Dynatrace API.

        Args:
            data (dict): Metric data.

        Returns:
            obj: Dynatrace API response.
        """
        name = data['name']
        return self.client.request('get',
                                   'timeseries',
                                   name=name)
