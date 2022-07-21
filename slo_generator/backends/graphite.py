# Copyright 2021 Adeo.
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
`Graphite.py`
Graphite backend implementation.
"""
import json
import logging
import pprint
import requests
import datetime

from datetime import datetime
from retrying import retry
from slo_generator.constants import NO_DATA

LOGGER = logging.getLogger(__name__)


class GraphiteBackend:
    """Backend for querying metrics from Datadog.
    Args:
        client (obj, optional): Existing `requests.Session` to pass.
        api_url (str): Graphite API URL.
        api_token (str): Graphite token.
    """
    def __init__(self, client=None, api_url=None):
        self.client = client
        if client is None:
            self.client = GraphiteClient(api_url)

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
        conf = slo_config['spec']
        measurement = conf['service_level_indicator']
        start = (timestamp - window)
        end = timestamp
        metric = measurement['metric']
        threshold = measurement['threshold']
        good_below_threshold = measurement.get('good_below_threshold', True)
        response = self.query(start=start, end=end, metric=metric)
        #LOGGER.debug(f"Result valid: {pprint.pformat(response)}")
        return GraphiteBackend.count_threshold(response,
                                                threshold,
                                                good_below_threshold)

    def query(self,
              start,
              end,
              metric):
        """Query Graphite Metrics V2.
        Args:
            start (int): Start timestamp (in milliseconds).
            end (int): End timestamp (in milliseconds).
        Returns:
            dict: Graphite API response.
        """
        params = {
            'from': datetime.fromtimestamp(start).strftime("%H:%M_%Y%m%d"),
            'until': datetime.fromtimestamp(end).strftime("%H:%M_%Y%m%d"),
            'format': "json"
        }
        LOGGER.debug(f"parameter{pprint.pformat(params)}")
        return self.client.request('get',
                                   'render?target',
                                   metric,
                                   **params)

    @staticmethod
    def count_threshold(response, threshold, good_below_threshold=True):
        """Create 2 buckets based on response and a value threshold, and return
        number of events contained in each bucket.
        Args:
            response (dict): Graphite API response.
            threshold (int): Threshold.
            good_below_threshold (bool): If true, good events are < threshold.
        Returns:
            tuple: Number of good events, Number of bad events.
        """
        try:
            x = len(response)
            LOGGER.debug(f"Response{response}")
            LOGGER.debug(f"Number Response {pprint.pformat(x)}")
            target = 0
            below = []
            above = []
            if x!= 0 :
                while (target < x):
                    #LOGGER.debug({pprint.pformat(response[target])})
                    datapoints = response[target]['datapoints']
                    #print(datapoints)
                    #LOGGER.debug({pprint.pformat(datapoints)})
                    
                    for point in datapoints:
                        #LOGGER.debug({pprint.pformat(point[0])})
                        value = point[0]
                        print(f"value : {value}")
                        if value is None or value <= threshold:
                            #LOGGER.debug("below")
                            below.append(value)
                            
                        #elif value == 3.0:
                            #LOGGER.debug("UNKNOWN")
                        elif value != 3.0:
                            #LOGGER.debug("above")
                            #print(f"value above : {value}")
                            above.append(value)
                    target = target + 1
                if good_below_threshold:
                    #LOGGER.debug(f"Good value : {len(below)} ; Bad Value: {len(above)}")
                    return len(below), len(above)
                return len(above), len(below)
            else :
                LOGGER.warning("Couldn't find any values in timeseries response")
                return NO_DATA, NO_DATA  # no events in timeseries
        except (IndexError, KeyError, ZeroDivisionError) as exception:
            LOGGER.warning("Couldn't find any values in timeseries response")
            LOGGER.debug(exception)
            return NO_DATA, NO_DATA  # no events in timeseries

class GraphiteClient:
    """Small wrapper around requests to query Graphite API.
    Args:
        api_url (str): Graphite API URL.
    """

    def __init__(self, api_url):
        self.client = requests.Session()
        self.url = api_url.rstrip('/')

    def request(self,
                method,
                endpoint,
                metric,
                **params):
        """Request Graphite API.
        Args:
            method (str): Requests method between ['post', 'put', 'get'].
            endpoint (str): API endpoint.
            params (dict): Params to send with request.
        Returns:
            obj: API response.
        """
        req = getattr(self.client, method)
        url = f'{self.url}/{endpoint}={metric}'
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'User-Agent': 'slo-generator'
        }
        params_str = "&".join("%s=%s" % (k, v) for k, v in params.items()
                              if v is not None)
        url += f'&{params_str}'
        """
        if method in ['put', 'post']:
            try:
                response = req(url, headers=headers, json=post_data, timeout=480)
            except requests.Timeout:
                print("Graphite timeout -> url : " + url)
        else:
            try:
                response = req(url, headers=headers, verify = False, timeout=480)
            except requests.Timeout:
                print("Graphite timeout -> url : " + url)
        """
        try:
            response = req(url, headers=headers, verify = False, timeout=480)
        except requests.Timeout:
            LOGGER.info("Graphite timeout -> url : " + url)
        #response = requests.get(url, headers=headers, verify = False)
        #response = '[{"target": "nagios.host.pfrlmasdrva01_corp_leroymerlin_com.service.sys_linux_memory-usage_ram.perfdata.ram_used", "datapoints": [[15281600.0, 1612257900], [15276100.0, 1612258200], [15277800.0, 1612258500], [15269300.0, 1612258800], [15293800.0, 1612259100], [null, 1612259400], [null, 1612259700], [null, 1612260000], [null, 1612260300], [null, 1612260600], [null, 1612260900], [null, 1612261200]]}]'
        #response = '[{"target": "nagios.host.arolmdbphxa02_corp_leroymerlin_com.service.db_oracle_instance-standby_SDBROLM.metadata.state", "datapoints": [[2.0, 1612271700], [0.0, 1612272000], [0.0, 1612272300], [0.0, 1612272600], [0.0, 1612272900], [0.0, 1612273200], [0.0, 1612273500], [0.0, 1612273800], [0.0, 1612274100], [0.0, 1612274400], [0.0, 1612274700], [null, 1612275000]]}]'
        LOGGER.debug(f'Response: {response.json()}')
        #data = GraphiteClient.to_json(response)
        data = response.json()
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
        #res = resp.content.decode('utf-8').replace('\n', '')
        data = json.loads(resp)
        return data