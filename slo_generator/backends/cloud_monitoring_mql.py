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
import typing
import warnings
from collections import OrderedDict
from datetime import datetime, timezone
from typing import List, Optional, Tuple

from google.api.distribution_pb2 import Distribution
from google.cloud.monitoring_v3 import QueryTimeSeriesRequest
from google.cloud.monitoring_v3.services.query_service import QueryServiceClient
from google.cloud.monitoring_v3.services.query_service.pagers import (
    QueryTimeSeriesPager,
)
from google.cloud.monitoring_v3.types.metric import TimeSeries

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

    def __init__(self, project_id: str, client=None):
        self.client = client
        if client is None:
            self.client = QueryServiceClient()
        self.parent = self.client.common_project_path(  # type: ignore[union-attr]
            project_id
        )

    def good_bad_ratio(
        self,
        timestamp: int,
        window: int,
        slo_config: dict,
    ) -> Tuple[int, int]:
        """Query two timeseries, one containing 'good' events, one containing
        'bad' events.

        Args:
            timestamp (int): UNIX timestamp.
            window (int): Window size (in seconds).
            slo_config (dict): SLO configuration.

        Returns:
            tuple: A tuple (good_event_count, bad_event_count)
        """
        measurement: dict = slo_config["spec"]["service_level_indicator"]
        filter_good: str = measurement["filter_good"]
        filter_bad: Optional[str] = measurement.get("filter_bad")
        filter_valid: Optional[str] = measurement.get("filter_valid")

        # Query 'good events' timeseries
        good_ts: List[TimeSeries] = self.query(timestamp, window, filter_good)
        good_event_count: int = CM.count(good_ts)

        # Query 'bad events' timeseries
        bad_event_count: int
        if filter_bad:
            bad_ts: List[TimeSeries] = self.query(timestamp, window, filter_bad)
            bad_event_count = CM.count(bad_ts)
        elif filter_valid:
            valid_ts: List[TimeSeries] = self.query(timestamp, window, filter_valid)
            bad_event_count = CM.count(valid_ts) - good_event_count
        else:
            raise ValueError("One of `filter_bad` or `filter_valid` is required.")

        LOGGER.debug(
            f"Good events: {good_event_count} | " f"Bad events: {bad_event_count}"
        )

        return good_event_count, bad_event_count

    # pylint: disable=too-many-locals,disable=unused-argument
    def distribution_cut(
        self,
        timestamp: int,
        window: int,
        slo_config: dict,
    ) -> Tuple[int, int]:
        """Query one timeseries of type 'exponential'.

        Args:
            timestamp (int): UNIX timestamp.
            window (int): Window size (in seconds).
            slo_config (dict): SLO configuration.

        Returns:
            tuple: A tuple (good_event_count, bad_event_count).
        """
        measurement: dict = slo_config["spec"]["service_level_indicator"]
        filter_valid: str = measurement["filter_valid"]
        threshold_bucket: int = int(measurement["threshold_bucket"])
        good_below_threshold: typing.Optional[bool] = measurement.get(
            "good_below_threshold", True
        )

        # Query 'valid' events
        series = self.query(timestamp, window, filter_valid)

        if not series:
            return NO_DATA, NO_DATA  # no timeseries

        distribution_value: Distribution = (
            series[0].point_data[0].values[0].distribution_value
        )
        bucket_counts: list = distribution_value.bucket_counts
        valid_events_count: int = distribution_value.count

        # Explicit the exponential distribution result
        count_sum: int = 0
        distribution = OrderedDict()
        for i, bucket_count in enumerate(bucket_counts):
            count_sum += bucket_count
            distribution[i] = {"count_sum": count_sum}
        LOGGER.debug(pprint.pformat(distribution))

        lower_events_count: int
        upper_events_count: int
        if len(distribution) - 1 < threshold_bucket:
            # maximum measured metric is below the cut after bucket number
            lower_events_count = valid_events_count
            upper_events_count = 0
        else:
            lower_events_count = distribution[threshold_bucket]["count_sum"]
            upper_events_count = valid_events_count - lower_events_count

        good_event_count: int
        bad_event_count: int
        if good_below_threshold:
            good_event_count = lower_events_count
            bad_event_count = upper_events_count
        else:
            good_event_count = upper_events_count
            bad_event_count = lower_events_count

        return good_event_count, bad_event_count

    def exponential_distribution_cut(self, *args, **kwargs) -> Tuple[int, int]:
        """Alias for `distribution_cut` method to allow for backwards
        compatibility.
        """
        warnings.warn(
            "exponential_distribution_cut will be deprecated in version 2.0, "
            "please use distribution_cut instead",
            FutureWarning,
        )
        return self.distribution_cut(*args, **kwargs)

    def query_sli(
        self,
        timestamp: int,  # pylint: disable=unused-argument
        window: int,
        slo_config: dict,
    ) -> float:
        """Query SLI value from a given MQL query.

        Args:
            timestamp (int): UNIX timestamp.
            window (int): Window (in seconds).
            slo_config (dict): SLO configuration.

        Returns:
            float: SLI value.
        """
        measurement: dict = slo_config["spec"]["service_level_indicator"]
        query: str = measurement["query"]
        series: List[TimeSeries] = self.query(timestamp, window, query)
        sli_value: float = series[0].point_data[0].values[0].double_value
        LOGGER.debug(f"SLI value: {sli_value}")
        return sli_value

    def query(self, timestamp: float, window: int, query: str) -> List[TimeSeries]:
        """Query timeseries from Cloud Monitoring using MQL.

        Args:
            timestamp (float): Current timestamp.
            window (int): Window size (in seconds).
            query (str): MQL query.
        Returns:
            list: List of timeseries objects.
        """
        # Enrich query to aggregate and reduce time series over target window.
        query_with_time_horizon_and_period: str = (
            self.enrich_query_with_time_horizon_and_period(timestamp, window, query)
        )
        request = QueryTimeSeriesRequest(
            {"name": self.parent, "query": query_with_time_horizon_and_period}
        )
        # fmt: off
        timeseries_pager: QueryTimeSeriesPager = (
            self.client.query_time_series(request)  # type: ignore[union-attr]
        )
        # fmt: on
        timeseries: List[TimeSeries] = list(timeseries_pager)
        LOGGER.debug(pprint.pformat(timeseries))
        return timeseries

    @staticmethod
    def enrich_query_with_time_horizon_and_period(
        timestamp: float,
        window: int,
        query: str,
    ) -> str:
        """Enrich MQL query with time period and horizon.
        Args:
            timestamp (float): UNIX timestamp.
            window (int): Query window (in seconds).
            query (str): Base query in YAML config.
        Returns:
            str: Enriched query.
        """
        # Python uses floating point numbers to represent time in seconds since the
        # epoch, in UTC, with decimal part representing nanoseconds.
        # MQL expects dates formatted like "%Y/%m/%d %H:%M:%S" or "%Y/%m/%d-%H:%M:%S".
        # Reference: https://cloud.google.com/monitoring/mql/reference#lexical-elements
        end_time_str: str = datetime.fromtimestamp(timestamp, tz=timezone.utc).strftime(
            "%Y/%m/%d %H:%M:%S"
        )
        query_with_time_horizon_and_period: str = (
            query
            + f"| group_by [] | within {window}s, d'{end_time_str}' | every {window}s"
        )
        return query_with_time_horizon_and_period

    @staticmethod
    def count(timeseries: List[TimeSeries]) -> int:
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


CM = CloudMonitoringMqlBackend
