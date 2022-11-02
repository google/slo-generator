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
`cloud_monitoring_mql.py`
Cloud Monitoring backend implementation with MQL (Monitoring Query Language).
"""
import logging
import pprint
from datetime import datetime
from typing import List

from google.api.distribution_pb2 import Distribution
from google.cloud.monitoring_v3 import QueryTimeSeriesRequest
from google.cloud.monitoring_v3.services.query_service import QueryServiceClient
from google.cloud.monitoring_v3.services.query_service.pagers import (
    QueryTimeSeriesPager,
)
from google.cloud.monitoring_v3.types.metric import TimeSeries

from .cloud_monitoring_abc import CloudMonitoringBackendABC

LOGGER = logging.getLogger(__name__)


class CloudMonitoringMqlBackend(CloudMonitoringBackendABC):
    """Backend for querying metrics from Cloud Monitoring with MQL.

    Args:
        project_id (str): Cloud Monitoring host project id.
        client (monitoring_v3.services.query_service.QueryServiceClient, optional):
            Existing Cloud Monitoring Query client. Initialize a new client if omitted.
    """

    def __init__(self, project_id: str, client=None):
        self.client = client
        if client is None:
            self.client = QueryServiceClient()
        self.parent = self.client.common_project_path(project_id)

    def query_sli(
        self,
        timestamp: float,
        window: int,
        slo_config: dict,
    ) -> float:
        """Query SLI value from a given MQL query.

        Args:
            timestamp (float): UNIX timestamp.
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

    def query(
        self,
        timestamp: float,
        window: int,
        filter_or_query: str,
    ) -> List[TimeSeries]:
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
            self.enrich_query_with_time_horizon_and_period(
                timestamp, window, filter_or_query
            )
        )
        request = QueryTimeSeriesRequest(
            {
                "name": self.parent,
                "query": query_with_time_horizon_and_period,
            }
        )
        timeseries_pager: QueryTimeSeriesPager = self.client.query_time_series(request)
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
        end_time_str: str = datetime.fromtimestamp(timestamp).strftime(
            "%Y/%m/%d %H:%M:%S"
        )
        query_with_time_horizon_and_period: str = (
            query
            + f"| group_by [] | within {window}s, d'{end_time_str}' | every {window}s"
        )
        return query_with_time_horizon_and_period

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
        return timeseries[0].point_data[0].values[0].distribution_value

    @staticmethod
    def get_nb_events_from_timeseries(timeseries: List[TimeSeries]) -> int:
        """Count the events from a list of timeseries.

        Args:
            timeseries (list): List of timeseries.

        Returns:
            int: Number of events.
        """
        return timeseries[0].point_data[0].values[0].int64_value
