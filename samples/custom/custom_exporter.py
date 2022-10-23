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
`custom_exporter.py`
Dummy sample of a custom exporter.
"""
import logging

from slo_generator.exporters.base import MetricsExporter

LOGGER = logging.getLogger(__name__)


class CustomMetricExporter(MetricsExporter):
    """Custom exporter for metrics."""

    def export_metric(self, data):
        """Export data to custom destination.

        Args:
            data (dict): Metric data.

        Returns:
            object: Custom destination response.
        """
        LOGGER.info(f"Metric data: {data}")
        return {
            "status": "ok",
            "code": 200,
        }


# pylint: disable=too-few-public-methods
class CustomSLOExporter:
    """Custom exporter for SLO data."""

    # pylint: disable=unused-argument
    def export(self, data, **config):
        """Export data to custom destination.

        Args:
            data (dict): SLO Report data.

        Returns:
            object: Custom destination response.
        """
        LOGGER.info(f"SLO data: {data}")
        return {
            "status": "ok",
            "code": 200,
        }
