# Copyright 2024 Google Inc.
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
`opentelemetry.py`
OpenTelemetry exporter class.
"""

import logging

from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource

from .base import MetricsExporter

LOGGER = logging.getLogger(__name__)


class OpenTelemetryExporter(MetricsExporter):
    """OpenTelemetry exporter class."""

    REQUIRED_FIELDS = ["endpoint"]
    OPTIONAL_FIELDS = ["headers", "insecure"]
    METRIC_PREFIX = "slo_"

    def export_metric(self, data):
        """Export data via OpenTelemetry OTLP.

        Args:
            data (dict): Metric data.
        """
        endpoint = data["endpoint"]
        headers = data.get("headers")
        insecure = data.get("insecure", False)

        name = data["name"]
        description = data["description"]
        value = data["value"]
        labels = data["labels"]

        exporter_kwargs = {"endpoint": endpoint, "insecure": insecure}
        if headers:
            exporter_kwargs["headers"] = list(headers.items())

        otlp_exporter = OTLPMetricExporter(**exporter_kwargs)
        reader = PeriodicExportingMetricReader(
            otlp_exporter, export_interval_millis=1_000_000
        )
        resource = Resource.create({"service.name": "slo-generator"})
        provider = MeterProvider(resource=resource, metric_readers=[reader])
        meter = provider.get_meter("slo-generator")

        gauge = meter.create_gauge(name=name, description=description)
        gauge.set(value, attributes=labels)

        provider.force_flush()
        provider.shutdown()
