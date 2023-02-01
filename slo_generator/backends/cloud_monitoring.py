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
Cloud Monitoring backend implementation with MQF (Monitoring Query Filters).
"""
import logging
import pprint
from typing import List, Optional

from google.api.distribution_pb2 import Distribution
from google.cloud.monitoring_v3 import Aggregation, ListTimeSeriesRequest, TimeInterval
from google.cloud.monitoring_v3.services.metric_service import MetricServiceClient
from google.cloud.monitoring_v3.services.metric_service.pagers import (
    ListTimeSeriesPager,
)
from google.cloud.monitoring_v3.types.metric import TimeSeries

from .cloud_monitoring_abc import CloudMonitoringBackendABC

LOGGER = logging.getLogger(__name__)


class CloudMonitoringBackend(CloudMonitoringBackendABC):
    """Backend for querying metrics from Cloud Monitoring with MQF.

    Args:
        project_id (str): Cloud Monitoring host project id.
        client (monitoring_v3.services.query_service.MetricServiceClient, optional):
            Existing Cloud Monitoring Metrics client. Initialize a new client if
            omitted.
    """

    def __init__(self, project_id: str, client=None):
        self.client = client
        if client is None:
            self.client = MetricServiceClient()
        self.parent = self.client.common_project_path(project_id)

    # pylint: disable=redefined-builtin,too-many-arguments
    def query(
        self,
        timestamp: float,
        window: int,
        filter_or_query: str,
        aligner: str = "ALIGN_SUM",
        reducer: str = "REDUCE_SUM",
        group_by: Optional[List[str]] = None,
    ) -> List[TimeSeries]:
        """Query timeseries from Cloud Monitoring using MQF.

        Args:
            timestamp (float): Current timestamp.
            window (int): Window size (in seconds).
            filter_or_query (str): Query filter.
            aligner (str, optional): Aligner to use.
            reducer (str, optional): Reducer to use.
            group_by (list, optional): List of fields to group by.

        Returns:
            list: List of timeseries objects.
        """
        if group_by is None:
            group_by = []
        measurement_window = self.get_window(timestamp, window)
        aggregation = self.get_aggregation(window, aligner, reducer, group_by)
        request = ListTimeSeriesRequest(
            {
                "name": self.parent,
                "filter": filter_or_query,
                "interval": measurement_window,
                "view": ListTimeSeriesRequest.TimeSeriesView.FULL,
                "aggregation": aggregation,
            }
        )
        timeseries_pager: ListTimeSeriesPager = self.client.list_time_series(request)
        timeseries: List[TimeSeries] = list(timeseries_pager)
        LOGGER.debug(pprint.pformat(timeseries))
        return timeseries

    @staticmethod
    def get_window(
        timestamp: float,
        window: int,
    ) -> TimeInterval:
        """Helper for measurement window.

        Args:
            timestamp (float): Current timestamp.
            window (int): Window size (in seconds).

        Returns:
            :obj:`monitoring_v3.TimeInterval`: Measurement window object.
        """
        end_time_seconds = int(timestamp)
        end_time_nanos = int((timestamp - end_time_seconds) * 10**9)
        start_time_seconds = int(timestamp - window)
        start_time_nanos = end_time_nanos
        measurement_window = TimeInterval(
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
        window: int,
        aligner: str = "ALIGN_SUM",
        reducer: str = "REDUCE_SUM",
        group_by: Optional[List[str]] = None,
    ) -> Aggregation:
        """Helper for aggregation object.

        Default aggregation is `ALIGN_SUM`.
        Default reducer is `REDUCE_SUM`.

        Args:
            window (int): Window size (in seconds).
            aligner (str): Aligner type.
            reducer (str): Reducer type.
            group_by (list, optional): List of fields to group by.

        Returns:
            :obj:`monitoring_v3.Aggregation`: Aggregation object.
        """
        if group_by is None:
            group_by = []
        aggregation = Aggregation(
            {
                "alignment_period": {"seconds": window},
                "per_series_aligner": getattr(Aggregation.Aligner, aligner),
                "cross_series_reducer": getattr(Aggregation.Reducer, reducer),
                "group_by_fields": group_by,
            }
        )
        LOGGER.debug(pprint.pformat(aggregation))
        return aggregation

    @staticmethod
    def get_distribution_value_from_timeseries(
        timeseries: List[TimeSeries],
    ) -> Distribution:
        """Extract a distribution from a list of timeseries.

        Args:
            timeseries (list): List of timeseries.

        Returns:
            :obj:`google.api.distribution_pb2.Distribution`: Distribution.
        """
        return timeseries[0].points[0].value.distribution_value

    @staticmethod
    def get_nb_events_from_timeseries(timeseries: List[TimeSeries]) -> int:
        """Count the events from a list of timeseries.

        Args:
            timeseries (list): List of timeseries.

        Returns:
            int: Number of events.
        """
        return timeseries[0].points[0].value.int64_value
