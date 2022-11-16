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
`api.py`
Api backend implementation.
"""

from datetime import datetime
from retrying import retry

import logging
import requests
import pprint
import json
from retrying import retry
import date_converter
import google.auth.transport.requests
import google.oauth2.id_token
LOGGER = logging.getLogger(__name__)

DEFAULT_DATE_FIELD = '@timestamp'

class ApiBackend:
    """Backend for querying metrics from ElasticSearch.

    Args:
        client (elasticsearch.ElasticSearch): Existing ES client.
        es_config (dict): ES client configuration.
    """

    def __init__(self, client=None, api_url=None, **es_config):
        self.client = client
        if self.client is None:
            self.client = APIClient(api_url)

    def threshold_data_quality(self, timestamp, window, slo_config):
        """Query SLI value from a given PromQL expression.

        Args:
            timestamp (int): UNIX timestamp.
            window (int): Window (in seconds).
            slo_config (dict): SLO configuration.

        Returns:
            float: SLI value.
        """
        conf = slo_config['spec']
        measurement = conf['service_level_indicator']
        dataScopeDateTimeBegin = APIClient.transform_timestamp(timestamp-3600)
        dataScopeDateTimeEnd = APIClient.transform_timestamp(timestamp)
        metricId = measurement['metric_id']
        threshold = measurement['threshold']
        good_below_threshold = measurement.get('good_below_threshold', True)
        response = self.query(start=dataScopeDateTimeBegin, end=dataScopeDateTimeEnd, metric=metricId, url=self.client.url)
        return APIClient.count_threshold(response,
                                                threshold,
                                                good_below_threshold)

    def query(self,
              start,
              end,
              metric,
              url):
        """Query Graphite Metrics V2.
        Args:
            start (int): Start timestamp (in milliseconds).
            end (int): End timestamp (in milliseconds).
        Returns:
            dict: Graphite API response.
        """
        url = f'{url}' + '?metricId=' + metric + "&dataScopeDateTimeBegin=" + start + "&dataScopeDateTimeEnd=" + end
        LOGGER.debug(f"parameter{pprint.pformat(url)}")
        return self.client.request('get', url)

def retry_http(response):
    """Retry on specific HTTP errors:
        * 429: Rate limited to 50 reqs/minute.
    Args:
        response (dict): Dynatrace API response.
    Returns:
        bool: True to retry, False otherwise.
    """
    retry_codes = [429]
    if isinstance(response.get('error', {}), str):
        code = 200
    else:
        code = int(response.get('error', {}).get('code', 200))
    return code in retry_codes

class APIClient:
    """Small wrapper around requests to query API.
    Args:
        api_url (str):  API URL.
    """

    def __init__(self, api_url , url_taget_audience):
        self.client = requests.Session()
        self.url = api_url.rstrip('/')
        self.url_taget_audience = url_taget_audience

    @retry(retry_on_result=retry_http,
           wait_exponential_multiplier=1000,
           wait_exponential_max=10000)
    def request(self,
                method,
                url,
                url_taget_audience,
                body=None,
                ):
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
        auth_req = google.auth.transport.requests.Request()
        target_audience = url_taget_audience
        Bearer = google.oauth2.id_token.fetch_id_token(auth_req, target_audience)
        #LOGGER.debug(url)
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'User-Agent': 'slo-generator',
            'Authorization': 'Bearer ' + Bearer
        }

        if method in ['put', 'post']:
            response = req(url, headers=headers, verify=False, json=body)
        else:
            response = req(url, headers=headers, verify=True)
            LOGGER.debug(f'Response: {response}')
        data = APIClient.to_json(response)
        return data


    def transform_timestamp(timestamp):
        dt_object = datetime.fromtimestamp(timestamp)
        converted_date = date_converter.string_to_string(str(dt_object), '%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S')
        return converted_date

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
            x = len(response["items"])
            LOGGER.debug(f"Response{response}")
            LOGGER.debug(f"Number Response {(x)}")
            target = 0
            below = []
            above = []
            if x!= 0 :
                while (target < x):
                    #LOGGER.debug({pprint.pformat(response[target])})
                    datapoints = response["items"][target]["metricOutcomeValue"]
                    #LOGGER.debug({pprint.pformat(datapoints)})
                    #print (datapoints)
                    if datapoints is None or datapoints >= threshold:
                        #LOGGER.debug("below")
                        below.append(datapoints)                        
                    else:
                        above.append(datapoints)
                    target = target + 1
                if good_below_threshold:
                    #LOGGER.debug(f"Good value : {len(below)} ; Bad Value: {len(above)}")
                    return len(below), len(above)
                return len(above), len(below)
            else :
                if good_below_threshold:
                    LOGGER.warning("Couldn't find any values in timeseries response")
                    return 0, 1
                LOGGER.warning("Couldn't find any values in timeseries response")
                #return NO_DATA, NO_DATA  # no events in timeseries
                return 1, 0
        except (IndexError, KeyError, ZeroDivisionError) as exception:
            LOGGER.debug(exception)
            if good_below_threshold:
                LOGGER.warning("Couldn't find any values in timeseries response")
                return 0, 1
            LOGGER.warning("Couldn't find any values in timeseries response")
            #return NO_DATA, NO_DATA  # no events in timeseries
            return 1, 0