import unittest

from slo_generator.backends.open_search import OpenSearchBackend


class TestOpenSearchBackend(unittest.TestCase):
    def test_build_query_with_empty_query(self):
        assert OpenSearchBackend.build_query(None, 3600, "date") is None

    def test_build_query_with_simple_query_and_no_filter(self):
        query: dict = {
            "must": {
                "term": {
                    "status": "200",
                },
            },
        }

        enriched_query = {
            "query": {
                "bool": {
                    "must": {
                        "term": {
                            "status": "200",
                        },
                    },
                    "filter": {
                        "range": {
                            "date": {
                                "gte": "now-3600s/s",
                                "lt": "now/s",
                            },
                        },
                    },
                },
            },
            "track_total_hits": True,
        }

        assert OpenSearchBackend.build_query(query, 3600, "date") == enriched_query

    def test_build_query_with_simple_query_and_simple_filter(self):
        query: dict = {
            "must": {
                "term": {
                    "status": "200",
                },
            },
            "filter": {
                "term": {
                    "type": "get",
                },
            },
        }

        enriched_query = {
            "query": {
                "bool": {
                    "must": {
                        "term": {
                            "status": "200",
                        },
                    },
                    "filter": [
                        {
                            "term": {
                                "type": "get",
                            }
                        },
                        {
                            "range": {
                                "date": {
                                    "gte": "now-3600s/s",
                                    "lt": "now/s",
                                },
                            }
                        },
                    ],
                },
            },
            "track_total_hits": True,
        }

        assert OpenSearchBackend.build_query(query, 3600, "date") == enriched_query

    def test_build_query_with_simple_query_and_existing_filter_on_range_date(self):
        query: dict = {
            "must": {
                "term": {
                    "status": "200",
                },
            },
            "filter": {
                "range": {
                    "date": {
                        "gte": "2023-08-28",
                        "lt": "2023-08-29",
                    },
                },
            },
        }

        enriched_query: dict = {
            "query": {
                "bool": {
                    "must": {
                        "term": {
                            "status": "200",
                        },
                    },
                    "filter": [
                        {
                            "range": {
                                "date": {
                                    "gte": "now-3600s/s",
                                    "lt": "now/s",
                                },
                            },
                        }
                    ],
                },
            },
            "track_total_hits": True,
        }

        assert OpenSearchBackend.build_query(query, 3600, "date") == enriched_query

    def test_build_query_with_simple_query_and_existing_filter_with_range(self):
        query: dict = {
            "must": {
                "term": {
                    "status": "200",
                },
            },
            "filter": {
                "range": {
                    "status": {
                        "lt": "299",
                    },
                },
            },
        }

        enriched_query: dict = {
            "query": {
                "bool": {
                    "must": {
                        "term": {
                            "status": "200",
                        },
                    },
                    "filter": [
                        {
                            "range": {
                                "status": {
                                    "lt": "299",
                                }
                            }
                        },
                        {
                            "range": {
                                "date": {
                                    "gte": "now-3600s/s",
                                    "lt": "now/s",
                                },
                            }
                        },
                    ],
                },
            },
            "track_total_hits": True,
        }

        assert OpenSearchBackend.build_query(query, 3600, "date") == enriched_query
