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

# Compute
NO_DATA = -1
MIN_VALID_EVENTS = int(os.environ.get("MIN_VALID_EVENTS", "1"))

# Global
LATEST_MAJOR_VERSION = 'v2'
COLORED_OUTPUT = int(os.environ.get("COLORED_OUTPUT", "0"))
DRY_RUN = bool(int(os.environ.get("DRY_RUN", "0")))
DEBUG = int(os.environ.get("DEBUG", "0"))

# Config skeletons
CONFIG_SCHEMA = {
    'backends': {},
    'exporters': {},
    'error_budget_policies': {},
}
SLO_CONFIG_SCHEMA = {
    'apiVersion': '',
    'kind': '',
    'metadata': {},
    'spec': {
        'description': '',
        'backend': '',
        'method': '',
        'exporters': [],
        'service_level_indicator': {}
    }
}

# Providers that have changed with v2 YAML config format. This mapping helps
# migrate them to their updated names.
PROVIDERS_COMPAT = {
    'Stackdriver': 'CloudMonitoring',
    'StackdriverServiceMonitoring': 'CloudServiceMonitoring'
}

# Fields that have changed name with v2 YAML config format. This mapping helps
# migrate them back to their former name, so that exporters are backward-
# compatible with v1.
METRIC_LABELS_COMPAT = {
    'goal': 'slo_target',
    'description': 'slo_description',
    'burn_rate_threshold': 'alerting_burn_rate_threshold'
}

# Fields that used to be specified in top-level of YAML config are now specified
# in metadata fields. This mapping helps migrate them back to the top level when
# exporting reports, so that so that exporters are backward-compatible with v1.
METRIC_METADATA_LABELS_TOP_COMPAT = ['service_name', 'feature_name', 'slo_name']


# Colors / Status
# pylint: disable=too-few-public-methods
class Colors:
    """Colors for console output."""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


GREEN = Colors.OKGREEN
RED = Colors.FAIL
ENDC = Colors.ENDC
BOLD = Colors.BOLD
WARNING = Colors.WARNING
FAIL = '❌'
SUCCESS = '✅'
RIGHT_ARROW = '➞'
