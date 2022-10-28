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
`constants.py`
Constants and environment variables used in `slo-generator`.
"""
import os
from typing import Dict, List, Tuple

# Compute
NO_DATA: int = -1
MIN_VALID_EVENTS: int = int(os.environ.get("MIN_VALID_EVENTS", "1"))

# Global
LATEST_MAJOR_VERSION: str = "v2"
COLORED_OUTPUT: int = int(os.environ.get("COLORED_OUTPUT", "0"))
DRY_RUN: bool = bool(int(os.environ.get("DRY_RUN", "0")))
DEBUG: int = int(os.environ.get("DEBUG", "0"))

# Exporters supporting v2 SLO report format
V2_EXPORTERS: Tuple[str, ...] = ("Pubsub", "Cloudevent")

# Config skeletons
CONFIG_SCHEMA: dict = {
    "backends": {},
    "exporters": {},
    "error_budget_policies": {},
}
SLO_CONFIG_SCHEMA: dict = {
    "apiVersion": "",
    "kind": "",
    "metadata": {},
    "spec": {
        "description": "",
        "backend": "",
        "method": "",
        "exporters": [],
        "service_level_indicator": {},
    },
}

# Providers that have changed with v2 YAML config format. This mapping helps
# migrate them to their updated names.
PROVIDERS_COMPAT: Dict[str, str] = {
    "Stackdriver": "CloudMonitoring",
    "StackdriverServiceMonitoring": "CloudServiceMonitoring",
}

# Fields that have changed name with v2 YAML config format. This mapping helps
# migrate them back to their former name, so that exporters are backward-
# compatible with v1.
METRIC_LABELS_COMPAT: Dict[str, str] = {
    "goal": "slo_target",
    "description": "slo_description",
    "error_budget_burn_rate_threshold": "alerting_burn_rate_threshold",
}

# Fields that used to be specified in top-level of YAML config are now specified
# in metadata fields. This mapping helps migrate them back to the top level when
# exporting reports, so that exporters are backward-compatible with v1.
METRIC_METADATA_LABELS_TOP_COMPAT: List[str] = [
    "service_name",
    "feature_name",
    "slo_name",
]


# Colors / Status
# pylint: disable=too-few-public-methods
class Colors:
    """Colors for console output."""

    HEADER: str = "\033[95m"
    OKBLUE: str = "\033[94m"
    OKGREEN: str = "\033[92m"
    WARNING: str = "\033[93m"
    FAIL: str = "\033[91m"
    ENDC: str = "\033[0m"
    BOLD: str = "\033[1m"
    UNDERLINE: str = "\033[4m"


GREEN: str = Colors.OKGREEN
RED: str = Colors.FAIL
ENDC: str = Colors.ENDC
BOLD: str = Colors.BOLD
WARNING: str = Colors.WARNING
FAIL: str = "❌"
SUCCESS: str = "✅"
RIGHT_ARROW: str = "➞"
