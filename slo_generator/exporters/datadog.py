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
`datadog.py`
Datadog exporter class.
"""
import logging

import datadog

from .base import MetricsExporter

LOGGER = logging.getLogger(__name__)
logging.getLogger("datadog.api").setLevel(logging.ERROR)

DEFAULT_API_HOST = "https://api.datadoghq.com"


# pylint: disable=too-few-public-methods
class DatadogExporter(MetricsExporter):
    """Datadog exporter class.

    Args:
        client (obj, optional): Existing Datadog client to pass.
        api_key (str): Datadog API key.
        app_key (str): Datadog APP key.
        kwargs (dict): Extra arguments to pass to initialize function.
    """

    REQUIRED_FIELDS = ["api_key", "app_key"]
    OPTIONAL_FIELDS = ["api_host"]

    def export_metric(self, data):
        """Export a metric to Datadog.

        Args:
            data (dict): Metric data.

        Raises:
            DatadogError (object): Datadog exception object.
        """
        options = {
            "api_key": data["api_key"],
            "app_key": data["app_key"],
            "api_host": data.get("api_host", DEFAULT_API_HOST),
        }
        datadog.initialize(**options)
        client = datadog.api
        timestamp = data["timestamp"]
        tags = data["labels"]
        name = data["name"]
        value = data["value"]
        return client.Metric.send(
            metric=name,
            points=[(timestamp, value)],
            tags=tags,
        )
