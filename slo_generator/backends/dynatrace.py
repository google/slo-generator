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

from retrying import retry
from slo_generator.constants import NO_DATA

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

    def threshold(self, timestamp, window, slo_config):
        """Compute SLI by counting the number of values below and above a
        threshold.

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
        query_valid = measurement['query_valid']
        threshold = measurement['threshold']
        good_below_threshold = measurement.get('good_below_threshold', True)
        response = self.query(start=start, end=end, **query_valid)
        LOGGER.debug(f"Result valid: {pprint.pformat(response)}")
        return DynatraceBackend.count_threshold(response,
                                                threshold,
                                                good_below_threshold)

    def query(self,
              start,
              end,
              metric_selector=None,
              entity_selector=None,
              aggregation='SUM'):
        """Query Dynatrace Metrics V2.

        Args:
            start (int): Start timestamp (in milliseconds).
            end (int): End timestamp (in milliseconds).
            metric_selector (str): Metric selector.
            entity_selector (str): Entity selector.
            aggregation (str): Aggregation.

        Returns:
            dict: Dynatrace API response.
        """
        params = {
            'from': start,
            'end': end,
            'metricSelector': metric_selector,
            'entitySelector': entity_selector,
            'aggregation': aggregation,
            'includeData': True
        }
        return self.client.request('get',
                                   'metrics/query',
                                   version='v2',
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
            datapoints = response['result'][0]['data']
            values = []
            for point in datapoints:
                point_values = [
                    point for point in point['values']
                    if point is not None and point > 0
                ]
                values.extend(point_values)
            return sum(values)
        except (IndexError, KeyError) as exception:
            LOGGER.warning("Couldn't find any values in timeseries response")
            LOGGER.debug(exception)
            return NO_DATA  # no events in timeseries

    @staticmethod
    def count_threshold(response, threshold, good_below_threshold=True):
        """Create 2 buckets based on response and a value threshold, and return
        number of events contained in each bucket.

        Args:
            response (dict): Dynatrace API response.
            threshold (int): Threshold.
            good_below_threshold (bool): If true, good events are < threshold.

        Returns:
            tuple: Number of good events, Number of bad events.
        """
        try:
            datapoints = response['result'][0]['data']
            below = []
            above = []
            for point in datapoints:
                points_below = [
                    point for point in point['values']
                    if point is not None and point < threshold
                ]
                points_above = [
                    point for point in point['values']
                    if point is not None and point > threshold
                ]
                below.extend(points_below)
                above.extend(points_above)
            if good_below_threshold:
                return len(below), len(above)
            return len(above), len(below)
        except (IndexError, KeyError, ZeroDivisionError) as exception:
            LOGGER.warning("Couldn't find any values in timeseries response")
            LOGGER.debug(exception)
            return NO_DATA, NO_DATA  # no events in timeseries


def retry_http(response):
    """Retry on specific HTTP errors:

        * 429: Rate limited to 50 reqs/minute.

    Args:
        response (dict): Dynatrace API response.

    Returns:
        bool: True to retry, False otherwise.
    """
    retry_codes = [429]
    code = int(response.get('error', {}).get('code', 200))
    return code in retry_codes


class DynatraceClient:
    """Small wrapper around requests to query Dynatrace API.

    Args:
        api_url (str): Dynatrace API URL.
        api_token (str): Dynatrace token.
    """
    # Keys to extract response data for each endpoint
    ENDPOINT_KEYS = {'metrics': 'metrics', 'metrics/query': 'result'}

    def __init__(self, api_url, api_key):
        self.client = requests.Session()
        self.url = api_url.rstrip('/')
        self.token = api_key

    @retry(retry_on_result=retry_http,
           wait_exponential_multiplier=1000,
           wait_exponential_max=10000)
    def request(self,
                method,
                endpoint,
                name=None,
                version='v1',
                post_data=None,
                key=None,
                **params):
        """Request Dynatrace API.

        Args:
            method (str): Requests method between ['post', 'put', 'get'].
            endpoint (str): API endpoint.
            name (str): API resource name.
            version (str): API version. Default: v1.
            post_data (dict): JSON data.
            key (str): Key to extract data from JSON response.
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
        params_str = "&".join("%s=%s" % (k, v) for k, v in params.items()
                              if v is not None)
        url += f'?{params_str}'
        if method in ['put', 'post']:
            response = req(url, headers=headers, json=post_data)
        else:
            response = req(url, headers=headers)
        data = DynatraceClient.to_json(response)
        next_page_key = data.get('nextPageKey')
        if next_page_key:
            params = {'nextPageKey': next_page_key, 'Api-Token': self.token}
            LOGGER.debug(f'Requesting next page: {next_page_key}')
            data_next = self.request(method, endpoint, name, version, **params)
            next_page_key = data_next.get('nextPageKey')
            if not key:
                key = DynatraceClient.ENDPOINT_KEYS.get(endpoint, 'result')
            data[key].extend(data_next[key])
        return data

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
        return data
