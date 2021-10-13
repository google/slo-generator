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
`prometheus_remote_write.py`
Prometheus Remote Write API exporter class.
"""
import logging
import snappy
import requests

from .base import MetricsExporter
from .prometheus_remote_write_pb2 import WriteRequest, MetricMetadata, Sample, Label

LOGGER = logging.getLogger(__name__)
DEFAULT_JOB = "slo-generator"


class PrometheusRemoteWriteExporter(MetricsExporter):
    """Prometheus Remote Write exporter class."""
    REQUIRED_FIELDS = ['url']
    OPTIONAL_FIELDS = ['job', 'username', 'password']

    def __init__(self):
        self.username = None
        self.password = None

    def export_metric(self, data):
        """Export data to Prometheus.

        Args:
            data (dict): Metric data.

        Returns:
            object: Prometheus API result.
        """
        self.create_timeseries(data)

    def create_timeseries(self, data):
        """Create Prometheus timeseries.

        Args:
            data (dict): Metric data.

        Returns:
            object: Metric descriptor.
        """

        write_request = WriteRequest()
        write_request.metadata.append(MetricMetadata(
            type=MetricMetadata.GAUGE, metric_family_name=data['name'], help=data['description']
        ))

        series = write_request.timeseries.add()
        series.samples.append(Sample(
            timestamp=data['timestamp'] * 1000, value=data['value']
        ))

        for k, v in data['labels'].items():
            series.labels.append(Label(name=k, value=v))

        series.labels.extend((
            Label(name="job", value=data.get('job', DEFAULT_JOB)),
            Label(name="__name__", value=data['name']),
        ))

        uncompressed = write_request.SerializeToString()
        compressed = snappy.compress(uncompressed)

        headers = {
            "Content-Encoding": "snappy",
            "Content-Type": "application/x-protobuf",
            "X-Prometheus-Remote-Write-Version": "0.1.0",
        }

        return requests.post(data['url'], headers=headers, data=compressed, auth=(data['username'], data['password']))
