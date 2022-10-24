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
`custom_backend.py`
Dummy sample of a custom backend.
"""
import logging

LOGGER = logging.getLogger(__name__)


class CustomBackend:
    """Custom backend that always return an SLI of 0.999."""

    def __init__(self, client=None, **kwargs):
        pass

    # pylint: disable=unused-argument
    def good_bad_ratio(self, timestamp, window, slo_config):
        """Good bad ratio method.

        Args:
            timestamp (str): UNIX timestamp.
            window (str): Window (in seconds).
            slo_config (dict): SLO Config.

        Returns:
            tuple: Good events count / bad events count.
        """
        return 100000, 100

    # pylint: disable=unused-argument,missing-function-docstring
    def query_sli(self, timestamp, window, slo_config):
        return 0.999
