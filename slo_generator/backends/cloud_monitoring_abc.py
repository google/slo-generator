# Copyright 2022 Google Inc.
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
`cloud_monitoring_base.py`
Abstract Base Class (ABC) for Cloud Monitoring backend implementations.
"""
import logging
import pprint
import warnings
from abc import ABC, abstractmethod
from collections import OrderedDict
from typing import List, Optional, Tuple

from google.api.distribution_pb2 import Distribution
from google.cloud.monitoring_v3.types.metric import TimeSeries

from slo_generator.constants import NO_DATA

LOGGER = logging.getLogger(__name__)


class CloudMonitoringBackendABC(ABC):
    """Abstract Base Class (ABC) for Cloud Monitoring backend implementations.

    Args:
        project_id (str): Cloud Monitoring host project ID.
        client (optional): Existing Cloud Monitoring client. Initialize a new client if
            omitted.
    """

    def good_bad_ratio(
        self,
        timestamp: float,
        window: int,
        slo_config: dict,
    ) -> Tuple[int, int]:
        """Query two timeseries, one containing 'good' events, one containing 'bad'
        events.

        Args:
            timestamp (float): UNIX timestamp.
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
        good_event_count: int = self.count(good_ts)

        # Query 'bad events' timeseries
        bad_event_count: int
        if filter_bad:
            bad_ts: List[TimeSeries] = self.query(timestamp, window, filter_bad)
            bad_event_count = self.count(bad_ts)
        elif filter_valid:
            valid_ts: List[TimeSeries] = self.query(timestamp, window, filter_valid)
            bad_event_count = self.count(valid_ts) - good_event_count
        else:
            raise Exception("One of `filter_bad` or `filter_valid` is required.")

        LOGGER.debug(
            f"Good events: {good_event_count} | " f"Bad events: {bad_event_count}"
        )

        return good_event_count, bad_event_count

    # pylint: disable=too-many-locals
    def distribution_cut(
        self,
        timestamp: float,
        window: int,
        slo_config: dict,
    ) -> Tuple[int, int]:
        """Query one timeseries of type 'exponential'.

        Args:
            timestamp (float): UNIX timestamp.
            window (int): Window size (in seconds).
            slo_config (dict): SLO configuration.

        Returns:
            tuple: A tuple (good_event_count, bad_event_count).
        """
        measurement: dict = slo_config["spec"]["service_level_indicator"]
        filter_valid: str = measurement["filter_valid"]
        threshold_bucket: int = int(measurement["threshold_bucket"])
        good_below_threshold: bool = measurement.get("good_below_threshold", True)

        # Query 'valid' events.
        series = self.query(timestamp, window, filter_valid)

        if not series:
            return NO_DATA, NO_DATA  # No timeseries.

        distribution_value = self.get_distribution_value_from_timeseries(series)
        bucket_counts: list[int] = distribution_value.bucket_counts
        valid_events_count: int = distribution_value.count

        # Explicit the exponential distribution result.
        count_sum: int = 0
        distribution = OrderedDict()
        for i, bucket_count in enumerate(bucket_counts):
            count_sum += bucket_count
            distribution[i] = {"count_sum": count_sum}
        LOGGER.debug(pprint.pformat(distribution))

        lower_events_count: int
        upper_events_count: int
        if len(distribution) - 1 < threshold_bucket:
            # Maximum measured metric is below the cut after bucket number.
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
        """Alias for `distribution_cut` method to allow for backwards compatibility."""
        warnings.warn(
            "exponential_distribution_cut will be deprecated in version 2.0, "
            "please use distribution_cut instead",
            FutureWarning,
        )
        return self.distribution_cut(*args, **kwargs)

    def count(self, timeseries: List[TimeSeries]) -> int:
        """Count events in time series.

        Args:
            timeseries (list): List of Timeseries objects.

        Returns:
            int: Event count.
        """
        try:
            return self.get_nb_events_from_timeseries(timeseries)
        except (IndexError, AttributeError) as exception:
            LOGGER.debug(exception, exc_info=True)
            return NO_DATA  # No events in timeseries.

    @abstractmethod
    def query(
        self,
        timestamp: float,
        window: int,
        filter_or_query: str,
    ) -> List[TimeSeries]:
        """Query timeseries from Cloud Monitoring.

        Args:
            timestamp (float): Current timestamp.
            window (int): Window size (in seconds).
            filter_or_query (str): Could Monitoring filter or query.

        Returns:
            list: List of timeseries objects.
        """

    @staticmethod
    @abstractmethod
    def get_distribution_value_from_timeseries(
        timeseries: List[TimeSeries],
    ) -> Distribution:
        """Extract a distribution from a list of timeseries.

        Args:
            timeseries (list): List of timeseries.

        Returns:
            :obj:`google.api.distribution_pb2.Distribution`: Distribution.
        """

    @staticmethod
    @abstractmethod
    def get_nb_events_from_timeseries(timeseries: List[TimeSeries]) -> int:
        """Count the events from a list of timeseries.

        Args:
            timeseries (list): List of timeseries.

        Returns:
            int: Number of events.
        """
        return NO_DATA
