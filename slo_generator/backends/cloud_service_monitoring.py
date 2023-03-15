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
`cloud_service_monitoring.py`
Cloud Service Monitoring exporter class.
"""
import difflib
import json
import logging
import os
import warnings
from typing import Optional, Sequence, Union

import google.api_core.exceptions
from google.cloud.monitoring_v3 import ServiceMonitoringServiceClient

# pytype: disable=pyi-error
from google.protobuf.json_format import MessageToJson

from slo_generator.backends.cloud_monitoring import CloudMonitoringBackend
from slo_generator.constants import NO_DATA
from slo_generator.utils import dict_snake_to_caml

# pytype: enable=pyi-error

LOGGER = logging.getLogger(__name__)

SID_GAE: str = "gae:{project_id}_{module_id}"
SID_CLOUD_ENDPOINT: str = "ist:{project_id}-{service}"
SID_CLUSTER_ISTIO: str = (
    "ist:{project_id}-{suffix}-{location}-{cluster_name}-{service_namespace}-"
    "{service_name}"
)
SID_MESH_ISTIO: str = "ist:{mesh_uid}-{service_namespace}-{service_name}"


# pylint: disable=too-many-public-methods
class CloudServiceMonitoringBackend:
    """Cloud Service Monitoring backend class.

    Args:
        project_id (str): Cloud Monitoring host project id.
        client (google.cloud.monitoring_v3.ServiceMonitoringServiceClient):
            Existing Service Monitoring API client. Initialize a new client if
            omitted.
    """

    def __init__(self, project_id: str, client=None):
        self.project_id = project_id
        self.client = client
        if client is None:
            self.client = ServiceMonitoringServiceClient()
        self.parent = self.client.common_project_path(project_id)
        self.workspace_path = f"workspaces/{project_id}"
        self.project_path = f"projects/{project_id}"

    def good_bad_ratio(self, timestamp: int, window: int, slo_config: dict) -> tuple:
        """Good bad ratio method.

        Args:
            timestamp (int): UNIX timestamp.
            window (int): Window in seconds.
            slo_config (dict): SLO configuration.

        Returns:
            tuple: SLO config.
        """
        return self.retrieve_slo(timestamp, window, slo_config)

    def distribution_cut(self, timestamp: int, window: int, slo_config: dict) -> tuple:
        """Distribution cut method.

        Args:
            timestamp (int): UNIX timestamp.
            window (int): Window in seconds.
            slo_config (dict): SLO configuration.

        Returns:
            tuple: SLO config.
        """
        return self.retrieve_slo(timestamp, window, slo_config)

    def basic(self, timestamp: int, window: int, slo_config: dict) -> tuple:
        """Basic method (automatic SLOs for GAE / GKE (Istio) and Cloud
        Endpoints).

        Args:
            timestamp (int): UNIX timestamp.
            window (int): Window in seconds.
            slo_config (dict): SLO configuration.

        Returns:
            tuple: SLO config.
        """
        return self.retrieve_slo(timestamp, window, slo_config)

    def window(self, timestamp: int, window: int, slo_config: dict) -> tuple:
        """Window-based SLI method.

        Args:
            timestamp (int): UNIX timestamp.
            window (int): Window in seconds.
            slo_config (dict): SLO configuration.

        Returns:
            tuple: SLO config.
        """
        return self.retrieve_slo(timestamp, window, slo_config)

    # pylint: disable=unused-argument
    def delete(self, timestamp: int, window: int, slo_config: dict) -> Optional[dict]:
        """Delete method.

        Args:
            timestamp (int): UNIX timestamp.
            window (int): Window in seconds.
            slo_config (dict): SLO configuration.

        Returns:
            dict: SLO config.
        """
        return self.delete_slo(window, slo_config)

    def retrieve_slo(self, timestamp: int, window: int, slo_config: dict):
        """Get SLI value from Cloud Monitoring API.

        Args:
            timestamp (int): UNIX timestamp.
            window (int): Window in seconds.
            slo_config (dict): SLO configuration.

        Returns:
            dict: SLO config.
        """
        # Get or create service
        service = self.get_service(slo_config)
        if service is None:
            service = self.create_service(slo_config)
        LOGGER.debug(service)

        # Get or create SLO
        slo = self.get_slo(window, slo_config)
        if not slo:
            slo = self.create_slo(window, slo_config)
        LOGGER.debug(service)

        # Now that we have our SLO, retrieve the TimeSeries from Cloud
        # Monitoring API for that particular SLO id.
        metric_filter = self.build_slo_id(window, slo_config, full=True)
        # pylint: disable=redefined-builtin
        filter = f'select_slo_counts("{metric_filter}")'

        # Query SLO timeseries
        cloud_monitoring = CloudMonitoringBackend(self.project_id)
        timeseries = cloud_monitoring.query(
            timestamp,
            window,
            filter,
            aligner="ALIGN_SUM",
            reducer="REDUCE_SUM",
            group_by=["metric.labels.event_type"],
        )
        timeseries = list(timeseries)
        good_event_count, bad_event_count = SSM.count(timeseries)
        return (good_event_count, bad_event_count)

    @staticmethod
    def count(timeseries: list):
        """Extract good_count, bad_count tuple from Cloud Monitoring API
        response.

        Args:
            timeseries (list): List of timeseries objects.

        Returns:
            tuple: A tuple (good_event_count, bad_event_count).
        """
        good_event_count, bad_event_count = NO_DATA, NO_DATA
        for timeserie in timeseries:
            event_type = timeserie.metric.labels["event_type"]
            value = timeserie.points[0].value.double_value
            if event_type == "bad":
                bad_event_count = value
            elif event_type == "good":
                good_event_count = value
        return good_event_count, bad_event_count

    def create_service(self, slo_config: dict) -> dict:
        """Create Service object in Cloud Service Monitoring API.

        Args:
            slo_config (dict): SLO configuration.

        Returns:
            dict: Cloud Service Monitoring API response.
        """
        LOGGER.debug("Creating service ...")
        service_json = self.build_service(slo_config)
        service_id = self.build_service_id(slo_config)
        service = self.client.create_service(
            request={
                "parent": self.project_path,
                "service": service_json,
                "service_id": service_id,
            }
        )
        LOGGER.info(
            f'Service "{service_id}" created successfully in Cloud '
            f"Service Monitoring API."
        )
        return SSM.to_json(service)

    def get_service(self, slo_config: dict) -> Optional[dict]:
        """Get Service object from Cloud Service Monitoring API.

        Args:
            slo_config (dict): SLO configuration.

        Returns:
            dict: Service config.
        """

        # Look for API services in workspace matching our config.
        service_id = self.build_service_id(slo_config)
        services = list(
            self.client.list_services(
                request={
                    "parent": self.workspace_path,
                }
            )
        )
        matches = [
            service for service in services if service.name.split("/")[-1] == service_id
        ]

        # If no match is found for our service name in the API, raise an
        # exception if the service should have been auto-added (method 'basic'),
        # else output a warning message.
        if not matches:
            msg = (
                f'Service "{service_id}" does not exist in '
                f'workspace "{self.project_id}"'
            )
            method = slo_config["spec"]["method"]
            if method == "basic":
                sids = [service.name.split("/")[-1] for service in services]
                LOGGER.debug(f"List of services in workspace {self.project_id}: {sids}")
                raise ValueError(msg)
            LOGGER.error(msg)
            return None

        # Match found in API, return it.
        service = matches[0]
        LOGGER.debug(f'Found matching service "{service.name}"')
        return SSM.to_json(service)

    def build_service(self, slo_config: dict) -> dict:
        """Build service JSON in Cloud Monitoring API from SLO
        configuration.

        Args:
            slo_config (dict): SLO configuration.

        Returns:
            dict: Service JSON in Cloud Monitoring API.
        """
        service_id = self.build_service_id(slo_config)
        display_name = slo_config.get("service_display_name", service_id)
        return {"display_name": display_name, "custom": {}}

    def build_service_id(
        self,
        slo_config: dict,
        dest_project_id: Optional[str] = None,
        full: bool = False,
    ):
        """Build service id from SLO configuration.

        Args:
            slo_config (dict): SLO configuration.
            dest_project_id (str, optional): Project id for service if different
                than the workspace project id.
            full (bool): If True, return full service resource id including
                project path.

        Returns:
            str: Service id.
        """
        project_id = self.project_id
        measurement = slo_config["spec"]["service_level_indicator"]
        app_engine = measurement.get("app_engine")
        cluster_istio = measurement.get("cluster_istio")
        mesh_istio = measurement.get("mesh_istio")
        cloud_endpoints = measurement.get("cloud_endpoints")

        # Use auto-generated ids for 'custom' SLOs, use system-generated ids
        # for all other types of SLOs.
        if app_engine:
            service_id = SID_GAE.format_map(app_engine)
            dest_project_id = app_engine["project_id"]
        elif cluster_istio:
            warnings.warn(
                "ClusterIstio is deprecated in the Service Monitoring API."
                "It will be removed in version 3.0, please use MeshIstio "
                "instead",
                FutureWarning,
            )
            if "zone" in cluster_istio:
                cluster_istio["suffix"] = "zone"
                cluster_istio["location"] = cluster_istio["zone"]
            elif "location" in cluster_istio:
                cluster_istio["suffix"] = "location"
            service_id = SID_CLUSTER_ISTIO.format_map(cluster_istio)
            dest_project_id = cluster_istio["project_id"]
        elif mesh_istio:
            service_id = SID_MESH_ISTIO.format_map(mesh_istio)
        elif cloud_endpoints:
            service_id = SID_CLOUD_ENDPOINT.format_map(cloud_endpoints)
            dest_project_id = cluster_istio["project_id"]
        else:  # user-defined service id
            service_name = slo_config["metadata"]["labels"].get("service_name", "")
            feature_name = slo_config["metadata"]["labels"].get("feature_name", "")
            service_id = slo_config["spec"]["service_level_indicator"].get("service_id")
            if not service_id:
                if not service_name or not feature_name:
                    raise ValueError(
                        "Service id not set in SLO configuration. Please set "
                        "either `spec.service_level_indicator.service_id` or "
                        "both `metadata.labels.service_name` and "
                        "`metadata.labels.feature_name` in your SLO "
                        "configuration."
                    )
                service_id = f"{service_name}-{feature_name}"

        if full:
            if dest_project_id:
                return f"projects/{dest_project_id}/services/{service_id}"
            return f"projects/{project_id}/services/{service_id}"

        return service_id

    def create_slo(self, window: int, slo_config: dict) -> dict:
        """Create SLO object in Cloud Service Monitoring API.

        Args:
            window (int): Window (in seconds).
            slo_config (dict): SLO config.

        Returns:
            dict: Service Management API response.
        """
        slo_json = SSM.build_slo(window, slo_config)
        slo_id = self.build_slo_id(window, slo_config)
        parent = self.build_service_id(slo_config, full=True)
        slo = self.client.create_service_level_objective(
            request={
                "parent": parent,
                "service_level_objective": slo_json,
                "service_level_objective_id": slo_id,
            }
        )
        return SSM.to_json(slo)

    # pylint: disable=R0912,R0915
    @staticmethod
    # pylint: disable=R0912,R0915,too-many-locals
    def build_slo(window: int, slo_config: dict) -> dict:
        """Get SLO JSON representation in Cloud Service Monitoring API from SLO
        configuration.

        Args:
            window (int): Window (in seconds).
            slo_config (dict): SLO Configuration.

        Returns:
            dict: SLO JSON configuration.
        """
        measurement = slo_config["spec"].get("service_level_indicator", {})
        method = slo_config["spec"]["method"]
        description = slo_config["spec"]["description"]
        goal = slo_config["spec"]["goal"]
        minutes, _ = divmod(window, 60)
        hours, _ = divmod(minutes, 60)
        display_name = f"{description} ({hours}h)"
        slo = {
            "display_name": display_name,
            "goal": goal,
            "rolling_period": {"seconds": window},
        }
        filter_valid = measurement.get("filter_valid", "")
        if method == "basic":
            methods = measurement.get("method", [])
            locations = measurement.get("location", [])
            versions = measurement.get("version", [])
            threshold = measurement.get("latency", {}).get("threshold")
            slo["service_level_indicator"] = {"basic_sli": {}}
            basic_sli = slo["service_level_indicator"]["basic_sli"]
            if methods:
                basic_sli["method"] = methods
            if locations:
                basic_sli["location"] = locations
            if versions:
                basic_sli["version"] = versions
            if threshold:
                basic_sli["latency"] = {
                    "threshold": {
                        "seconds": 0,
                        "nanos": int(threshold) * 10**6,
                    }
                }
            else:
                basic_sli["availability"] = {}

        elif method == "good_bad_ratio":
            filter_good = measurement.get("filter_good", "")
            filter_bad = measurement.get("filter_bad", "")
            slo["service_level_indicator"] = {
                "request_based": {
                    "good_total_ratio": {},
                }
            }
            sli = slo["service_level_indicator"]
            ratio = sli["request_based"]["good_total_ratio"]
            if filter_good:
                ratio["good_service_filter"] = filter_good
            if filter_bad:
                ratio["bad_service_filter"] = filter_bad
            if filter_valid:
                ratio["total_service_filter"] = filter_valid

        elif method == "distribution_cut":
            range_min = measurement.get("range_min", 0)
            range_max = measurement["range_max"]
            slo["service_level_indicator"] = {
                "request_based": {
                    "distribution_cut": {
                        "distribution_filter": filter_valid,
                        "range": {
                            "max": float(range_max),
                        },
                    }
                }
            }
            sli = slo["service_level_indicator"]["request_based"]
            if range_min != 0:
                sli["distribution_cut"]["range"]["min"] = float(range_min)

        elif method == "windows":
            # pylint: disable=redefined-builtin
            filter = measurement.get("filter")
            # threshold = conf.get('threshold')
            # mean_in_range = conf.get('filter')
            # sum_in_range = conf.get('filter')
            slo["service_level_indicator"] = {
                "windows_based": {
                    "window_period": window,
                    "good_bad_metric_filter": filter,
                    # 'good_total_ratio_threshold': {
                    #   object (PerformanceThreshold)
                    # },
                    # 'metricMeanInRange': {
                    #   object (MetricRange)
                    # },
                    # 'metricSumInRange': {
                    #   object (MetricRange)
                    # }
                }
            }
        else:
            raise ValueError(f'Method "{method}" is not supported.')
        return slo

    def get_slo(self, window: int, slo_config: dict) -> Optional[dict]:
        """Get SLO object from Cloud Service Monssitoring API.

        Args:
            window (int): Window in seconds.
            slo_config (dict): SLO config.

        Returns:
            dict: API response.
        """
        service_path = self.build_service_id(slo_config, full=True)
        LOGGER.debug(f'Getting SLO for for "{service_path}" ...')
        slos = self.list_slos(service_path)
        slo_local_id = self.build_slo_id(window, slo_config)
        slo_json = SSM.build_slo(window, slo_config)
        slo_json = SSM.convert_slo_to_ssm_format(slo_json)

        # Loop through API response to find an existing SLO that corresponds to
        # our configuration.
        for slo in slos:
            slo_remote_id = slo["name"].split("/")[-1]
            equal = slo_remote_id == slo_local_id
            if equal:
                LOGGER.debug(f'Found existing SLO "{slo_remote_id}".')
                LOGGER.debug(f"SLO object: {slo}")
                strict_equal = SSM.compare_slo(slo_json, slo)
                if strict_equal:
                    return slo
                return self.update_slo(window, slo_config)
        LOGGER.warning("No SLO found matching configuration.")
        LOGGER.debug(f"SLOs from Cloud Service Monitoring API: {slos}")
        LOGGER.debug(f"SLO config converted: {slo_json}")
        return None

    def update_slo(self, window: int, slo_config: dict) -> dict:
        """Update an existing SLO.

        Args:
            window (int): Window (in seconds)
            slo_config (dict): SLO configuration.

        Returns:
            dict: API response.
        """
        slo_json = SSM.build_slo(window, slo_config)
        slo_id = self.build_slo_id(window, slo_config, full=True)
        LOGGER.warning(f"Updating SLO {slo_id} ...")
        slo_json["name"] = slo_id
        return SSM.to_json(
            self.client.update_service_level_objective(
                request={
                    "service_level_objective": slo_json,
                }
            )
        )

    def list_slos(self, service_path: str) -> list:
        """List all SLOs from Cloud Service Monitoring API.

        Args:
            service_path (str): Service path in the form
                'projects/{project_id}/services/{service_id}'.

        Returns:
            list: API response.
        """
        slos = self.client.list_service_level_objectives(
            request={
                "parent": service_path,
            }
        )
        slos = list(slos)
        LOGGER.debug(f"{len(slos)} SLOs found in Cloud Service Monitoring API.")
        # LOGGER.debug(slos)
        return [SSM.to_json(slo) for slo in slos]

    def delete_slo(self, window: int, slo_config: dict) -> Optional[dict]:
        """Delete SLO from Cloud Service Monitoring API.

        Args:
            window (int): Window (in seconds).
            slo_config: SLO configuration.

        Returns:
            dict: API response.
        """
        slo_path = self.build_slo_id(window, slo_config, full=True)
        LOGGER.info(f'Deleting SLO "{slo_path}"')
        try:
            return self.client.delete_service_level_objective(
                request={
                    "name": slo_path,
                }
            )
        except google.api_core.exceptions.NotFound:
            LOGGER.warning(
                f'SLO "{slo_path}" does not exist in Service Monitoring API. '
                f"Skipping."
            )
            return None

    def build_slo_id(self, window: int, slo_config: dict, full: bool = False) -> str:
        """Build SLO id from SLO configuration.

        Args:
            slo_config (dict): SLO configuration.
            full (bool): If True, return full resource id including project.

        Returns:
            str: SLO id.
        """
        sli = slo_config["spec"]["service_level_indicator"]
        slo_name = slo_config["metadata"]["labels"].get("slo_name")
        slo_id = sli.get("slo_id", slo_name)
        if not slo_id:
            raise ValueError(
                "SLO id not set in SLO configuration. Please set either "
                "`spec.service_level_indicator.slo_id` or "
                "`metadata.labels.slo_name` in your SLO configuration."
            )
        full_slo_id = f"{slo_id}-{window}"
        if full:
            service_path = self.build_service_id(slo_config, full=True)
            return f"{service_path}/serviceLevelObjectives/{full_slo_id}"
        return full_slo_id

    @staticmethod
    def compare_slo(slo1: dict, slo2: dict) -> bool:
        """Compares 2 SLO configurations to see if they correspond to the same
        SLO.

        An SLO is deemed the same if the whole configuration is similar, except
        for the `goal` field that should be adjustable.

        Args:
            slo1 (dict): Service Monitoring API SLO configuration to compare.
            slo2 (dict): Service Monitoring API SLO configuration to compare.

        Returns:
            bool: True if the SLOs match, False otherwise.
        """
        exclude_keys = ["name"]
        slo1_copy = {k: v for k, v in slo1.items() if k not in exclude_keys}
        slo2_copy = {k: v for k, v in slo2.items() if k not in exclude_keys}
        local_json = json.dumps(slo1_copy, sort_keys=True)
        remote_json = json.dumps(slo2_copy, sort_keys=True)
        if os.environ.get("DEBUG") == "2":
            LOGGER.info("----------")
            LOGGER.info(local_json)
            LOGGER.info("----------")
            LOGGER.info(remote_json)
            LOGGER.info("----------")
            LOGGER.info(SSM.string_diff(local_json, remote_json))
        return local_json == remote_json

    @staticmethod
    def string_diff(
        string1: Union[str, Sequence[str]], string2: Union[str, Sequence[str]]
    ) -> list:
        """Diff 2 strings. Used to print comparison of JSONs for debugging.

        Args:
            string1 (str): String 1.
            string2 (str): String 2.

        Returns:
            list: List of messages pointing out differences.
        """
        lines = []
        for idx, string in enumerate(difflib.ndiff(string1, string2)):
            if string[0] == " ":
                continue
            last = string[-1]
            if string[0] == "-":
                info = f'Delete "{last}" from position {idx}'
                lines.append(info)
            elif string[0] == "+":
                info = f'Add "{last}" to position {idx}'
                lines.append(info)
        return lines

    @staticmethod
    def convert_slo_to_ssm_format(slo: dict) -> dict:
        """Convert SLO JSON to Cloud Service Monitoring API format.
        Address edge cases, like `duration` object computation.

        Args:
            slo (dict): SLO JSON object to be converted to Cloud Service
                Monitoring API format.

        Returns:
            dict: SLO configuration in Cloud Service Monitoring API format.
        """
        # Our local JSON is in snake case, convert it to Caml case.
        data = dict_snake_to_caml(slo)

        # The `rollingPeriod` field is in Duration format, convert it.
        try:
            period = data["rollingPeriod"]
            data["rollingPeriod"] = SSM.convert_duration_to_string(period)
        except KeyError:
            pass

        # The `latency` field is in Duration format, convert it.
        try:
            latency = data["serviceLevelIndicator"]["basicSli"]["latency"]
            threshold = latency["threshold"]
            latency["threshold"] = SSM.convert_duration_to_string(threshold)
        except KeyError:
            pass

        return data

    @staticmethod
    def convert_duration_to_string(duration):
        """Convert a duration object to a duration string (in seconds).

        Args:
            duration (dict): Duration dictionary.

        Returns:
            str: Duration string.
        """
        duration_seconds = 0.000
        if "seconds" in duration:
            duration_seconds += duration["seconds"]
        if "nanos" in duration:
            duration_seconds += duration["nanos"] * 10 ** (-9)
        if duration_seconds.is_integer():
            duration_str = int(duration_seconds)
        else:
            duration_str = f"{duration_seconds:0.3f}"
        return str(duration_str) + "s"

    @staticmethod
    def to_json(response):
        """Convert a Cloud Service Monitoring API response to JSON
        format.

        Args:
            response (obj): Response object.

        Returns:
            dict: Response object serialized as JSON.
        """
        # pylint: disable=protected-access
        return json.loads(MessageToJson(response._pb))


SSM = CloudServiceMonitoringBackend
