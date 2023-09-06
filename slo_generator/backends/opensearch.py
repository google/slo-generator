"""
`opensearch.py`
Opensearch backend implementation.
"""

import copy
import logging

from opensearchpy import OpenSearch

from slo_generator.constants import NO_DATA

LOGGER = logging.getLogger(__name__)


# pylint: disable=duplicate-code
class OpensearchBackend:
    """Backend for querying metrics from OpenSearch.

    Args:
        client(opensearch.OpenSearch): Existing OS client.
        os_config(dict): OS client configuration.
    """

    def __init__(self, client=None, **os_config):
        self.client = client
        if self.client is None:
            conf = copy.deepcopy(os_config)
            url = conf.pop("url", None)
            basic_auth = conf.pop("basic_auth", None)
            api_key = conf.pop("api_key", None)
            if url:
                conf["hosts"] = url
            if basic_auth:
                conf["basic_auth"] = (basic_auth["username"], basic_auth["password"])
            if api_key:
                conf["api_key"] = (api_key["id"], api_key["value"])

            self.client = OpenSearch(**conf)

    # pylint: disable=unused-argument
    def good_bad_ratio(self, timestamp, window, slo_config):
        """Query two timeseries, one containing 'good' events, one containing
        'bad' events.

        Args:
            timestamp(int): UNIX timestamp.
            window(int): Window size (in seconds).
            slo_config(dict): SLO configuration.
              spec:
                method: "good_bad_ratio"
                service_level_indicator:
                  query_good(str): the search query to look for good events
                  query_bad(str): the search query to look for ba events
                  query_valid(str): the search query to look for valid events

        Returns:
            tuple: good_event_count, bad_event_count
        """
        measurement = slo_config["spec"]["service_level_indicator"]
        index = measurement["index"]
        query_good = measurement["query_good"]
        query_bad = measurement.get("query_bad")
        query_valid = measurement.get("query_valid")
        date_field = measurement.get("date_field")

        good = OS.build_query(query_good, window, date_field)
        bad = OS.build_query(query_bad, window, date_field)
        valid = OS.build_query(query_valid, window, date_field)

        good_events_count = OS.count(self.query(index, good))

        if query_bad is not None:
            bad_events_count = OS.count(self.query(index, bad))
        elif query_valid is not None:
            bad_events_count = OS.count(self.query(index, valid)) - good_events_count
        else:
            raise ValueError("`filter_bad` or `filter_valid` is required.")

        return good_events_count, bad_events_count

    def query(self, index, body):
        """Query Opensearch server.

        Args:
            index(str): Index to query.
            body(dict): Query body.

        Returns:
            dict: Response.
        """
        return self.client.search(index=index, body=body)

    @staticmethod
    def count(response):
        """Count event in opensearch response.

        Args:
            response(dict): Opensearch query response.

        Returns:
            int: Event count.
        """
        try:
            return response["hits"]["total"]["value"]
        except KeyError as exception:
            LOGGER.warning("Couldn't find any values in timeseries response")
            LOGGER.debug(exception, exc_info=True)
            return NO_DATA

    @staticmethod
    def build_query(query, window, date_field):
        """Build Opensearch query.

        Add window to existing query.
        Replace window for different error budget steps on-the-fly.

        Args:
            query(dict): Existing query body.
            window(int): Window in seconds.
            date_field(str): Field to filter time on

        Returns:
            dict: Query body with range clause added.
        """
        if query is None:
            return None
        body = {"query": {"bool": query}, "track_total_hits": True}
        range_query = {
            f"{date_field}": {
                "gte": f"now-{window}s/s",
                "lt": "now/s",
            }
        }

        if "filter" in body["query"]["bool"]:
            body["query"]["bool"]["filter"]["range"] = range_query
        else:
            body["query"]["bool"]["filter"] = {"range": range_query}

        return body


OS = OpensearchBackend
