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
import pprint

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

    def good_bad_ratio(self, timestamp, window, slo_config):
        """Query SLI value from good and valid queries.

        Args:
            timestamp (int): UNIX timestamp.
            window (int): Window (in seconds).
            slo_config (dict): SLO configuration.

        Returns:
            tuple: Good event count, Bad event count.
        """
        conf = slo_config['backend']
        measurement = conf['measurement']
        start = (timestamp - window) * 1000
        end = timestamp * 1000
        query_good = measurement['query_good']
        query_valid = measurement['query_valid']

        # Good query
        good_event_response = self.query(start=start, end=end, **query_good)
        LOGGER.debug(f"Result good: {pprint.pformat(good_event_response)}")
        good_event_count = DynatraceBackend.count(good_event_response)

        # Good query
        valid_event_response = self.query(start=start, end=end, **query_valid)
        LOGGER.debug(f"Result valid: {pprint.pformat(valid_event_response)}")
        valid_event_count = DynatraceBackend.count(valid_event_response)

        # Return good, bad
        bad_event_count = valid_event_count - good_event_count
        return (good_event_count, bad_event_count)

    def query(self, start, end, timeseries_id, aggregation='AVG'):
        """Query Dynatrace Metrics V1.

        Args:
            start (int): Start timestamp (in milliseconds).
            end (int): End timestamp (in milliseconds).
            timeseries_id (str): Timeseries id.
            entity (str): Entity selector.
            aggregation (str): Aggregation.

        Returns:
            dict: Dynatrace API response.
        """
        params = {
            'startTimestamp': start,
            'endTimestamp': end,
            'aggregationType': aggregation,
            'includeData': True
        }
        return self.client.request('get',
                                   'timeseries',
                                   timeseries_id,
                                   version='v1',
                                   **params)

    @staticmethod
    def count(response):
        """Count events in time series data.

        Args:
            response (dict): Dynatrace API response.

        Returns:
            int: Event count.
        """
        try:
            datapoints = response['dataResult']['dataPoints']
            timeseries = list(datapoints.values())
            values = []
            for datapoints_sets in timeseries:
                set_values = [
                    datapoint[1] for datapoint in datapoints_sets
                    if datapoint[1] is not None and datapoint[1] > 0
                ]
                values.extend(set_values)
            return sum(values) / len(values)
        except (IndexError, AttributeError, ZeroDivisionError) as exception:
            LOGGER.warning("Couldn't find any values in timeseries response")
            LOGGER.debug(exception)
            return 0  # no events in timeseries


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
        params_str = "&".join("%s=%s" % (k, v) for k, v in params.items())
        url += f'?{params_str}'
        if method in ['put', 'post']:
            response = req(url, headers=headers, json=post_data)
        else:
            response = req(url, headers=headers)
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
        LOGGER.debug(data)
        return data
