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
`report.py`
Report utilities.
"""

import logging
from dataclasses import asdict, dataclass, fields, field

from slo_generator import utils
from slo_generator.constants import COLORED_OUTPUT, MIN_VALID_EVENTS, NO_DATA

LOGGER = logging.getLogger(__name__)


@dataclass(init=False)
class SLOReport:
    """SLO report dataclass. Compute an SLO report out of an SLO config and an
    Error Budget Policy step.

    Args:
        config (dict): SLO configuration.
        step (dict): Error budget policy step configuration.
        timestamp (int): Timestamp.
        client (obj): Existing backend client.
        delete (bool): Backend delete action.
    """
    # pylint: disable=too-many-instance-attributes

    # Metadata
    metadata: dict = field(default_factory=dict)

    # SLO
    service_name: str
    feature_name: str
    slo_name: str
    slo_target: float
    slo_description: str
    sli_measurement: float = 0
    events_count: int = 0
    bad_events_count: int = 0
    good_events_count: int = 0
    gap: float

    # Error budget
    error_budget_policy_step_name: str
    error_budget_target: float
    error_budget_measurement: float
    error_budget_burn_rate: float
    error_budget_minutes: float
    error_budget_remaining_minutes: float
    error_minutes: float

    # Error Budget step config
    timestamp: int
    timestamp_human: str
    window: int
    alert: bool
    alerting_burn_rate_threshold: float
    consequence_message: str

    # Data validation
    valid: bool

    def __init__(self, config, step, timestamp, client=None, delete=False):

        # Init dataclass fields from SLO config and Error Budget Policy
        self.__set_fields(**config,
                          **step,
                          lambdas={
                              'slo_target': float,
                              'alerting_burn_rate_threshold': float
                          })
        # Set other fields
        self.window = int(step['measurement_window_seconds'])
        self.timestamp = int(timestamp)
        self.timestamp_human = utils.get_human_time(timestamp)
        self.valid = True
        self.metadata = config.get('metadata', {})

        # Get backend results
        data = self.run_backend(config, client=client, delete=delete)
        if not self._validate(data):
            self.valid = False
            return

        # Build SLO report
        self.build(step, data)

        # Post validation
        if not self._post_validate():
            self.valid = False

    def build(self, step, data):
        """Compute all data necessary for the SLO report.

        Args:
            step (dict): Error Budget Policy step configuration.
            data (obj): Backend data.

        See https://landing.google.com/sre/workbook/chapters/implementing-slos/
        for details on the calculations.
        """
        info = self.__get_info()
        LOGGER.debug(f"{info} | SLO report starting ...")

        # SLI, Good count, Bad count, Gap from backend results
        sli, good_count, bad_count = self.get_sli(data)
        gap = sli - self.slo_target

        # Error Budget calculations
        eb_target = 1 - self.slo_target
        eb_value = 1 - sli
        eb_remaining_minutes = self.window * gap / 60
        eb_target_minutes = self.window * eb_target / 60
        eb_minutes = self.window * eb_value / 60
        if eb_target == 0:
            eb_burn_rate = 0
        else:
            eb_burn_rate = round(eb_value / eb_target, 1)

        # Alert boolean on burn rate excessive speed.
        alert = eb_burn_rate > self.alerting_burn_rate_threshold

        # Manage alerting message.
        if alert:
            consequence_message = step['overburned_consequence_message']
        elif eb_burn_rate <= 1:
            consequence_message = step['achieved_consequence_message']
        else:
            consequence_message = \
                'Missed for this measurement window, but not enough to alert'

        # Set fields in dataclass.
        self.__set_fields(sli_measurement=sli,
                          good_events_count=int(good_count),
                          bad_events_count=int(bad_count),
                          events_count=int(good_count + bad_count),
                          gap=gap,
                          error_budget_target=eb_target,
                          error_budget_measurement=eb_value,
                          error_budget_burn_rate=eb_burn_rate,
                          error_budget_remaining_minutes=eb_remaining_minutes,
                          error_budget_minutes=eb_target_minutes,
                          error_minutes=eb_minutes,
                          alert=alert,
                          consequence_message=consequence_message)

    def run_backend(self, config, client=None, delete=False):
        """Get appropriate backend method from SLO configuration and run it on
        current SLO config and Error Budget Policy step.

        Args:
            config (dict): SLO configuration.
            client (obj, optional): Backend client initiated beforehand.
            delete (bool, optional): Set to True if we're running a delete
                action.

        Returns:
            obj: Backend data.
        """
        info = self.__get_info()

        # Grab backend class and method dynamically.
        cfg = config.get('backend', {})
        cls = cfg.get('class')
        method = cfg.get('method')
        excluded_keys = ['class', 'method', 'measurement']
        backend_cfg = {k: v for k, v in cfg.items() if k not in excluded_keys}
        instance = utils.get_backend_cls(cls)(client=client, **backend_cfg)
        method = getattr(instance, method)
        LOGGER.debug(f'{info} | '
                     f'Using backend {cls}.{method.__name__} (from '
                     f'SLO config file).')

        # Delete mode activation.
        if delete and hasattr(instance, 'delete'):
            method = instance.delete
            LOGGER.warning(f'{info} | Delete mode enabled.')

        # Run backend method and return results.
        data = method(self.timestamp, self.window, config)
        LOGGER.debug(f'{info} | Backend response: {data}')
        return data

    def get_sli(self, data):
        """Compute SLI value and good / bad counts from the backend result.

        Some backends (e.g: Prometheus) are computing and returning the SLI
        value directly, others are sending a tuple (good_count, bad_count) and
        SLI value is computed from there.

        Args:
            data (obj): Backend data.

        Returns:
            tuple: A tuple of 3 values to unpack (float, int, int).
                float: SLI value.
                int: Good events count.
                int: Bad events count.

        Raises:
            Exception: When the backend does not return a proper result.
        """
        info = self.__get_info()
        if isinstance(data, tuple):  # good, bad count
            good_count, bad_count = data
            if good_count == NO_DATA:
                good_count = 0
            if bad_count == NO_DATA:
                bad_count = 0
            LOGGER.debug(f"{info} | Good: {good_count} | Bad: {bad_count}")
            sli_measurement = round(good_count / (good_count + bad_count), 6)
        else:  # sli value
            sli_measurement = round(data, 6)
            good_count, bad_count = NO_DATA, NO_DATA
        return sli_measurement, good_count, bad_count

    def to_json(self):
        """Serialize dataclass to JSON."""
        return asdict(self)

    # pylint: disable=too-many-return-statements
    def _validate(self, data):
        """Validate backend results. Invalid data will result in SLO report not
        being built.

        Args:
            data (obj): Backend result (expecting tuple, float, or int).

        Returns:
            bool: True if data is valid, False
        """
        info = self.__get_info()

        # Backend data type should be one of tuple, float, or int
        if not isinstance(data, (tuple, float, int)):
            LOGGER.error(
                f'{info} | Backend method returned an object of type '
                f'{type(data).__name__}. It should instead return a tuple '
                '(good_count, bad_count) or a numeric SLI value (float / int).'
            )
            return False

        # Good / Bad tuple
        if isinstance(data, tuple):

            # Tuple length should be 2
            if len(data) != 2:
                LOGGER.error(
                    f'{info} | Backend method returned a tuple with {len(data)}'
                    ' elements. Expected 2 elements.')
                return False
            good, bad = data

            # Tuple should contain only elements of type int or float
            if not all(isinstance(n, (float, int)) for n in data):
                LOGGER.error('f{info} | Backend method returned'
                             'a tuple with some elements having '
                             'a type different than float / int')
                return False

            # Tuple should not contain any element with value None.
            if good is None or bad is None:
                LOGGER.error(f'{info} | Backend method returned a valid tuple '
                             '{data} but one of the values is None.')
                return False

            # Tuple should not have NO_DATA everywhere
            if (good + bad) == (NO_DATA, NO_DATA):
                LOGGER.error(f'{info} | Backend method returned a valid '
                             f'tuple {data} but the good and bad count '
                             'is NO_DATA (-1).')
                return False

            # Tuple should not have elements where the sum is inferior to our
            # minimum valid events threshold
            if (good + bad) < MIN_VALID_EVENTS:
                LOGGER.error(f"{info} | Not enough valid events found | "
                             f"Minimum valid events: {MIN_VALID_EVENTS}")
                return False

        # Check backend float / int value
        if isinstance(data, (float, int)) and data == NO_DATA:
            LOGGER.error(f'{info} | Backend returned NO_DATA (-1).')
            return False

        # Check backend None
        if data is None:
            LOGGER.error(f'{info} | Backend returned None.')
            return False

        return True

    def _post_validate(self):
        """Validate report after build."""

        # SLI measurement should be 0 <= x <= 1
        if not 0 <= self.sli_measurement <= 1:
            LOGGER.error(
                f"SLI is not between 0 and 1 (value = {self.sli_measurement})")
            return False

        return True

    def __set_fields(self, lambdas={}, **kwargs):
        """Set all fields in dataclasses from configs passed and apply function
        on values whose key match one in the dictionaries.

        Args:
            lambdas (dict): Dict {key: function} to apply a function on certain
            kwargs (dict): Dict of key / values to set in dataclass.
        """
        names = set(f.name for f in fields(self))
        for name in names:
            if name not in kwargs:
                continue
            value = kwargs[name]
            if name in lambdas.keys():
                value = lambdas[name](value)
            setattr(self, name, value)

    def __get_info(self):
        """Get info message describing current SLO andcurrent Error Budget Step.
        """
        slo_full_name = self.__get_slo_full_name()
        step_name = self.error_budget_policy_step_name
        return f"{slo_full_name :<32} | {step_name :<8}"

    def __get_slo_full_name(self):
        """Compile full SLO name from SLO configuration.

        Returns:
            str: Full SLO name.
        """
        return f'{self.service_name}/{self.feature_name}/{self.slo_name}'

    def __str__(self):
        report = self.to_json()
        info = self.__get_info()
        slo_target_per = self.slo_target * 100
        sli_per = round(self.sli_measurement * 100, 6)
        gap = round(self.gap * 100, 2)
        gap_str = str(gap)
        if gap >= 0:
            gap_str = f'+{gap}'
        sli_str = (f'SLI: {sli_per:<7} % | SLO: {slo_target_per} % | '
                   f'Gap: {gap_str:<6}%')
        result_str = ("BR: {error_budget_burn_rate:<2} / "
                      "{alerting_burn_rate_threshold} | "
                      "Alert: {alert:<1} | Good: {good_events_count:<8} | "
                      "Bad: {bad_events_count:<8}").format_map(report)
        full_str = f'{info} | {sli_str} | {result_str}'
        if COLORED_OUTPUT == 1:
            if self.alert:
                full_str = utils.Colors.FAIL + full_str + utils.Colors.ENDC
            else:
                full_str = utils.Colors.OKGREEN + full_str + utils.Colors.ENDC
        return full_str
