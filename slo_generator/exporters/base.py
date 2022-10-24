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
`base.py`
Base exporter abstract classes.
"""
import logging
import warnings
from abc import ABCMeta, abstractmethod

LOGGER = logging.getLogger(__name__)

# Default metric labels exported by all metrics exporters
DEFAULT_METRIC_LABELS = [
    "error_budget_policy_step_name",
    "service_name",
    "feature_name",
    "slo_name",
    "metadata",
]

# Default metrics that are exported by metrics exporters.
DEFAULT_METRICS = [
    {
        "name": "error_budget_burn_rate",
        "description": "Speed at which the error budget is consumed.",
        "labels": DEFAULT_METRIC_LABELS,
    },
    {
        "name": "alerting_burn_rate_threshold",
        "description": "Error Budget burn rate threshold.",
        "labels": DEFAULT_METRIC_LABELS,
    },
    {
        "name": "events_count",
        "description": "Number of events",
        "labels": DEFAULT_METRIC_LABELS + ["good_events_count", "bad_events_count"],
    },
    {
        "name": "sli_measurement",
        "description": "Service Level Indicator.",
        "labels": DEFAULT_METRIC_LABELS,
    },
    {
        "name": "slo_target",
        "description": "Service Level Objective target.",
        "labels": DEFAULT_METRIC_LABELS,
    },
]


class MetricsExporter:  # pytype: disable=ignored-metaclass
    """Abstract class to export metrics to different backends. Common format
    for YAML configuration to configure which metrics should be exported."""

    __metaclass__ = ABCMeta  # pytype: disable=ignored-metaclass

    def export(self, data, **config):
        """Export metric data. Loops through metrics config and calls the child
        class `export_metric` method.

        Args:
            data (dict): SLO Report data.
            config (dict): Exporter config.

        Returns:
            list: List of exporter responses.
        """
        metrics = config.get("metrics", DEFAULT_METRICS)
        required_fields = getattr(self, "REQUIRED_FIELDS", [])
        optional_fields = getattr(self, "OPTIONAL_FIELDS", [])
        LOGGER.debug(f"Exporting {len(metrics)} metrics with {self.__class__.__name__}")
        for metric_cfg in metrics:
            if isinstance(metric_cfg, str):  # short form
                metric_cfg = {
                    "name": metric_cfg,
                    "alias": metric_cfg,
                    "description": "",
                    "labels": DEFAULT_METRIC_LABELS,
                }
            if metric_cfg["name"] == "error_budget_burn_rate":
                metric_cfg = MetricsExporter.use_deprecated_fields(
                    config=config, metric=metric_cfg
                )
            metric = metric_cfg.copy()
            fields = {
                key: value
                for key, value in config.items()
                if key in required_fields or key in optional_fields
            }
            metric.update(fields)
            metric = self.build_metric(data, metric)
            self.export_metric(metric)

    def build_metric(self, data, metric):
        """Build a metric from current data and metric configuration.
        Set the metric value labels and eventual alias.

        Args:
            data (dict): SLO Report data.
            metric (dict): Metric configuration.

        Returns:
            dict: Metric configuration.
        """
        name = metric["name"]
        prefix = getattr(self, "METRIC_PREFIX", None)

        # Set value + timestamp
        metric["value"] = data[name]
        metric["timestamp"] = data["timestamp"]

        # Set metric data labels
        labels = metric.get("labels", DEFAULT_METRIC_LABELS).copy()
        additional_labels = metric.get("additional_labels", [])
        labels.extend(additional_labels)
        labels = MetricsExporter.build_data_labels(data, labels)
        metric["labels"] = labels

        # Use metric alias (mapping)
        if "alias" in metric:
            metric["name"] = metric["alias"]

        if prefix and not metric["name"].startswith(prefix):
            metric["name"] = prefix + metric["name"]

        # Set description
        metric["description"] = metric.get("description", "")
        return metric

    @staticmethod
    def build_data_labels(data, labels):
        """Build data labels. Also handle nested labels (depth=1).

        Args:
            data (dict): SLO Report data.
            labels (list): Label keys.

        Returns:
            dict: Data labels.
        """
        data_labels = {}
        nested_labels = [
            label for label in labels if label in data and isinstance(data[label], dict)
        ]
        flat_labels = [
            label
            for label in labels
            if label in data and not isinstance(data[label], dict)
        ]
        for label in nested_labels:
            data_labels.update({k: str(v) for k, v in data[label].items()})
        for label in flat_labels:
            data_labels[label] = str(data[label])
        LOGGER.debug(f"Data labels: {data_labels}")
        return data_labels

    @staticmethod
    def use_deprecated_fields(config, metric):
        """Old format to new format with FutureWarning for 2.0.0.

        Update error_budget_burn_rate metric with `metric_type`,
        `metric_labels`, and `metric_description`.

        Args:
            config (dict): Exporter config.
            metric (dict): Metric config.

        Returns:
            list: List of metrics to export.
        """
        old_metric_type = config.get("metric_type")
        old_metric_labels = config.get("metric_labels")
        old_metric_description = config.get("metric_description")
        if old_metric_type:
            metric["alias"] = old_metric_type
            warnings.warn(
                "`metric_type` will be deprecated in favor of `metrics` "
                "in version 2.0.0, ",
                FutureWarning,
            )
        if old_metric_labels:
            metric["labels"] = old_metric_labels
            warnings.warn(
                "`metric_labels` will be deprecated in favor of `metrics` "
                "in version 2.0.0, ",
                FutureWarning,
            )
        if old_metric_description:
            warnings.warn(
                "`metric_description` will be deprecated in favor of `metrics` "
                "in version 2.0.0, ",
                FutureWarning,
            )
            metric["description"] = old_metric_description
        return metric

    @abstractmethod
    def export_metric(self, data):
        """Abstract method to export a metric. Should be implemented by children
        classes."""
        raise NotImplementedError
