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
`cloud_monitoring_mql.py`
Cloud Monitoring backend implementation with MQL (Monitoring Query Language).
"""
import logging
import pprint
import re
import warnings
from collections import OrderedDict

from google.api.distribution_pb2 import Distribution
from google.cloud.monitoring_v3.services.query_service import QueryServiceClient
from google.cloud.monitoring_v3.services.query_service.pagers import \
    QueryTimeSeriesPager
from google.cloud.monitoring_v3.types import metric_service
from google.cloud.monitoring_v3.types.metric import TimeSeriesData

from slo_generator.constants import NO_DATA

LOGGER = logging.getLogger(__name__)


class CloudMonitoringMqlBackend:
    """Backend for querying metrics from Cloud Monitoring with MQL.

    Args:
        project_id (str): Cloud Monitoring host project id.
        client (google.cloud.monitoring_v3.QueryServiceClient, optional):
            Existing Cloud Monitoring Query client. Initialize a new client
            if omitted.
    """

    def __init__(self, project_id: str, client: QueryServiceClient = None):
        self.client = client
        if client is None:
            self.client = QueryServiceClient()
        self.parent = self.client.common_project_path(project_id)

    def good_bad_ratio(self,
                       timestamp: int,  # pylint: disable=unused-argument
                       window: int,
                       slo_config: dict) -> tuple[int, int]:
        """Query two timeseries, one containing 'good' events, one containing
        'bad' events.

        Args:
            timestamp (int): UNIX timestamp.
            window (int): Window size (in seconds).
            slo_config (dict): SLO configuration.

        Returns:
            tuple: A tuple (good_event_count, bad_event_count)
        """
        measurement: dict = slo_config['spec']['service_level_indicator']
        filter_good: str = measurement['filter_good']
        filter_bad: str = measurement.get('filter_bad')
        filter_valid: str = measurement.get('filter_valid')

        # Query 'good events' timeseries
        good_ts: list[TimeSeriesData] = self.query(
            query=filter_good, window=window)
        good_event_count: int = CM.count(good_ts)

        # Query 'bad events' timeseries
        if filter_bad:
            bad_ts: list[TimeSeriesData] = self.query(
                query=filter_bad, window=window)
            bad_event_count: int = CM.count(bad_ts)
        elif filter_valid:
            valid_ts: list[TimeSeriesData] = self.query(
                query=filter_valid, window=window)
            bad_event_count: int = CM.count(valid_ts) - good_event_count
        else:
            raise Exception(
                "One of `filter_bad` or `filter_valid` is required.")

        LOGGER.debug(f'Good events: {good_event_count} | '
                     f'Bad events: {bad_event_count}')

        return good_event_count, bad_event_count

    def distribution_cut(self,
                         timestamp: int,  # pylint: disable=unused-argument
                         window: int,
                         slo_config: dict) -> tuple[int, int]:
        """Query one timeseries of type 'exponential'.

        Args:
            timestamp (int): UNIX timestamp.
            window (int): Window size (in seconds).
            slo_config (dict): SLO configuration.

        Returns:
            tuple: A tuple (good_event_count, bad_event_count).
        """
        measurement: dict = slo_config['spec']['service_level_indicator']
        filter_valid: str = measurement['filter_valid']
        threshold_bucket: int = int(measurement['threshold_bucket'])
        good_below_threshold: bool = measurement.get('good_below_threshold',
                                                     True)

        # Query 'valid' events
        series = self.query(query=filter_valid, window=window)

        if not series:
            return NO_DATA, NO_DATA  # no timeseries

        distribution_value: Distribution = series[0].point_data[0].values[
            0].distribution_value
        bucket_counts: list = distribution_value.bucket_counts
        valid_events_count: int = distribution_value.count

        # Explicit the exponential distribution result
        count_sum: int = 0
        distribution = OrderedDict()
        for i, bucket_count in enumerate(bucket_counts):
            count_sum += bucket_count
            distribution[i] = {
                'count_sum': count_sum
            }
        LOGGER.debug(pprint.pformat(distribution))

        if len(distribution) - 1 < threshold_bucket:
            # maximum measured metric is below the cut after bucket number
            lower_events_count: int = valid_events_count
            upper_events_count: int = 0
        else:
            lower_events_count: int = distribution[threshold_bucket][
                'count_sum']
            upper_events_count: int = valid_events_count - lower_events_count

        if good_below_threshold:
            good_event_count: int = lower_events_count
            bad_event_count: int = upper_events_count
        else:
            good_event_count: int = upper_events_count
            bad_event_count: int = lower_events_count

        return good_event_count, bad_event_count

    def exponential_distribution_cut(self, *args, **kwargs) -> tuple[int, int]:
        """Alias for `distribution_cut` method to allow for backwards
        compatibility.
        """
        warnings.warn(
            'exponential_distribution_cut will be deprecated in version 2.0, '
            'please use distribution_cut instead', FutureWarning)
        return self.distribution_cut(*args, **kwargs)

    def query_sli(self,
                  timestamp: int,  # pylint: disable=unused-argument
                  window: int, slo_config: dict) -> float:
        """Query SLI value from a given MQL query.

        Args:
            timestamp (int): UNIX timestamp.
            window (int): Window (in seconds).
            slo_config (dict): SLO configuration.

        Returns:
            float: SLI value.
        """
        measurement: dict = slo_config['spec']['service_level_indicator']
        query: str = measurement['query']
        series: list[TimeSeriesData] = self.query(query=query, window=window)
        sli_value: float = series[0].point_data[0].values[0].double_value
        LOGGER.debug(f"SLI value: {sli_value}")
        return sli_value

    def query(self, query: str, window: int) -> list[TimeSeriesData]:
        """Query timeseries from Cloud Monitoring using MQL.

        Args:
            query (str): MQL query.
            window (int): Window size (in seconds).

        Returns:
            list: List of timeseries objects.
        """
        # Enrich query to aggregate and reduce the time series over the
        # desired window.
        formatted_query: str += self._fmt_query(query, window)
        request = metric_service.QueryTimeSeriesRequest({
            'name': self.parent,
            'query': formatted_query
        })
        timeseries_pager: QueryTimeSeriesPager = self.client.query_time_series(
            request)
        timeseries: list = list(timeseries_pager)  # convert pager to flat list
        LOGGER.debug(pprint.pformat(timeseries))
        return timeseries

    @staticmethod
    def count(timeseries: list[TimeSeriesData]) -> int:
        """Count events in time series assuming it was aligned with ALIGN_SUM
        and reduced with REDUCE_SUM (default).

        Args:
            :obj:`monitoring_v3.TimeSeries`: Timeseries object.

        Returns:
            int: Event count.
        """
        try:
            return timeseries[0].point_data[0].values[0].int64_value
        except (IndexError, AttributeError) as exception:
            LOGGER.debug(exception, exc_info=True)
            return NO_DATA  # no events in timeseries

    @staticmethod
    def _fmt_query(query: str, window: int) -> str:
        """Format MQL query:

        * If the MQL expression has a `window` placeholder, replace it by the
        current window. Otherwise, append it to the expression.

        * If the MQL expression has a `every` placeholder, replace it by the
        current window. Otherwise, append it to the expression.

        * If the MQL expression has a `group_by` placeholder, replace it.
        Otherwise, append it to the expression.

        Args:
            query (str): Original query in YAMLconfig.
            window (int): Query window (in seconds).

        Returns:
            str: Formatted query.
        """
        formatted_query: str = query.strip()
        if 'group_by' in formatted_query:
            formatted_query = re.sub(r'\|\s+group_by\s+\[.*\]\s*',
                                     '| group_by [] ', formatted_query)
        else:
            formatted_query += '| group_by [] '
        for mql_time_interval_keyword in ['within', 'every']:
            if mql_time_interval_keyword in formatted_query:
                formatted_query = re.sub(
                    fr'\|\s+{mql_time_interval_keyword}\s+\w+\s*',
                    f'| {mql_time_interval_keyword} {window}s ',
                    formatted_query)
            else:
                formatted_query += f'| {mql_time_interval_keyword} {window}s '
        return formatted_query.strip()


CM = CloudMonitoringMqlBackend
