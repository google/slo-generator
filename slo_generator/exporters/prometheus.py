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

from prometheus_client import CollectorRegistry, Gauge, pushadd_to_gateway
from prometheus_client.exposition import basic_auth_handler, default_handler

from .base import MetricsExporter

LOGGER = logging.getLogger(__name__)
DEFAULT_PUSHGATEWAY_JOB = "slo-generator"


class PrometheusExporter(MetricsExporter):
    """Prometheus exporter class."""

    REQUIRED_FIELDS = ["url"]
    OPTIONAL_FIELDS = ["job", "username", "password"]

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
        name = data["name"]
        description = data["description"]
        prometheus_push_url = data["url"]
        prometheus_push_job_name = data.get("job", DEFAULT_PUSHGATEWAY_JOB)
        value = data["value"]

        # Write timeseries w/ metric labels.
        labels = data["labels"]
        registry = CollectorRegistry()
        gauge = Gauge(
            name,
            description,
            registry=registry,
            labelnames=labels.keys(),
        )
        gauge.labels(*labels.values()).set(value)

        # Handle headers
        handler = default_handler
        if "username" in data and "password" in data:
            self.username = data["username"]
            self.password = data["password"]
            handler = PrometheusExporter.auth_handler

        return pushadd_to_gateway(
            prometheus_push_url,
            job=prometheus_push_job_name,
            grouping_key=labels,
            registry=registry,
            handler=handler,
        )

    # pylint: disable=too-many-arguments
    def auth_handler(self, url, method, timeout, headers, data):
        """Handles authentication for pushing to Prometheus gateway.

        Args:
            url (str): Prometheus gateway URL.
            method (str): Prometheus query method.
            timeout (int): Prometheus timeout.
            headers (dict): Headers.
            data (dict): Data to send.

        Returns:
            func: Auth handler function.
        """
        username = self.username
        password = self.password
        return basic_auth_handler(
            url, method, timeout, headers, data, username, password
        )
