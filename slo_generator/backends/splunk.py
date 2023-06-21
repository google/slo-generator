"""
`splunk.py`
Query a splunk search to compute a SLI as a custom slo-generator backend
"""
import copy
import json
import logging
import re

import splunklib.client as splunk_client

LOGGER = logging.getLogger(__name__)


class SplunkBackend:
    """
    Queries data from a Splunk instance (On Premises or Cloud)
    and make SLO out of them
    """

    def __init__(self, client=None, **splunk_config):
        self.client = client
        conf = copy.deepcopy(splunk_config)
        host = conf.pop("host", None)
        port = int(conf.pop("port", 8089))
        token = conf.pop("token", None)
        user = conf.pop("user", None)
        password = conf.pop("password", None)
        if not self.client:
            if token is not None:
                # Create a Service instance and log in using a token
                self.client = splunk_client.connect(
                    host=host,
                    port=port,
                    splunkToken=token,
                )
            else:
                # Create a Service instance and log in using user/pwd
                self.client = splunk_client.connect(
                    host=host,
                    port=port,
                    username=user,
                    password=password,
                )

    def good_bad_ratio(self, timestamp, window, slo_config):
        """
        Query SLI value from good and valid queries.
        If both search_query_bad & search_query_valid are supplied,
           "bad" takes precedence over valid.
        Args:
            timestamp (int): UNIX timestamp.
            window (int): Window (in seconds).
            slo_config (dict): SLO configuration.
              spec:
                method: "good_bad_ratio"
                service_level_indicator:
                  search_query_good (str): the search query to loook for good events,
                                           must return a single row/column named "good"
                  search_query_bad (str): the search query to loook for bad events,
                                           must return a single row/column named "bad"
                  search_query_valid (str): the search query to loook for valid events,
                                           must return a single row/column named "valid"
        Returns:
            tuple: Good event count, Bad event count.
        """
        kwargs_search = {
            "earliest_time": f"-{window}s",
            "latest_time": timestamp,
            "output_mode": "json",
        }
        result_good = int(
            self.splunk_query(
                slo_config["spec"]["service_level_indicator"]["search_query_good"],
                "good",
                **kwargs_search,
            )
        )
        if "search_query_bad" in slo_config["spec"]["service_level_indicator"]:
            result_bad = int(
                self.splunk_query(
                    slo_config["spec"]["service_level_indicator"]["search_query_bad"],
                    "bad",
                    **kwargs_search,
                )
            )
        elif "search_query_valid" in slo_config["spec"]["service_level_indicator"]:
            result_bad = (
                int(
                    self.splunk_query(
                        slo_config["spec"]["service_level_indicator"][
                            "search_query_valid"
                        ],
                        "valid",
                        **kwargs_search,
                    )
                )
                - result_good
            )

        return (result_good, result_bad)

    def query_sli(self, timestamp, window, slo_config):
        """Query SLI value directly.
        Args:
            timestamp (int): UNIX timestamp.
            window (int): Window (in seconds).
            slo_config (dict): SLO configuration.
              spec:
                method: "query_sli"
                service_level_indicator:
                  search_query (str): the search query to run.
                                      must return a single row
                                      with at least a column named "sli"
        Returns:
            float: SLI value.
        """
        kwargs_search = {
            "earliest_time": f"-{window}s",
            "latest_time": timestamp,
            "output_mode": "json",
        }
        result = self.splunk_query(
            slo_config["spec"]["service_level_indicator"]["search_query"],
            "sli",
            **kwargs_search,
        )
        return result["sli"]

    @staticmethod
    def fix_search_prefix(search=""):
        """
        Splunk API search queries must start with "search"
        but people are used to the search bar of the UI which doesn't

        Args:
            search(string): the search to execute
        Returns:
            The same string prefixed with "search " if needed
        """
        if not re.search("^search ", search):
            search = f"search {search}"
        return search

    def splunk_query(self, search="", result_column="", **kwargs_search):
        """
        Cleanup and sent the search query to splunk
        and return the content of the first row of the choosen column

        Args:
            search(string): the search string to run against Splunk
            result_column(string): the column to look for in the results of the search
            kwargs_search(item): search parameters
                                 as described in the Splunk oneshot search API
        Returns
            The value of the first row of the results for the selected column
        """
        search_query = self.fix_search_prefix(search)
        result_json = self.client.jobs.oneshot(search_query, **kwargs_search)
        return json.loads(str(result_json))["results"][0][result_column]
