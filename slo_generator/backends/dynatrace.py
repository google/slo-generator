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
`dynatrace.py`
Datadog backend implementation.
"""
import json
import logging

import requests

LOGGER = logging.getLogger(__name__)


class DynatraceBackend:
    """Backend for querying metrics from Datadog.

    Args:
        client (obj, optional): Existing `requests.Session` to pass.
        api_url (str): Dynatrace API URL.
        api_token (str): Dynatrace token.
    """
    def __init__(self, client=None, api_url=None, api_token=None):
        self.client = client
        if client is None:
            self.client = DynatraceClient(api_url, api_token)

    def query_sli(self, timestamp, window, slo_config):
        """Query SLI value directly.

        Args:
            timestamp (int): UNIX timestamp.
            window (int): Window (in seconds).
            slo_config (dict): SLO configuration.

        Returns:
            tuple: Good event count, Bad event count.
        """
        conf = slo_config['backend']
        metric_selector = conf['measurement']['metric_selector']
        aggregation = conf['measurement'].get('aggregation', 'AVG')
        start = (timestamp - window) * 1000
        end = timestamp * 1000
        ret = self.query(start, end, metric_selector, aggregation)
        LOGGER.info(ret)

    def query(self, start, end, metric_selector, aggregation='AVG'):
        """Query Dynatrace Metrics V2.

        Args:
            start (int): Start timestamp (in milliseconds).
            end (int): End timestamp (in milliseconds).
            metric_selector (str): Metric selector.
            aggregation (str): Aggregation.

        Returns:
            dict: Dynatrace API response.
        """
        params = {
            'from': start,
            'to': end,
            'metricSelector': metric_selector,
            'aggregation': aggregation,
            'includeData': True
        }
        return self.client.request('get', 'metrics', version='v2', **params)


class DynatraceClient:
    """Small wrapper around requests to query Dynatrace API.

    Args:
        api_url (str): Dynatrace API URL.
        api_token (str): Dynatrace token.
    """
    def __init__(self, api_url, api_key):
        self.client = requests.Session()
        self.url = api_url
        self.token = api_key

    def request(self,
                method,
                endpoint,
                name=None,
                version='v1',
                post_data=None,
                **params):
        """Request Dynatrace API.

        Args:
            method (str): Requests method between ['post', 'put', 'get'].
            endpoint (str): API endpoint.
            name (str): API resource name.
            version (str): API version. Default: v1.
            post_data (dict): JSON data.
            params (dict): Params to send with request.

        Returns:
            obj: API response.
        """
        req = getattr(self.client, method)
        url = f'{self.url}/api/{version}/{endpoint}'
        params['Api-Token'] = self.token
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'User-Agent': 'slo-generator'
        }
        if name:
            url += f'/{name}'
        if method in ['put', 'post']:
            response = req(url, params=params, headers=headers, json=post_data)
        else:
            response = req(url, params=params, headers=headers)
        return DynatraceClient.to_json(response)

    @staticmethod
    def to_json(resp):
        """Decode JSON response from Python requests response as utf-8 and
        replace \n characters.

        Args:
            resp (requests.Response): API response.

        Returns:
            dict: API JSON response.
        """
        res = resp.content.decode('utf-8').replace('\n', '')
        data = json.loads(res)
        if 'error' in data:
            LOGGER.error(f"Dynatrace API returned an error: {data}")
        return data
