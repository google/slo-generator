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

DEFAULT_METRIC_LABELS = [
    'error_budget_policy_step_name', 'window', 'service_name', 'slo_name',
    'alerting_burn_rate_threshold'
]

DEFAULT_METRICS = [
    {
        'name': 'error_budget_burn_rate',
        'description': 'Speed at which the error budget is consumed.',
        'labels': DEFAULT_METRIC_LABELS
    },
    {
        'name': 'sli_measurement',
        'description': 'Service Level Indicator.',
        'labels': DEFAULT_METRIC_LABELS
    }
]

class MetricsExporter:
    """Abstract class to export metrics to different backends. Common format
    for YAML configuration to configure which metrics should be exported."""
    __metaclass__ = ABCMeta

    def export(self, data, **config):
        """Export metric data. Loops through metrics config and calls the child
        class `export_metric` method.

        Args:
            data (dict): SLO Report data.
            config (dict): Exporter config.

        Returns:
            list: List of exporter responses.
        """

        metrics = config.get('metrics', DEFAULT_METRICS)
        required_fields = getattr(self, 'REQUIRED_FIELDS', [])
        optional_fields = getattr(self, 'OPTIONAL_FIELDS', [])
        all_data = []
        LOGGER.debug(
            f'Exporting {len(metrics)} metrics with {self.__class__.__name__}')
        for metric_cfg in metrics:
            if isinstance(metric_cfg, str): # short form
                metric_cfg = {
                    'name': metric_cfg,
                    'alias': metric_cfg,
                    'description': "",
                    'labels': DEFAULT_METRIC_LABELS
                }
            if metric_cfg['name'] == 'error_budget_burn_rate':
                metric_cfg = MetricsExporter.use_deprecated_fields(
                    config=config,
                    metric=metric_cfg)
            metric = metric_cfg.copy()
            fields = {
                key: value for key, value in config.items()
                if key in required_fields or key in optional_fields
            }
            metric.update(fields)
            metric = self.build_metric(data, metric)
            name = metric['name']
            LOGGER.info(f'Exporting "{name}" ...')
            ret = self.export_metric(metric)
            metric_info = {
                k: v for k, v in metric.items() 
                if k in ['name', 'alias', 'description', 'labels']
            }
            response = {
                'response': ret,
                'metric': metric_info
            }
            if ret and 'error' in ret:
                LOGGER.error(response)
            all_data.append(response)
        return all_data

    def build_metric(self, data, metric):
        """Build a metric from current data and metric configuration.
        Set the metric value labels and eventual alias.

        Args:
            data (dict): SLO Report data.
            metric (dict): Metric configuration.

        Returns:
            dict: Metric configuration.
        """
        name = metric['name']
        prefix = getattr(self, 'METRIC_PREFIX', None)

        # Set value + timestamp
        metric['value'] = data[name]
        metric['timestamp'] = data['timestamp']

        # Set metric labels
        labels = metric.get('labels', DEFAULT_METRIC_LABELS)
        additional_labels = metric.get('additional_labels', [])
        labels.extend(additional_labels)
        labels = {key: str(val) for key, val in data.items() if key in labels}
        metric['labels'] = labels

        # Use metric alias (mapping)
        if 'alias' in metric:
            metric['name'] = metric['alias']

        if prefix:
            metric['name'] = prefix + metric['name']

        # Set description
        metric['description'] = metric.get('description', "")

        return metric

    @staticmethod
    def use_deprecated_fields(config, metric):
        """Old format to new format with DeprecationWarning for 2.0.0.

        Update error_budget_burn_rate metric with `metric_type`,
        `metric_labels`, and `metric_description`.

        Args:
            config (dict): Exporter config.
            metric (dict): Metric config.

        Returns:
            list: List of metrics to export.
        """
        old_metric_type = config.get('metric_type')
        old_metric_labels = config.get('metric_labels')
        old_metric_description = config.get('metric_description')
        if old_metric_type:
            metric['alias'] = old_metric_type
            warnings.warn(
                '`metric_type` will be deprecated in favor of `metrics` '
                'in version 2.0.0, ', FutureWarning)
        if old_metric_labels:
            metric['labels'] = old_metric_labels
            warnings.warn(
                '`metric_labels` will be deprecated in favor of `metrics` '
                'in version 2.0.0, ', FutureWarning)
        if old_metric_description:
            warnings.warn(
                '`metric_description` will be deprecated in favor of `metrics` '
                'in version 2.0.0, ', FutureWarning)
            metric['description'] = old_metric_description
        return metric

    @abstractmethod
    def export_metric(self, data):
        """Abstract method to export a metric. Should be implemented by children
        classes."""
        raise NotImplementedError
