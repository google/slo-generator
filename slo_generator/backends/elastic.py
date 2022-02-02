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
`elasticsearch.py`
ElasticSearch backend implementation.
"""

import logging
import requests
import json
from retrying import retry

#from elasticsearch import Elasticsearch

from slo_generator.constants import NO_DATA

LOGGER = logging.getLogger(__name__)

DEFAULT_DATE_FIELD = '@timestamp'


class ElasticBackend:
    """Backend for querying metrics from ElasticSearch.

    Args:
        client (elasticsearch.ElasticSearch): Existing ES client.
        es_config (dict): ES client configuration.
    """

    def __init__(self, client=None, url=None, **es_config):
        self.client = client
        if self.client is None:
            #self.client = Elasticsearch(**es_config)
            self.client = ElasticClient(url)

    # pylint: disable=unused-argument
    def good_bad_ratio(self, timestamp, window, slo_config):
        """Query two timeseries, one containing 'good' events, one containing
        'bad' events.

        Args:
            timestamp (int): UNIX timestamp.
            window (int): Window size (in seconds).
            slo_config (dict): SLO configuration.

        Returns:
            tuple: A tuple (good_event_count, bad_event_count)
        """
        measurement = slo_config['spec']['service_level_indicator']
        index = measurement['index']
        query_good = measurement['query_good']
        query_bad = measurement.get('query_bad')
        query_valid = measurement.get('query_valid')
        date_field = measurement.get('date_field', DEFAULT_DATE_FIELD)

        # Build ELK request bodies
        good = ES.build_query(query_good, window, date_field)
        bad = ES.build_query(query_bad, window, date_field)
        valid = ES.build_query(query_valid, window, date_field)

        # Get good events count
        response = self.query(index, good)
        good_events_count = ES.count(response)

        # Get bad events count
        if query_bad is not None:
            response = self.query(index, bad)
            bad_events_count = ES.count(response)
        elif query_valid is not None:
            response = self.query(index, valid)
            bad_events_count = ES.count(response) - good_events_count
        else:
            raise Exception("`filter_bad` or `filter_valid` is required.")

        return (good_events_count, bad_events_count)

    def query_slo(self, timestamp, window, slo_config):
        """Query SLO value from a given Datadog SLO.
        Args:
            timestamp (int): UNIX timestamp.
            window (int): Window (in seconds).
            slo_config (dict): SLO configuration.
        Returns:
            tuple: Good event count, bad event count.
        """
        measurement = slo_config['spec']['service_level_indicator']
        index = measurement['index']
        slo = measurement['slo']
        query_filter = measurement['filter']
        query_sort = measurement['sort']
        date_field = measurement.get('date_field', DEFAULT_DATE_FIELD)
        query_size = measurement.get('size')
        use_range = measurement.get('use_range')
         
        # Build ELK request bodies
        #filter = query_filter
        LOGGER.debug(query_filter)
        filter = ES.build_query_slo(query_filter, query_sort, query_size, use_range, window, date_field)
        
        # Get SLO
        response = self.query_json(index, filter)
        sli_value = ES.value_slo(response, slo)
        LOGGER.debug(sli_value)
        return sli_value


    def query(self, index, body):
        """Query ElasticSearch server.

        Args:
            index (str): Index to query.
            body (dict): Query body.

        Returns:
            dict: Response.
        """
        return self.client.search(index=index, body=body)

    def query_json(self, index, body):
        """Query ElasticSearch server.
        Args:
            index (str): Index to query.
            body (dict): Query body.
        Returns:
            dict: Response.
        """
        return self.client.request('post',index=index, body=body)
    
    @staticmethod
    def value_slo(response, slo):
        """Count event in Prometheus response.
        Args:
            response (dict): Prometheus query response.
        Returns:
            int: Event count.
        """
        LOGGER.debug(response)
        try:
            #print(response['hits']['hits']['_source']['valid_hosts'])
            hits_response = response['hits']['hits']
            for key in response['hits']['hits']:
                return float(key['_source'][slo])
        except KeyError as exception:
            LOGGER.warning("Couldn't find any values in timeseries response")
            LOGGER.debug(exception, exc_info=True)
            return NO_DATA

    @staticmethod
    def count(response):
        """Count event in Prometheus response.

        Args:
            response (dict): Prometheus query response.

        Returns:
            int: Event count.
        """
        try:
            return response['hits']['total']['value']
        except KeyError as exception:
            LOGGER.warning("Couldn't find any values in timeseries response")
            LOGGER.debug(exception, exc_info=True)
            return NO_DATA

    @staticmethod
    def build_query(query, window, date_field=DEFAULT_DATE_FIELD):
        """Build ElasticSearch query.

        Add window to existing query.
        Replace window for different error budget steps on-the-fly.

        Args:
            body (dict): Existing query body.
            window (int): Window in seconds.
            date_field (str): Field to filter time on (must be an ElasticSearch
                field of type `date`. Defaults to `@timestamp` (Logstash-
                generated date field).

        Returns:
            dict: Query body with range clause added.
        """
        if query is None:
            return None
        body = {"query": {"bool": query}, "track_total_hits": True}
        range_query = {
            f"{date_field}": {
                "gte": f"now-{window}s/s",
                "lt": "now/s"
            }
        }

        # If a 'filter' clause already exist, add the range query on top,
        # otherwise create the 'filter' clause.
        if "filter" in body["query"]["bool"]:
            body["query"]["bool"]["filter"]["range"] = range_query
        else:
            body["query"]["bool"] = {"filter": {"range": range_query}}

        return body

    @staticmethod
    def build_query_slo(query, sort, size, use_range, window, date_field=DEFAULT_DATE_FIELD):
        """Build ElasticSearch query.
        Add window to existing query.
        Replace window for different error budget steps on-the-fly.
        Args:
            body (dict): Existing query body.
            window (int): Window in seconds.
            date_field (str): Field to filter time on (must be an ElasticSearch
                field of type `date`. Defaults to `@timestamp` (Logstash-
                generated date field).
        Returns:
            dict: Query body with range clause added.
        """
        if query is None:
            return None
        body = {"query": {"bool" : {"must" : [query]}}}
        range_query = {
            f"{date_field}": {
                "gte": f"now-{window}s/s",
                "lt": "now/s"
            }
        }

        # Add the range query on top,
        if (use_range == "True"):
            body = {"query": {"bool": {"must" : [query] , "filter": [{ "range": range_query}]}}}
        body["sort"] = sort
        body["size"] = size
        LOGGER.debug(body)
        return body

ES = ElasticBackend

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



class ElasticClient:
    """Small wrapper around requests to query Elasticsearch API.
    Args:
        api_url (str): Elasticsearch API URL.
        api_token (str): Elasticsearch token.
    """
    # Keys to extract response data for each endpoint
    ENDPOINT_KEYS = {'metrics': 'metrics', 'metrics/query': 'result'}

    def __init__(self, api_url):
        self.client = requests.Session()
        self.url = api_url.rstrip('/')

    @retry(retry_on_result=retry_http,
           wait_exponential_multiplier=1000,
           wait_exponential_max=10000)
    def request(self,
                method,
                index=None,
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
        url = f'{self.url}' + '/' + index + "/_search?pretty"
        #LOGGER.debug(url)
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'User-Agent': 'slo-generator',
        }
        if method in ['put', 'post']:
            response = req(url, headers=headers, verify=False, json=body)
        else:
            response = req(url, headers=headers, verify=False)
            LOGGER.debug(f'Response: {response}')
        data = ElasticsearchClient.to_json(response)
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
