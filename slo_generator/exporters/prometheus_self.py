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
`prometheus_self.py`
Prometheus Self exporter class.
"""
import logging

from flask import current_app, make_response
from prometheus_client import Gauge, generate_latest

from .base import MetricsExporter

LOGGER = logging.getLogger(__name__)


class PrometheusSelfExporter(MetricsExporter):
    """Prometheus exporter class which uses
    the API mode of itself to export the metrics."""

    REGISTERED_URL: bool = False
    REGISTERED_METRICS: dict = {}

    def __init__(self):
        if not self.REGISTERED_URL:
            current_app.add_url_rule("/metrics", view_func=self.serve_metrics)
            PrometheusSelfExporter.REGISTERED_URL = True

    @staticmethod
    def serve_metrics():
        """Serves prometheus metrics

        Returns:
            object: Flask HTTP Response
        """
        resp = make_response(generate_latest(), 200)
        resp.mimetype = "text/plain"
        return resp

    def export_metric(self, data):
        """Export data to Prometheus global registry.

        Args:
            data (dict): Metric data.
        """
        name = data["name"]
        description = data["description"]
        value = data["value"]

        # Write timeseries w/ metric labels.
        labels = data["labels"]
        gauge = self.REGISTERED_METRICS.get(name)
        if gauge is None:
            gauge = Gauge(
                name,
                description,
                labelnames=labels.keys(),
            )
            PrometheusSelfExporter.REGISTERED_METRICS[name] = gauge
        gauge.labels(*labels.values()).set(value)
