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
`datadog.py`
Datadog backend implementation.
"""

import logging
import pprint

import datadog

LOGGER = logging.getLogger(__name__)
logging.getLogger("datadog.api").setLevel(logging.ERROR)


class DatadogBackend:
    """Backend for querying metrics from Datadog.

    Args:
        client (obj, optional): Existing Datadog client to pass.
        api_key (str): Datadog API key.
        app_key (str): Datadog APP key.
        kwargs (dict): Extra arguments to pass to initialize function.
    """

    def __init__(self, client=None, api_key=None, app_key=None, **kwargs):
        self.client = client
        if not self.client:
            options = {"api_key": api_key, "app_key": app_key}
            options.update(kwargs)
            datadog.initialize(**options)
            self.client = datadog.api

    # pylint: disable=too-many-locals
    def good_bad_ratio(self, timestamp, window, slo_config):
        """Query SLI value from good and valid queries.

        Args:
            timestamp (int): UNIX timestamp.
            window (int): Window (in seconds).
            slo_config (dict): SLO configuration.

        Returns:
            tuple: Good event count, Bad event count.
        """
        measurement = slo_config["spec"]["service_level_indicator"]
        operator = measurement.get("operator", "sum")
        operator_suffix = measurement.get("operator_suffix", "as_count()")
        start = timestamp - window
        end = timestamp
        query_good = measurement["query_good"]
        query_valid = measurement["query_valid"]
        query_good = self._fmt_query(
            query_good,
            window,
            operator,
            operator_suffix,
        )
        query_valid = self._fmt_query(
            query_valid,
            window,
            operator,
            operator_suffix,
        )
        good_event_query = self.client.Metric.query(
            start=start,
            end=end,
            query=query_good,
        )
        valid_event_query = self.client.Metric.query(
            start=start,
            end=end,
            query=query_valid,
        )
        LOGGER.debug(f"Result good: {pprint.pformat(good_event_query)}")
        LOGGER.debug(f"Result valid: {pprint.pformat(valid_event_query)}")
        good_event_count = DatadogBackend.count(good_event_query)
        valid_event_count = DatadogBackend.count(valid_event_query)
        bad_event_count = valid_event_count - good_event_count
        return (good_event_count, bad_event_count)

    def query_sli(self, timestamp, window, slo_config):
        """Query SLI value directly.

        Args:
            timestamp (int): UNIX timestamp.
            window (int): Window (in seconds).
            slo_config (dict): SLO configuration.

        Returns:
            float: SLI value.
        """
        measurement = slo_config["spec"]["service_level_indicator"]
        start = timestamp - window
        end = timestamp
        query = measurement["query"]
        query = self._fmt_query(query, window)
        response = self.client.Metric.query(start=start, end=end, query=query)
        LOGGER.debug(f"Result valid: {pprint.pformat(response)}")
        return DatadogBackend.count(response, average=True)

    def query_slo(self, timestamp, window, slo_config):
        """Query SLO value from a given Datadog SLO.

        Args:
            timestamp (int): UNIX timestamp.
            window (int): Window (in seconds).
            slo_config (dict): SLO configuration.

        Returns:
            tuple: Good event count, bad event count.
        """
        slo_id = slo_config["spec"]["service_level_indicator"]["slo_id"]
        from_ts = timestamp - window
        slo_data = self.client.ServiceLevelObjective.get(id=slo_id)
        LOGGER.debug(f"SLO data: {slo_id} | Result: {pprint.pformat(slo_data)}")
        data = self.client.ServiceLevelObjective.history(
            id=slo_id,
            from_ts=from_ts,
            to_ts=timestamp,
        )
        try:
            LOGGER.debug(f"Timeseries data: {slo_id} | Result: {pprint.pformat(data)}")
            good_event_count = data["data"]["series"]["numerator"]["sum"]
            valid_event_count = data["data"]["series"]["denominator"]["sum"]
            bad_event_count = valid_event_count - good_event_count
            return (good_event_count, bad_event_count)
        except KeyError as exception:  # monitor-based SLI
            sli_value = data["data"]["overall"]["sli_value"] / 100
            LOGGER.debug(exception)
            return sli_value

    @staticmethod
    def _fmt_query(query, window, operator=None, operator_suffix=None):
        """Format Datadog query:

        * If the Datadog expression has a `[window]` placeholder, replace it by
        the current window. Otherwise, append it to the expression.

        * If prefix / suffix operators are defined, apply them to the metric.

        * If labels are defined, append them to existing labels.

        Args:
            query (str): Original query in YAML config.
            window (int): Query window (in seconds).
            operator (str): Operator (e.g: sum, avg, median, ...)
            operator_suffix (str): Operator suffix (e.g: as_count(), ...)

        Returns:
            str: Formatted query.
        """
        query = query.strip()
        if operator:
            query = f"{operator}:{query}"
        if "[window]" in query:
            query = query.replace("[window]", f"{window}")
        if operator_suffix:
            query = f"{query}.{operator_suffix}"
        LOGGER.debug(f"Query: {query}")
        return query

    @staticmethod
    def count(response, average=False):
        """Count events in time series.

        Args:
            response (dict):  Datadog Metrics API response.
            average (bool): Take average of result.

        Returns:
            int: Event count.
        """
        try:
            values = []
            pointlist = response["series"][0]["pointlist"]
            for point in pointlist:
                value = point[1]
                if value is None:
                    continue
                values.append(value)
            if not values:
                raise IndexError
            if average:
                return sum(values) / len(values)
            return sum(values)
        except (IndexError, AttributeError) as exception:
            LOGGER.debug(exception)
            return 0  # no events in timeseries
