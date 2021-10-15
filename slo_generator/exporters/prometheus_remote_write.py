"""
`prometheus_remote_write.py`
Prometheus Remote Write exporter class.
"""
import logging
import re
import time
from typing import Dict, Tuple

import requests
import snappy
from slo_generator.exporters.base import MetricsExporter
from slo_generator.exporters.gen.remote_pb2 import (
    WriteRequest,
)
from slo_generator.exporters.gen.types_pb2 import (
    Label,
)

LOGGER = logging.getLogger(__name__)
DEFAULT_REMOTE_WRITE_JOB = 'slo-generator'


# pylint: disable=too-many-instance-attributes
class PrometheusRemoteWriteExporter(MetricsExporter):
    """
    Prometheus Remote Write exporter class.

    Args:
        url: endpoint URL where to send the data (Required)
        username: username for Basic Auth (Optional)
        password: password for Basic Auth (Optional)
        headers: Dict of extra headers to add to remote write request
                                                               (Optional)
        timeout: timeout for writes in seconds, defaults to 30 (Optional)
        tls_config: configuration for remote write TLS settings (Optional)
    """

    REQUIRED_FIELDS = ['url']
    OPTIONAL_FIELDS = [
        'username',
        'password',
        'headers',
        'timeout',
        'tls_config',
    ]

    def __init__(self) -> None:

        self.url: str = None
        self.username: str = None
        self.password: str = None
        self.headers: Dict[str, str] = None
        self.timeout: int = None
        self.tls_config: Dict[str, str] = None
        self.basic_auth: Dict[str, str] = None
        self.job_name: str = None

    def export_metric(self, data: Dict) -> requests.Response:
        """Export data to Prometheus Remote Write.

        Args:
            data (dict): Metric data.

        Returns:
            Response: python-requests Response object which holds the result of
                the HTTP POST to Remote Write URL
        """

        self._export_init(data)
        timeseries = self.create_timeseries(data)
        headers = self._build_headers()
        return self._send_message(timeseries, headers)

    # pylint: disable=too-many-branches
    def _export_init(self, data: Dict) -> None:
        if 'url' not in data:
            raise ValueError('remote write URL required')
        self.url = data['url']

        self.job_name = data.get('job', DEFAULT_REMOTE_WRITE_JOB)

        if 'username' in data and 'password' not in data:
            raise ValueError('must have password for Basic Auth')
        if 'password' in data and 'username' not in data:
            raise ValueError('must have username for Basic Auth')
        if 'username' in data and 'password' in data:
            self.basic_auth = {
                'username': data['username'],
                'password': data['password'],
            }

        if 'headers' in data:
            if not isinstance(data['headers'], dict):
                raise ValueError('additional headers must be a Dict[str, str]')
            self.headers = data['headers']

        if 'timeout' in data:
            try:
                int(data['timeout'])
            except ValueError as err:
                raise ValueError('timeout must be an integer') from err
            if int(data['timeout']) <= 0:
                raise ValueError('timeout must be >0')
            self.timeout = int(data['timeout'])

        if 'tls_config' in data:
            if not isinstance(data['tls_config'], dict):
                raise ValueError('tls_config must be a Dict[str,str]')
            config = {}
            if 'ca_file' in data['tls_config']:
                config['ca_file'] = data['tls_config']['ca_file']
            if (
                'cert_file' in data['tls_config']
                and 'key_file' in data['tls_config']
            ):
                config['cert_file'] = data['tls_config']['cert_file']
                config['key_file'] = data['tls_config']['key_file']
            elif (
                'cert_file' in data['tls_config']
                and 'key_file' not in data['tls_config']
            ):
                raise ValueError(
                    'both cert and key are required for custom TLS config'
                )
            if 'insecure_skip_verify' in data['tls_config']:
                if not isinstance(
                    data['tls_config']['insecure_skip_verify'], bool
                ):
                    raise ValueError('insecure_skip_verify must be a boolean')
                config['insecure_skip_verify'] = data['tls_config'][
                    'insecure_skip_verify'
                ]
            self.tls_config = config

    # pylint: disable=no-member, no-self-use
    def create_timeseries(self, data: Dict) -> bytes:
        """Create Prometheus timeseries.

        Args:
            data(dict): Metric data.

        Returns:
            TimeSeries object: Metric descriptor.
        """
        name = data['name']
        value = data['value']
        labelkeyvalues = data['labels']

        write_request = WriteRequest()
        timeseries = write_request.timeseries.add()

        seen = set()

        def add_label(label_name: str, label_value: str) -> None:
            # restrict to only alphanumeric chars and underscore
            label_name = re.sub('[^\\w_]', '_', label_name)
            if label_name not in seen:
                label = Label()
                label.name = label_name
                label.value = label_value
                timeseries.labels.append(label)
                seen.add(label_name)
            else:
                # pylint: disable=line-too-long
                LOGGER.warning(
                    f'Duplicate label with name {label_name} and value {label_value}'  # noqa: E501
                )

        # the __name__ label is special: its value is the metric_name
        add_label(label_name='__name__', label_value=name)
        # add the `job` label
        add_label(label_name='job', label_value=self.job_name)

        for label_key, label_value in labelkeyvalues.items():
            add_label(label_key, label_value)

        sample = timeseries.samples.add()
        # we need to manage timestamps ourselves because remote write is a WAL
        sample.timestamp = int(time.time() * 1000)
        sample.value = value

        timeseries.samples.append(sample)

        serialized = write_request.SerializeToString()
        return snappy.compress(serialized)

    def _build_headers(self) -> Dict[str, str]:
        headers = {
            'Content-Encoding': 'snappy',
            'Content-Type': 'application/x-protobuf',
            'X-Prometheus-Remote-Write-Version': '0.1.0',
            'User-Agent': 'slo-generator',
        }
        if self.headers:
            for header_name, header_value in self.headers.items():
                headers[header_name] = header_value
        return headers

    def _send_message(
        self, message: bytes, headers: Dict[str, str]
    ) -> requests.Response:
        auth: Tuple[str, str] = None
        if self.basic_auth:
            auth = (
                self.basic_auth['username'],
                self.basic_auth['password'],
            )

        cert: Tuple[str, str] = None
        verify = True

        if self.tls_config:
            if 'ca_file' in self.tls_config:
                verify = self.tls_config['ca_file']
            elif 'insecure_skip_verify' in self.tls_config:
                if self.tls_config['insecure_skip_verify']:
                    verify = False
            if (
                'cert_file' in self.tls_config
                and 'key_file' in self.tls_config
            ):
                cert = (
                    self.tls_config['cert_file'],
                    self.tls_config['key_file'],
                )

        try:
            response = requests.post(
                self.url,
                data=message,
                headers=headers,
                auth=auth,
                timeout=self.timeout,
                cert=cert,
                verify=verify,
            )
            if not response.ok:
                response.raise_for_status()
            LOGGER.debug(response.content)
            return response
        except requests.exceptions.RequestException as err:
            LOGGER.error(f'remote write POST failed: {err}')
            return err.response
