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
`cloud_monitoring.py`
Cloud Monitoring backend implementation.
"""

import logging
import math
import pprint
import warnings
from collections import OrderedDict

from google.cloud import monitoring_v3

from slo_generator.constants import NO_DATA

LOGGER = logging.getLogger(__name__)


def infer_threshold_bucket(bucket_options, threshold_value: float) -> int:
    """Infer the distribution bucket index corresponding to `threshold_value`."""
    target = float(threshold_value)
    exp = getattr(bucket_options, "exponential_buckets", None)
    if exp and getattr(exp, "growth_factor", 0) > 1 and getattr(exp, "scale", 0) > 0:
        if target <= 0:
            return 0
        val = math.log(target / exp.scale, exp.growth_factor)
        rounded = round(val)
        is_close = math.isclose(val, rounded, rel_tol=1e-9, abs_tol=1e-9)
        bucket_idx = rounded if is_close else math.ceil(val)
        num_finite = getattr(exp, "num_finite_buckets", None)
        max_bucket = int(num_finite) + 1 if num_finite is not None else bucket_idx
        return max(0, min(bucket_idx, max_bucket))

    lin = getattr(bucket_options, "linear_buckets", None)
    if lin and getattr(lin, "width", 0) > 0:
        offset = float(getattr(lin, "offset", 0.0))
        width = float(lin.width)
        if target < offset:
            return 0
        val = (target - offset) / width
        rounded = round(val)
        is_close = math.isclose(val, rounded, rel_tol=1e-9, abs_tol=1e-9)
        bucket_idx = rounded if is_close else math.ceil(val)
        num_finite = getattr(lin, "num_finite_buckets", None)
        max_bucket = int(num_finite) + 1 if num_finite is not None else bucket_idx
        return max(0, min(bucket_idx, max_bucket))

    explicit = getattr(bucket_options, "explicit_buckets", None)
    bounds = getattr(explicit, "bounds", None) if explicit else None
    if bounds:
        for idx, bound in enumerate(bounds):
            is_close = math.isclose(bound, target, rel_tol=1e-9, abs_tol=1e-9)
            if bound >= target or is_close:
                return idx
        return len(bounds)

    raise ValueError(
        "Unable to infer threshold_bucket from distribution bucket_options"
    )


def get_threshold_bucket(raw_threshold_bucket, threshold_value, bucket_options) -> int:
    """Get threshold bucket index from raw threshold_bucket or threshold_value."""
    if raw_threshold_bucket is not None:
        if threshold_value is not None:
            LOGGER.warning(
                "Both `threshold_bucket` and `threshold_value` / `value` are "
                "provided. Using `threshold_bucket`."
            )
        return int(raw_threshold_bucket)
    if threshold_value is not None:
        return infer_threshold_bucket(bucket_options, float(threshold_value))
    raise ValueError("Either `threshold_bucket` or `threshold_value` is required.")


class CloudMonitoringBackend:
    """Backend for querying metrics from Cloud Monitoring.

    Args:
        project_id (str): Cloud Monitoring host project id.
        client (google.cloud.monitoring_v3.MetricServiceClient, optional):
            Existing Cloud Monitoring Metrics client. Initialize a new client
            if omitted.
    """

    def __init__(self, project_id, client=None):
        self.client = client
        if client is None:
            self.client = monitoring_v3.MetricServiceClient()
        self.parent = self.client.common_project_path(project_id)

    def good_bad_ratio(self, timestamp, window, slo_config):
        """Query two timeseries, one containing 'good' events, one containing
        'bad' events.

        Args:
            timestamp (int): UNIX timestamp.
            window (int): Window size (in seconds).
            slo_config (dict): SLO configuration.

        Returns:
            tuple: A tuple (good_event_count, bad_event_count)
        """
        measurement = slo_config["spec"]["service_level_indicator"]
        filter_good = measurement["filter_good"]
        filter_bad = measurement.get("filter_bad")
        filter_valid = measurement.get("filter_valid")

        # Query 'good events' timeseries
        good_ts = self.query(
            timestamp=timestamp,
            window=window,
            filter=filter_good,
        )
        good_ts = list(good_ts)
        good_event_count = CM.count(good_ts)

        # Query 'bad events' timeseries
        if filter_bad:
            bad_ts = self.query(
                timestamp=timestamp,
                window=window,
                filter=filter_bad,
            )
            bad_ts = list(bad_ts)
            bad_event_count = CM.count(bad_ts)
        elif filter_valid:
            valid_ts = self.query(
                timestamp=timestamp,
                window=window,
                filter=filter_valid,
            )
            valid_ts = list(valid_ts)
            bad_event_count = CM.count(valid_ts) - good_event_count
        else:
            raise ValueError("One of `filter_bad` or `filter_valid` is required.")

        LOGGER.debug(f"Good events: {good_event_count} | Bad events: {bad_event_count}")

        return good_event_count, bad_event_count

    def distribution_cut(self, timestamp, window, slo_config):
        """Query one timeseries of type 'exponential'.

        Args:
            timestamp (int): UNIX timestamp.
            window (int): Window size (in seconds).
            slo_config (dict): SLO configuration.

        Returns:
            tuple: A tuple (good_event_count, bad_event_count).
        """
        measurement = slo_config["spec"]["service_level_indicator"]
        filter_valid = measurement["filter_valid"]
        raw_threshold_bucket = measurement.get("threshold_bucket")
        threshold_value = measurement.get("threshold_value", measurement.get("value"))
        good_below_threshold = measurement.get("good_below_threshold", True)

        # Query 'valid' events
        series = self.query(
            timestamp=timestamp,
            window=window,
            filter=filter_valid,
        )
        series = list(series)

        if not series:
            return NO_DATA, NO_DATA  # no timeseries

        distribution_value = series[0].points[0].value.distribution_value
        threshold_bucket = get_threshold_bucket(
            raw_threshold_bucket, threshold_value, distribution_value.bucket_options
        )
        bucket_counts = distribution_value.bucket_counts
        valid_events_count = distribution_value.count

        # Explicit the exponential distribution result
        count_sum = 0
        distribution = OrderedDict()
        for i, bucket_count in enumerate(bucket_counts):
            count_sum += bucket_count
            # upper_bound = scale * math.pow(growth_factor, i)
            distribution[i] = {
                # 'upper_bound': upper_bound,
                # 'bucket_count': bucket_count,
                "count_sum": count_sum
            }
        LOGGER.debug(pprint.pformat(distribution))

        if len(distribution) - 1 < threshold_bucket:
            # maximum measured metric is below the cut after bucket number
            lower_events_count = valid_events_count
            upper_events_count = 0
        else:
            lower_events_count = distribution[threshold_bucket]["count_sum"]
            upper_events_count = valid_events_count - lower_events_count

        if good_below_threshold:
            good_event_count = lower_events_count
            bad_event_count = upper_events_count
        else:
            good_event_count = upper_events_count
            bad_event_count = lower_events_count

        return good_event_count, bad_event_count

    def exponential_distribution_cut(self, *args, **kwargs):
        """Alias for `distribution_cut` method to allow for backwards
        compatibility.
        """
        warnings.warn(
            "exponential_distribution_cut will be deprecated in version 2.0, "
            "please use distribution_cut instead",
            FutureWarning,
            stacklevel=2,
        )
        return self.distribution_cut(*args, **kwargs)

    def query(  # noqa: PLR0913
        self,
        timestamp,
        window,
        filter,
        aligner="ALIGN_SUM",
        reducer="REDUCE_SUM",
        group_by=None,
    ):
        """Query timeseries from Cloud Monitoring.

        Args:
            timestamp (int): Current timestamp.
            window (int): Window size (in seconds).
            filter (str): Query filter.
            aligner (str, optional): Aligner to use.
            reducer (str, optional): Reducer to use.
            group_by (list, optional): List of fields to group by.

        Returns:
            list: List of timeseries objects.
        """
        if group_by is None:
            group_by = []
        measurement_window = CM.get_window(timestamp, window)
        aggregation = CM.get_aggregation(
            window, aligner=aligner, reducer=reducer, group_by=group_by
        )
        request = monitoring_v3.ListTimeSeriesRequest()
        request.name = self.parent
        request.filter = filter
        request.interval = measurement_window
        request.view = monitoring_v3.ListTimeSeriesRequest.TimeSeriesView.FULL
        request.aggregation = aggregation
        timeseries = self.client.list_time_series(request)
        LOGGER.debug(pprint.pformat(timeseries))
        return timeseries

    @staticmethod
    def count(timeseries):
        """Count events in time series assuming it was aligned with ALIGN_SUM
        and reduced with REDUCE_SUM (default).

        Args:
            :obj:`monitoring_v3.TimeSeries`: Timeseries object.

        Returns:
            int: Event count.
        """
        try:
            return timeseries[0].points[0].value.int64_value
        except (IndexError, AttributeError) as exception:
            LOGGER.debug(exception, exc_info=True)
            return NO_DATA  # no events in timeseries

    @staticmethod
    def get_window(timestamp, window):
        """Helper for measurement window.

        Args:
            timestamp (int): Current timestamp.
            window (int): Window size (in seconds).

        Returns:
            :obj:`monitoring_v3.types.TimeInterval`: Measurement window object.
        """
        end_time_seconds = int(timestamp)
        end_time_nanos = int((timestamp - end_time_seconds) * 10**9)
        start_time_seconds = int(timestamp - window)
        start_time_nanos = end_time_nanos
        measurement_window = monitoring_v3.TimeInterval(
            {
                "end_time": {
                    "seconds": end_time_seconds,
                    "nanos": end_time_nanos,
                },
                "start_time": {
                    "seconds": start_time_seconds,
                    "nanos": start_time_nanos,
                },
            }
        )
        LOGGER.debug(pprint.pformat(measurement_window))
        return measurement_window

    @staticmethod
    def get_aggregation(
        window,
        aligner="ALIGN_SUM",
        reducer="REDUCE_SUM",
        group_by=None,
    ):
        """Helper for aggregation object.

        Default aggregation is `ALIGN_SUM`.
        Default reducer is `REDUCE_SUM`.

        Args:
            window (int): Window size (in seconds).
            aligner (str): Aligner type.
            reducer (str): Reducer type.
            group_by (list): List of fields to group by.

        Returns:
            :obj:`monitoring_v3.types.Aggregation`: Aggregation object.
        """
        if group_by is None:
            group_by = []
        aggregation = monitoring_v3.Aggregation(
            {
                "alignment_period": {"seconds": window},
                "per_series_aligner": getattr(
                    monitoring_v3.Aggregation.Aligner, aligner
                ),
                "cross_series_reducer": getattr(
                    monitoring_v3.Aggregation.Reducer, reducer
                ),
                "group_by_fields": group_by,
            }
        )
        LOGGER.debug(pprint.pformat(aggregation))
        return aggregation


CM = CloudMonitoringBackend
