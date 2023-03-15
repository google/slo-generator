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
`prometheus.py`
Prometheus backend implementation.
"""

import json
import logging
import os
import pprint
from typing import Dict, List, Optional, Tuple

from prometheus_http_client import Prometheus

from slo_generator.constants import NO_DATA

LOGGER = logging.getLogger(__name__)


class PrometheusBackend:
    """Backend for querying metrics from Prometheus."""

    def __init__(self, client=None, url=None, headers=None):
        self.client = client
        if not self.client:
            if url:
                os.environ["PROMETHEUS_URL"] = url
            if headers:
                os.environ["PROMETHEUS_HEAD"] = json.dumps(headers)
            self.client = Prometheus()

    def query_sli(self, timestamp, window, slo_config):
        """Query SLI value from a given PromQL expression.

        Args:
            timestamp (int): UNIX timestamp.
            window (int): Window (in seconds).
            slo_config (dict): SLO configuration.

        Returns:
            float: SLI value.
        """
        measurement = slo_config["spec"]["service_level_indicator"]
        expr = measurement["expression"]
        response = self.query(expr, window, timestamp, operators=[])
        sli_value = PrometheusBackend.count(response)
        LOGGER.debug(f"SLI value: {sli_value}")
        return sli_value

    def good_bad_ratio(self, timestamp, window, slo_config):
        """Compute good bad ratio from two metric filters.

        Args:
            timestamp (int): UNIX timestamp.
            window (int): Window (in seconds).
            slo_config (dict): SLO configuration.

        Note:
            At least one of `filter_bad` or `filter_valid` is required.

        Returns:
            tuple: A tuple of (good_count, bad_count).
        """
        measurement = slo_config["spec"]["service_level_indicator"]
        good = measurement["filter_good"]
        bad = measurement.get("filter_bad")
        valid = measurement.get("filter_valid")
        operators = measurement.get("operators", ["increase", "sum"])

        # Replace window by its value in the error budget policy step
        res = self.query(good, window, timestamp, operators)
        good_count = PrometheusBackend.count(res)

        if bad:
            res = self.query(bad, window, timestamp, operators)
            bad_count = PrometheusBackend.count(res)
        elif valid:
            res = self.query(valid, window, timestamp, operators)
            valid_count = PrometheusBackend.count(res)
            bad_count = valid_count - good_count
        else:
            raise ValueError("`filter_bad` or `filter_valid` is required.")

        LOGGER.debug(f"Good events: {good_count} | " f"Bad events: {bad_count}")

        return (good_count, bad_count)

    # pylint: disable=unused-argument
    def distribution_cut(
        self, timestamp: int, window: int, slo_config: dict
    ) -> Tuple[float, float]:
        """Query events for distributions (histograms).

        Args:
            timestamp (int): UNIX timestamp.
            window (int): Window (in seconds).
            slo_config (dict): SLO configuration.

        Returns:
            float: SLI value.
        """
        measurement = slo_config["spec"]["service_level_indicator"]
        expr = measurement["expression"]
        threshold_bucket = measurement["threshold_bucket"]
        labels = {"le": threshold_bucket}
        res_good = self.query(
            expr,
            window,
            operators=["increase", "sum"],
            labels=labels,
        )
        good_count = PrometheusBackend.count(res_good)

        # We use the _count metric to figure out the 'valid count'.
        # Trying to get the valid count from the _bucket metric query is hard
        # due to Prometheus 'le' syntax that doesn't have the alternative 'ge'
        # See https://github.com/prometheus/prometheus/issues/2018.
        expr_count = expr.replace("_bucket", "_count")
        res_valid = self.query(
            expr_count,
            window,
            operators=["increase", "sum"],
        )
        valid_count = PrometheusBackend.count(res_valid)
        bad_count = valid_count - good_count
        LOGGER.debug(f"Good events: {good_count} | " f"Bad events: {bad_count}")
        return (good_count, bad_count)

    # pylint: disable=unused-argument,redefined-builtin,dangerous-default-value
    # pylint: disable=too-many-arguments
    def query(
        self,
        filter: str,
        window: int,
        timestamp: Optional[int] = None,
        operators: list = [],
        labels: dict = {},
    ) -> dict:
        """Query Prometheus server.

        Args:
            filter (str): Query filter.
            window (int): Window (in seconds).
            timestamp (int): UNIX timestamp.
            operators (list): List of PromQL operators to apply on query.
            labels (dict): Labels dict to add to existing query.

        Returns:
            dict: Response.
        """
        filter = PrometheusBackend._fmt_query(filter, window, operators, labels)
        LOGGER.debug(f"Query: {filter}")
        response = self.client.query(metric=filter)
        response = json.loads(response)
        LOGGER.debug(pprint.pformat(response))
        return response

    @staticmethod
    def count(response: dict) -> float:
        """Count events in Prometheus response.
        Args:
            response (dict): Prometheus query response.
        Returns:
            int: Event count.
        """
        # Note: this function could be replaced by using the `count_over_time`
        # function that Prometheus provides.
        try:
            return float(response["data"]["result"][0]["value"][1])
        except (IndexError, KeyError) as exception:
            LOGGER.warning("Couldn't find any values in timeseries response.")
            LOGGER.debug(exception, exc_info=True)
            return NO_DATA  # no events in timeseries

    @staticmethod
    # pylint: disable=dangerous-default-value
    def _fmt_query(
        query: str, window: int, operators: List[str] = [], labels: Dict[str, str] = {}
    ) -> str:
        """Format Prometheus query:

        * If the PromQL expression has a `window` placeholder, replace it by the
        current window. Otherwise, append it to the expression.

        * If operators are defined, apply them to the metric in sequential
        order.

        * If labels are defined, append them to existing labels.

        Args:
            query (str): Original query in YAML config.
            window (int): Query window (in seconds).
            operators (list): Operators to wrap query with.
            labels (dict): Labels dict to add to existing query.

        Returns:
            str: Formatted query.
        """
        query = query.strip()
        if "[window" in query:
            query = query.replace("[window", f"[{window}s")
        else:
            query += f"[{window}s]"
        for operator in operators:
            query = f"{operator}({query})"
        for key, value in labels.items():
            query = query.replace("}", f', {key}="{value}"}}')
        return query
