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

from slo_generator.backends.cloud_monitoring_mql import \
    CloudMonitoringMqlBackend


class TestCloudMonitoringMqlBackend(unittest.TestCase):

    def test_fmt_query(self):
        # pylint: disable=trailing-whitespace
        queries = [
            '''  fetch gae_app
      | metric 'appengine.googleapis.com/http/server/response_count'
      | filter resource.project_id == '${GAE_PROJECT_ID}'
      | filter
          metric.response_code == 429
          || metric.response_code == 200
      | group_by [metric.response_code] | within 1h   ''',

            ''' fetch gae_app
      | metric 'appengine.googleapis.com/http/server/response_count'
      | filter resource.project_id == '${GAE_PROJECT_ID}'
      | filter
          metric.response_code == 429
          || metric.response_code == 200
      | group_by [metric.response_code,  response_code_class]
      | within 1h   
      | every 1h  ''',

            ''' fetch gae_app
      | metric 'appengine.googleapis.com/http/server/response_count'
      | filter resource.project_id == '${GAE_PROJECT_ID}'
      | filter
          metric.response_code == 429
          || metric.response_code == 200
      | group_by [metric.response_code,response_code_class]  
      | within 1h
      | every 1h ''',
        ]
        # pylint: enable=trailing-whitespace

        formatted_query = '''fetch gae_app
      | metric 'appengine.googleapis.com/http/server/response_count'
      | filter resource.project_id == '${GAE_PROJECT_ID}'
      | filter
          metric.response_code == 429
          || metric.response_code == 200
      | group_by [] | within 3600s | every 3600s'''

        for query in queries:
            assert CloudMonitoringMqlBackend._fmt_query(query,
                                                        3600) == formatted_query
