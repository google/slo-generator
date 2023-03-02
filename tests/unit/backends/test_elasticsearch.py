# Copyright 2022 Google Inc.
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

import unittest

from slo_generator.backends.elasticsearch import ElasticsearchBackend


class TestElasticsearchBackend(unittest.TestCase):
    def test_build_query_with_empty_query(self):
        query: dict = None
        window: int = 3600
        date_field: str = "@timestamp"
        enriched_query: dict = None
        assert (
            ElasticsearchBackend.build_query(query, window, date_field)
            == enriched_query
        )

    def test_build_query_with_simple_query_and_no_filter(self):
        query: dict = {
            "must": {
                "term": {
                    "name": "JAgOZE8",
                },
            },
        }
        window: int = 3600
        date_field: str = "@timestamp"
        enriched_query: dict = {
            "query": {
                "bool": {
                    "must": {
                        "term": {
                            "name": "JAgOZE8",
                        },
                    },
                    "filter": {
                        "range": {
                            "@timestamp": {
                                "gte": "now-3600s/s",
                                "lt": "now/s",
                            },
                        },
                    },
                },
            },
            "track_total_hits": True,
        }
        assert (
            ElasticsearchBackend.build_query(query, window, date_field)
            == enriched_query
        )

    def test_build_query_with_simple_query_and_existing_filter(self):
        query: dict = {
            "must": {
                "term": {
                    "name": "JAgOZE8",
                },
            },
            "filter": {
                "term": {
                    "grade": 2,
                },
            },
        }
        window: int = 3600
        date_field: str = "@timestamp"
        enriched_query: dict = {
            "query": {
                "bool": {
                    "must": {
                        "term": {
                            "name": "JAgOZE8",
                        },
                    },
                    "filter": {
                        "term": {
                            "grade": 2,
                        },
                        "range": {
                            "@timestamp": {
                                "gte": "now-3600s/s",
                                "lt": "now/s",
                            },
                        },
                    },
                },
            },
            "track_total_hits": True,
        }
        assert (
            ElasticsearchBackend.build_query(query, window, date_field)
            == enriched_query
        )

    def test_build_query_with_simple_query_and_existing_filter_with_range(self):
        query: dict = {
            "must": {
                "term": {
                    "name": "JAgOZE8",
                },
            },
            "filter": {
                "range": {
                    "@timestamp": {
                        "gte": "2015-01-01",  # should be replaced, so can be anything
                        "lt": "2015-01-03",  # should be replaced, so can be anything
                    },
                },
            },
        }
        window: int = 3600
        date_field: str = "@timestamp"
        enriched_query: dict = {
            "query": {
                "bool": {
                    "must": {
                        "term": {
                            "name": "JAgOZE8",
                        },
                    },
                    "filter": {
                        "range": {
                            "@timestamp": {
                                "gte": "now-3600s/s",
                                "lt": "now/s",
                            },
                        },
                    },
                },
            },
            "track_total_hits": True,
        }
        assert (
            ElasticsearchBackend.build_query(query, window, date_field)
            == enriched_query
        )
