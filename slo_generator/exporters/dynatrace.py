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
import pprint
import random
import sched
import time

from slo_generator.backends.dynatrace import DynatraceClient

LOGGER = logging.getLogger(__name__)
DEFAULT_METRIC_TYPE = "custom:error_budget_burn_rate"
DEFAULT_METRIC_DESCRIPTION = ("Speed at which the error budget for a given"
                              "aggregation window is consumed")
DEFAULT_METRIC_TYPES = ["SLO"]
DEFAULT_METRIC_DISPLAY_NAME = "Error budget burn rate"


class DynatraceExporter:
    """Backend for querying metrics from Dynatrace.

    Args:
        client (obj, optional): Existing `requests.Session` to pass.
        api_url (str): Dynatrace API URL.
        api_token (str): Dynatrace token.
    """
    def __init__(self, client, api_url, api_key):
        self.client = client
        if client is None:
            self.client = DynatraceClient(api_url, api_key)

    def export(self, data, **config):
        """Export SLO data to Dynatrace.

        Args:
            data (dict): Data to send to Dynatrace
            config (dict): Metric / exporter config.

        Returns:
            object: Dynatrace API response.
        """
        ret = self.create_metric_descriptor(data, **config)
        LOGGER.info(ret)
        ret2 = self.create_timeseries(data, **config)
        LOGGER.info(ret2)
        return ret2

    def create_timeseries(self, data, **config):
        """Create Dynatrace timeseries.

        Args:
            data (dict): Data to send to Dynatrace
            config (dict): Metric / exporter config.

        Returns:
            object: Dynatrace API response.
        """
        metric_description = config.get('metric_description',
                                        DEFAULT_METRIC_DESCRIPTION)
        metric_display_name = config.get('metric_display_name',
                                         DEFAULT_METRIC_DISPLAY_NAME)
        tags = config.get('metric_tags', [])
        prometheus_push_url = config.get('url', DEFAULT_DYNATRACE_URL)
        prometheus_push_job_name = config.get('job', DEFAULT_PUSHGATEWAY_JOB)
        burn_rate = data['error_budget_burn_rate']
        labels = {
            'service_name':
            data['service_name'],
            'feature_name':
            data['feature_name'],
            'slo_name':
            data['slo_name'],
            'window':
            str(data['window']),
            'error_budget_policy_step_name':
            str(data['error_budget_policy_step_name']),
            'alerting_burn_rate_threshold':
            str(data['alerting_burn_rate_threshold']),
        }
        timeseries = {
            "displayName": f'{metric_display_name},
            "type": "SLO",
            "tags": metric_tags,
            "properties": {},
            "series": [{
                "timeseriesId": metric_type,
                "dimensions": labels,
                "dataPoints": [[timestamp, error_budget_burn_rate]]
            }]
        }
        return self.client.request('post',
                                    endpoint='entity/infrastructure/custom',
                                    name=metric_display_name,
                                    post_data=timeseries)

    def create_metric_descriptor(self, data, **config):
        """Create a metric descriptor in Dynatrace API.

        Args:
            data (dict): SLO Report data
            condif (dict): Exporter config

        Returns:
            obj: Dynatrace API response.
        """
        metric_description = config.get('metric_description',
                                        DEFAULT_METRIC_DESCRIPTION)
        metric_type = config.get('metric_type', DEFAULT_METRIC_TYPE)
        metric_types = config.get('metric_types', [])
        labelkeys = [
            'service_name', 'feature_name', 'slo_name', 'window',
            'error_budget_burn_rate', 'alerting_burn_rate_threshold'
        ]
        metric_definition = {
            "displayName": metric_description,
            "unit": "Count",
            "dimensions": labelkeys,
            "types": metric_types
        }
        return self.client.request('put',
                                    endpoint='timeseries',
                                    name=metric_type,
                                    post_data=metric_definition)
