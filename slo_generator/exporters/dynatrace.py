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

LOGGER = logging.getLogger(__name__)
DEFAULT_TIMESERIES_ID = "custom:error_budget_burn_rate"
DEFAULT_METRIC_DESCRIPTION = ("Speed at which the error budget for a given"
                              "aggregation window is consumed")
DEFAULT_DEVICE_ID = "slo_report"
DEFAULT_METRIC_LABELS = [
    'service_name', 'feature_name', 'slo_name', 'window',
    'error_budget_policy_step_name', 'alerting_burn_rate_threshold'
]


class DynatraceExporter:
    """Backend for querying metrics from Dynatrace.

    Args:
        client (obj, optional): Existing Dynatrace client to pass.
        api_url (str): Dynatrace API URL.
        api_token (str): Dynatrace token.
    """
    def __init__(self):
        self.client = None

    def export(self, data, **config):
        """Export SLO data to Dynatrace.

        Args:
            data (dict): Data to send to Dynatrace.
            config (dict): Metric / exporter config.

        Returns:
            object: Dynatrace API response.
        """
        api_url, api_token = config['api_url'], config['api_token']
        self.client = DynatraceClient(api_url, api_token)
        metric = self.get_custom_metric(**config)
        if 'error' in metric:
            LOGGER.warning("Custom metric doesn't exist. Creating it.")
            metric = self.create_custom_metric(**config)
        LOGGER.debug(f'Custom metric: {metric}')
        response = self.create_timeseries(data, **config)
        LOGGER.debug(f'API Response: {response}')
        return response

    def create_timeseries(self, data, **config):
        """Create Dynatrace timeseries.

        Args:
            data (dict): Data to send to Dynatrace.
            config (dict): Metric / exporter config.

        Returns:
            object: Dynatrace API response.
        """
        metric_tags = config.get('metric_tags', [])
        metric_timeseries_id = config.get('metric_timeseries_id',
                                          DEFAULT_TIMESERIES_ID)
        error_budget_burn_rate = data['error_budget_burn_rate']
        device_id = config.get('device_id', DEFAULT_DEVICE_ID)
        timestamp_ms = time.time() * 1000
        labels = {
            key: value
            for key, value in data.items() if key in DEFAULT_METRIC_LABELS
        }
        timeseries = {
            "type":
            DEFAULT_DEVICE_ID,
            "tags":
            metric_tags,
            "properties": {},
            "series": [{
                "timeseriesId": metric_timeseries_id,
                "dimensions": labels,
                "dataPoints": [[timestamp_ms, error_budget_burn_rate]]
            }]
        }
        return self.client.request('post',
                                   'entity/infrastructure/custom',
                                   name=device_id,
                                   post_data=timeseries)

    def create_custom_metric(self, **config):
        """Create a metric descriptor in Dynatrace API.

        Args:
            config (dict): Exporter config.

        Returns:
            obj: Dynatrace API response.
        """
        metric_description = config.get('metric_description',
                                        DEFAULT_METRIC_DESCRIPTION)
        metric_timeseries_id = config.get('metric_timeseries_id',
                                          DEFAULT_TIMESERIES_ID)
        device_ids = [config.get('device_id', DEFAULT_DEVICE_ID)]
        labelkeys = DEFAULT_METRIC_LABELS
        metric_definition = {
            "displayName": metric_description,
            "unit": "Count",
            "dimensions": labelkeys,
            "types": device_ids
        }
        return self.client.request('put',
                                   'timeseries',
                                   name=metric_timeseries_id,
                                   post_data=metric_definition)

    def get_custom_metric(self, **config):
        """Get a custom metric descriptor from Dynatrace API.

        Args:
            data (dict): SLO Report data.
            config(dict): Exporter config.

        Returns:
            obj: Dynatrace API response.
        """
        metric_timeseries_id = config.get('metric_timeseries_id',
                                          DEFAULT_TIMESERIES_ID)
        return self.client.request('get',
                                   'timeseries',
                                   name=metric_timeseries_id)
