"""dummy_backend.py

Dummy backend implementation for testing.
"""


class DummyBackend:
    def __init__(self, client=None, **config):
        self.good_events = config.get("good_events", None)
        self.bad_events = config.get("bad_events", None)
        self.sli_value = config.get("sli", None)

    def good_bad_ratio(self, timestamp, window, slo_config):
        return (self.good_events, self.bad_events)

    def sli(self, timestamp, window, slo_config):
        return self.sli_value
