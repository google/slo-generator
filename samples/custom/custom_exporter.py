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

class CustomExporter(MetricsExporter):
    """Custom exporter."""

    def export_metric(self, data, **config):
        """Export data to Stackdriver Monitoring.

        Args:
            data (dict): Data to send.
            config (dict): Exporter config.

        Returns:
            object: Stackdriver Monitoring API result.
        """
        return {
            'status': 'ok',
            'code': 200
        }
