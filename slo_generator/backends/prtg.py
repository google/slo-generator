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
`prtg.py`
PRTG backend implementation.
"""
import json
import logging
import pprint
import requests
import time
import datetime

from datetime import datetime
from retrying import retry
from slo_generator.constants import NO_DATA

LOGGER = logging.getLogger(__name__)


class PrtgBackend:
    """Backend for querying metrics from PRTG.
    Args:
        client (obj, optional): Existing `requests.Session` to pass.
        api_url (str): PRTG API URL.
        api_passhash (str): PRTG passhash.
    """
    def __init__(self, client=None, api_url=None, api_passhash=None):
        self.client = client
        if client is None:
            self.client = PrtgClient(api_url, api_passhash)

    def latency(self, timestamp, window, slo_config):
        """Compute SLI by counting the number of values below and above a
        threshold.
        Args:
            timestamp (int): UNIX timestamp.
            window (int): Window (in seconds).
            slo_config (dict): SLO configuration.
        Returns:
            tuple: Good event count, Bad event count.
        """
        conf = slo_config['spec']
        measurement = conf['service_level_indicator']
        timestamp = time.time()
        start = (timestamp - window)
        start = datetime.fromtimestamp(start)
        start = start.strftime('%Y-%m-%dT%H:%M:%S')
        end = timestamp
        end = datetime.fromtimestamp(end)
        end = end.strftime('%Y-%m-%dT%H:%M:%S')
        probe_id = measurement['probe_id']
        threshold = measurement['threshold']
        good_below_threshold = measurement.get('good_below_threshold', True)
        response = self.query_historicdata(start=start, end=end, probe_id=probe_id)
        LOGGER.debug(f"Result valid: {pprint.pformat(response)}")
        return PrtgBackend.count_threshold(response,
                                                threshold,
                                                good_below_threshold)
        
    def availability(self, timestamp, window, slo_config):
        """Compute SLI by counting the number of values below and above a
        threshold.
        Args:
            timestamp (int): UNIX timestamp.
            window (int): Window (in seconds).
            slo_config (dict): SLO configuration.
        Returns:
            tuple: Good event count, Bad event count.
        """
        conf = slo_config['spec']
        measurement = conf['service_level_indicator']
        timestamp = time.time()
        start = (timestamp - window)
        start = datetime.fromtimestamp(start)
        start = start.strftime('%Y-%m-%dT%H:%M:%S')
        end = timestamp
        end = datetime.fromtimestamp(end)
        end = end.strftime('%Y-%m-%dT%H:%M:%S')
        probe_id = measurement['probe_id']
        response = self.query_historicdata(start=start, end=end, probe_id=probe_id)
        LOGGER.debug(f"Result valid: {pprint.pformat(response)}")
        return PrtgBackend.count_availability(response)
    
    def bandwidth(self, timestamp, window, slo_config):
        """Compute SLI by counting the number of values below and above a
        threshold.
        Args:
            timestamp (int): UNIX timestamp.
            window (int): Window (in seconds).
            slo_config (dict): SLO configuration.
        Returns:
            tuple: Good event count, Bad event count.
        """
        conf = slo_config['spec']
        measurement = conf['service_level_indicator']
        timestamp = time.time()
        start = (timestamp - window)
        start = datetime.fromtimestamp(start)
        start = start.strftime('%Y-%m-%dT%H:%M:%S')
        LOGGER.warning(start)
        end = timestamp
        end = datetime.fromtimestamp(end)
        end = end.strftime('%Y-%m-%dT%H:%M:%S')
        LOGGER.warning(end)
        probe_id = measurement['probe_id']
        bandwidth_capacity = measurement['bandwidth_capacity']
        response = self.query_table(start=start, end=end, probe_id=probe_id)
        LOGGER.debug(f"Result valid: {pprint.pformat(response)}")
        return PrtgBackend.count_bandwidth(response, bandwidth_capacity)


    def query_historicdata(self,
              start,
              end,
              probe_id=None,
              aggregation='SUM'):
        """Query historicdata.json PRTG Metrics V2.
        Args:
            start (int): Start timestamp (in milliseconds).
            end (int): End timestamp (in milliseconds).
            metric_selector (str): Metric selector.
            entity_selector (str): Entity selector.
            aggregation (str): Aggregation.
        Returns:
            dict: PRTG API response.
        """
        params = {
            'sdate': start,
            'edate': end,
            'output': 'json',
            'id': probe_id,
            'username': 'slogenerator',
            'avg':'0',
            'usecaption':'1'
        }
        return self.client.request('get',
                                   'historicdata.json',
                                   version='v2',
                                   **params)

    def query_table(self,
              start,
              end,
              probe_id=None,
              aggregation='SUM'):
        """Query table.json PRTG Metrics V2.
        Args:
            start (int): Start timestamp (in milliseconds).
            end (int): End timestamp (in milliseconds).
            metric_selector (str): Metric selector.
            entity_selector (str): Entity selector.
            aggregation (str): Aggregation.
        Returns:
            dict: PRTG API response.
        """
        params = {
            'sdate': start,
            'edate': end,
            'output': 'json',
            'id': probe_id,
            'username': 'slogenerator',
            'content': 'channels',
            'columns': 'name,lastvalue_'
        }
        return self.client.request('get',
                                   'table.json',
                                   version='v2',
                                   **params)

    @staticmethod
    def count_threshold(response, threshold, good_below_threshold=True):
        """Create 2 buckets based on response and a value threshold, and return
        number of events contained in each bucket.
        Args:
            response (dict): PRTG API response.
            threshold (int): Threshold.
            good_below_threshold (bool): If true, good events are < threshold.
        Returns:
            tuple: Number of good events, Number of bad events.
        """
        try:
            datapoints = response['histdata']
            below = []
            above = []
            
            points_below = [
                point['Avg. Round Trip Time (RTT)'] for point in datapoints
                if point['Avg. Round Trip Time (RTT)'] is not None and type(point['Avg. Round Trip Time (RTT)']) is float and point['Avg. Round Trip Time (RTT)'] < threshold
            ]
            points_above = [
                point['Avg. Round Trip Time (RTT)'] for point in datapoints
                if point['Avg. Round Trip Time (RTT)'] is not None and type(point['Avg. Round Trip Time (RTT)']) is float and point['Avg. Round Trip Time (RTT)'] > threshold
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

    @staticmethod
    def count_availability(response):
        """Count events in time series.
        Args:
            response (dict):  PRTG Metrics API response.
            average (bool): Take average of result.
        Returns:
            int: Event count.
        """
        try:
            values = []
            datapoints = response['histdata']
            for point in datapoints:
                value = int(point['coverage'].strip(' %'))/100
                if value is None:
                    continue
                values.append(value)
            if not values:
                raise IndexError
            return sum(values) / len(values)
        except (IndexError, AttributeError) as exception:
            LOGGER.warning("Couldn't find any values in timeseries response")
            LOGGER.debug(exception)
            return 0  # no events in timeseries
    
    @staticmethod
    def count_bandwidth(response, bandwidth_capacity):
        """Count events in time series.
        Args:
            response (dict):  PRTG Metrics API response.
            average (bool): Take average of result.
        Returns:
            int: Event count.
        """
        try:
            datapoints = response['channels']
            for point in datapoints:
                if point['name'] == 'Traffic Total':
                    value = int(point['lastvalue'].strip(' Mbit/s'))
                    LOGGER.warning(value)
            return value / bandwidth_capacity
        except (IndexError, AttributeError) as exception:
            LOGGER.warning("Couldn't find any values in timeseries response")
            LOGGER.debug(exception)
            return 0  # no events in timeseries

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


class PrtgClient:
    """Small wrapper around requests to query PRTG API.
    Args:
        api_url (str): PRTG API URL.
        api_passhash (str): PRTG token.
    """
    # Keys to extract response data for each endpoint
    ENDPOINT_KEYS = {'metrics': 'metrics', 'historicdata': 'historicdata.json'}

    def __init__(self, api_url, api_passhash):
        self.client = requests.Session()
        self.url = api_url.rstrip('/')
        self.token = api_passhash

    #@retry(retry_on_result=retry_http,
    #       wait_exponential_multiplier=1000,
    #       wait_exponential_max=10000)
    def request(self,
                method,
                endpoint,
                name=None,
                version='v1',
                post_data=None,
                key=None,
                **params):
        """Request PRTG API.
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
        url = f'{self.url}/api/{endpoint}'
        params['passhash'] = self.token
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
        LOGGER.debug(f'PRTG url: {url}')
        if method in ['put', 'post']:
            try:
                response = req(url, headers=headers, json=post_data, timeout=480, verify=False)
            except requests.Timeout:
                print("PRTG timeout -> url : " + url)
        else:
            try:
                response = req(url, headers=headers, timeout=480, verify=False)
            except requests.Timeout:
                print("PRTG timeout -> url : " + url)
        data = PrtgClient.to_json(response)
        #LOGGER.debug(f'Data from PRTG: {data}')
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