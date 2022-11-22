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
from slo_generator.constants import NO_DATA
class ApiBackend:
    """Backend for querying metrics from ElasticSearch.

    Args:
        client (elasticsearch.ElasticSearch): Existing ES client.
        es_config (dict): ES client configuration.
    """

    def __init__(self, client=None, api_url=None, url_target_audience=None, **es_config):
        self.client = client
        if self.client is None:
            self.client = APIClient(api_url,url_target_audience)

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
        dataScopeDateTimeBegin = APIClient.transform_timestamp(timestamp-window)
        dataScopeDateTimeEnd = APIClient.transform_timestamp(timestamp)
        metricId = measurement['metric_id']
        threshold = measurement['threshold']
        good_below_threshold = measurement.get('good_below_threshold', True)
        response = self.query(start=dataScopeDateTimeBegin, end=dataScopeDateTimeEnd, metric=metricId, url=self.client.url, url_target_audience=self.client.url_target_audience)
        return APIClient.count_threshold(response,
                                                threshold,
                                                good_below_threshold)

    def query(self,
              start,
              end,
              metric,
              url,
              url_target_audience):
        """Query Graphite Metrics V2.
        Args:
            start (int): Start timestamp (in milliseconds).
            end (int): End timestamp (in milliseconds).
        Returns:
            dict: Graphite API response.
        """
        
        #

        return self.client.request('get', url, url_target_audience, start, end, metric)

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

    def __init__(self, api_url , url_target_audience):
        self.client = requests.Session()
        self.url = api_url.rstrip('/')
        self.url_target_audience = url_target_audience

    @retry(retry_on_result=retry_http,
           wait_exponential_multiplier=1000,
           wait_exponential_max=10000)
    def request(self,
                method,
                url,
                url_target_audience,
                start,
                end,
                metric,
                body=None,
                ):
        """Request Dynatrace API.
        Args:
            method (str): Requests method between ['post', 'put', 'get'].
            endpoint (str): API endpoint.
            name (str): API resource name.
            version (str): API version. Default: v1.url_target_audience
            post_data (dict): JSON data.
            key (str): Key to extract data from JSON response.
            params (dict): Params to send with request.
        Returns:
            obj: API response.
        """
        req = getattr(self.client, method)
        auth_req = google.auth.transport.requests.Request()
        target_audience = url_target_audience
        Bearer = google.oauth2.id_token.fetch_id_token(auth_req, target_audience)
        #LOGGER.debug(url)
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'User-Agent': 'slo-generator',
            'Authorization': 'Bearer ' + Bearer
        }
        main_url = f'{url}' + '?metricId=' + metric + "&dataScopeDateTimeBegin=" + start + "&dataScopeDateTimeEnd=" + end + "&maxResults=250"
        LOGGER.debug(f"parameter{pprint.pformat(url)}")
        if method in ['put', 'post']:
            response = req(main_url, headers=headers, verify=False, json=body)           
        else:
            response = req(main_url, headers=headers, verify=True)
            LOGGER.debug(f'Response: {response}')
            json_response = APIClient.to_json(response)
            data = json_response
            #items = json_response["items"]
            if (json_response["items"] != []) :
                while (json_response["items"][-1]["processingDateTime"] >= start ):
                    url_next_page = f'{url}' + '?metricId=' + metric + "&pageToken=" + json_response["nextPageToken"] + "&dataScopeDateTimeBegin=" + start + "&dataScopeDateTimeEnd=" + end  + "&maxResults=250"
                    response = requests.get(url_next_page, headers=headers, verify=True)
                    json_response = APIClient.to_json(response)
                    for item in json_response ["items"] :
                        data["items"].append(item)
            
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
            #LOGGER.debug(f"Response{response['items']}")
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
                    if datapoints is None or datapoints >= float(threshold):
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
                LOGGER.warning("Couldn't find any values in timeseries response")
                return NO_DATA, NO_DATA  # no events in timeseries

        except (IndexError, KeyError, ZeroDivisionError) as exception:
            LOGGER.debug(exception)
            LOGGER.warning("Couldn't find any values in timeseries response")
            return NO_DATA, NO_DATA  # no events in timeseries
