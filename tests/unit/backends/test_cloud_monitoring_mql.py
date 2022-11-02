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

# flake8: noqa

import unittest

from slo_generator.backends.cloud_monitoring_mql import CloudMonitoringMqlBackend


class TestCloudMonitoringMqlBackend(unittest.TestCase):
    def test_enrich_query_with_time_horizon_and_period(self):
        timestamp: float = 1666995015.5144777  # = 2022/10/28 22:10:15.5144777
        window: int = 3600  # in seconds
        query: str = """fetch gae_app
| metric 'appengine.googleapis.com/http/server/response_count'
| filter resource.project_id == 'slo-generator-demo'
| filter
    metric.response_code == 429
    || metric.response_code == 200
"""

        enriched_query = """fetch gae_app
| metric 'appengine.googleapis.com/http/server/response_count'
| filter resource.project_id == 'slo-generator-demo'
| filter
    metric.response_code == 429
    || metric.response_code == 200
| group_by [] | within 3600s, d'2022/10/28 22:10:15' | every 3600s"""

        assert (
            CloudMonitoringMqlBackend.enrich_query_with_time_horizon_and_period(
                timestamp, window, query
            )
            == enriched_query
        )
