# Copyright 2019 Google Inc.
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
`stackdriver.py`
Stackdriver Monitoring exporter class.
"""
import logging

import google.api_core.exceptions
from google.cloud import monitoring_v3

from .base import MetricsExporter

LOGGER = logging.getLogger(__name__)

class StackdriverExporter(MetricsExporter):
    """Stackdriver Monitoring exporter class."""
    METRIC_PREFIX = "custom.googleapis.com/"
    REQUIRED_FIELDS = ['project_id']

    def __init__(self):
        self.client = monitoring_v3.MetricServiceClient()

    def export_metric(self, data):
        """Export metric to Stackdriver Monitoring. Create metric descriptor if
        it doesn't exist.

        Args:
            data (dict): Data to send to Stackdriver Monitoring.
            project_id (str): Stackdriver Monitoring project id.

        Returns:
            object: Stackdriver Monitoring API result.
        """
        if not self.get_metric_descriptor(data):
            self.create_metric_descriptor(data)
        self.create_timeseries(data)

    def create_timeseries(self, data):
        """Create Stackdriver Monitoring timeseries.

        Args:
            data (dict): Metric data.

        Returns:
            object: Metric descriptor.
        """
        labels = data['labels']
        series = monitoring_v3.types.TimeSeries()
        series.metric.type = data['name']
        for key, value in labels.items():
            series.metric.labels[key] = value
        series.resource.type = 'global'

        # Create a new data point.
        point = series.points.add()

        # Define end point timestamp.
        timestamp = data['timestamp']
        point.interval.end_time.seconds = int(timestamp)
        point.interval.end_time.nanos = int(
            (timestamp - point.interval.end_time.seconds) * 10**9)

        # Set the metric value.
        point.value.double_value = data['value']

        # Record the timeseries to Stackdriver Monitoring.
        project = self.client.project_path(data['project_id'])
        result = self.client.create_time_series(project, [series])
        labels = series.metric.labels
        LOGGER.debug(
            f"timestamp: {timestamp} value: {point.value.double_value}"
            f"{labels['service_name']}-{labels['feature_name']}-"
            f"{labels['slo_name']}-{labels['error_budget_policy_step_name']}")
        return result

    def get_metric_descriptor(self, data):
        """Get Stackdriver Monitoring metric descriptor.

        Args:
            data (dict): Metric data.

        Returns:
            object: Metric descriptor (or None if not found).
        """
        descriptor = self.client.metric_descriptor_path(data['project_id'],
                                                        data['name'])
        try:
            return self.client.get_metric_descriptor(descriptor)
        except google.api_core.exceptions.NotFound:
            return None

    def create_metric_descriptor(self, data):
        """Create Stackdriver Monitoring metric descriptor.

        Args:
            data (dict): Metric data.

        Returns:
            object: Metric descriptor.
        """
        project = self.client.project_path(data['project_id'])
        descriptor = monitoring_v3.types.MetricDescriptor()
        descriptor.type = data['name']
        descriptor.metric_kind = (
            monitoring_v3.enums.MetricDescriptor.MetricKind.GAUGE)
        descriptor.value_type = (
            monitoring_v3.enums.MetricDescriptor.ValueType.DOUBLE)
        descriptor.description = data['description']
        self.client.create_metric_descriptor(project, descriptor)
        return descriptor
