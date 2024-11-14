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

import logging, os, time
import pprint
from slo_generator import utils
from datadog_api_client.v1 import Configuration, ApiClient
from datadog_api_client.v1.api.service_level_objectives_api import ServiceLevelObjectivesApi
from datadog_api_client.v1.api.metrics_api import MetricsApi
from datadog_api_client.v1.api.authentication_api import AuthenticationApi

# Configure logging
logging.basicConfig(
    level=os.environ.get('LOGLEVEL', 'ERROR').upper(), force=True
)
logger = logging.getLogger(__name__)

class DatadogClient:
    def __init__(self, api_key=None, app_key=None, api_host=None, **kwargs):
        configuration = Configuration(host=api_host, **kwargs)
        configuration.api_key['apiKeyAuth'] = api_key
        configuration.api_key['appKeyAuth'] = app_key
        self.api_client = ApiClient(configuration)
        AuthenticationApi(self.api_client).validate()
        self.slo_api_client = ServiceLevelObjectivesApi(self.api_client)
        self.metrics_api_client = MetricsApi(self.api_client)

class DatadogBackend:
    """Backend for querying metrics from Datadog.
    Args:
        client (obj, optional): Existing Datadog client to pass.
        api_key (str): Datadog API key.
        app_key (str): Datadog APP key.
        app_host (str): Datadog site.
        kwargs (dict): Extra arguments to pass to initialize function.
    """

    def __init__(self, client=None, api_key=None, app_key=None, api_host=None, **kwargs):
        self.client = client
        if not self.client:
            self.client = DatadogClient(api_key=api_key, app_key=app_key, api_host=api_host, **kwargs)

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

        if measurement.get("query_bad"):
            query = measurement.get("query_bad")
        elif measurement.get("query_valid"):
            query = measurement.get("query_valid")
        else:
            raise ValueError("One of `query_bad` or `query_valid` is required.")

        query_good = self._fmt_query(
            query_good,
            window,
            operator,
            operator_suffix,
        )

        good_event_query = self.client.metrics_api_client.query_metrics(
            _from=int(start),
            to=int(end),
            query=query_good,
        )

        query = self._fmt_query(
            query,
            window,
            operator,
            operator_suffix,
        )

        event_query = self.client.metrics_api_client.query_metrics(
            _from=int(start),
            to=int(end),
            query=query,
        )

        good_event_count = DatadogBackend.count(good_event_query)
        event_count = DatadogBackend.count(event_query)
        if measurement.get("query_valid"):
            event_count = event_count - good_event_count

        logging.debug(f"Good events: {good_event_count} | " f"Bad events: {event_count}")

        return good_event_count, event_count

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
        response = self.client.metrics_api_client.query_metrics(_from=int(start), to=int(end), query=query)
        logging.debug(f"Result valid: {pprint.pformat(response)}")
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

        try:
            # Retrieve the SLO history
            data = self.client.slo_api_client.get_slo_history(slo_id, from_ts=int(from_ts), to_ts=int(timestamp))
            logging.info(f"SLO history: {data}")
        except ApiException as e:
            logging.error(f"Error retrieving SLO history: {e}")
            return None, None

        # Check if the data is present and properly structured
        try:
            logging.debug(f"Timeseries data: {slo_id} | Result: {pprint.pformat(data)}")

            # Check if necessary keys exist before accessing them
            good_event_count = data.get("data", {}).get("series", {}).get("numerator", {}).get("sum", 0)
            valid_event_count = data.get("data", {}).get("series", {}).get("denominator", {}).get("sum", 0)

            if good_event_count is not None and valid_event_count is not None:
                bad_event_count = valid_event_count - good_event_count
                return good_event_count, bad_event_count

        except KeyError as exception:  # Monitor-based SLI case
            logging.debug(f"KeyError exception: {exception}")
            # Retrieve the SLI value if it's a monitor-based SLI
            sli_value = data.get("data", {}).get("overall", {}).get("sli_value", 0) / 100
            return sli_value, None  # Return None for bad_event_count if it's not a standard SLO

        # If the data is invalid or there's an issue, return None for both counts
        return None, None


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
        logging.debug(f"Query: {query}")
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
                value = point['value'][1]
                if value is None:
                    continue
                values.append(value)
            if not values:
                raise IndexError
            if average:
                return sum(values) / len(values)
            return sum(values)
        except (IndexError, AttributeError) as exception:
            logging.debug(exception)
            return 0  # no events in timeseries
