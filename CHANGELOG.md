# Changelog

## [1.3.0](https://www.github.com/google/slo-generator/compare/v1.2.0...v1.3.0) (2020-10-16)


### Features

* add support for multiple metrics in metrics exporters ([#77](https://www.github.com/google/slo-generator/issues/77)) ([268058a](https://www.github.com/google/slo-generator/commit/268058ada37a61f1d797868017d1ee33d2e7c37f))


### Bug Fixes

* fail gracefully when no data in response ([#79](https://www.github.com/google/slo-generator/issues/79)) ([7265f25](https://www.github.com/google/slo-generator/commit/7265f25d205e186b77062d400b46c059337d9179))
* Metrics feature bugfix ([#84](https://www.github.com/google/slo-generator/issues/84)) ([9953c1a](https://www.github.com/google/slo-generator/commit/9953c1aa15c0883e23e8f1aaaecea051090a2529))
* SLO Report: cast good / bad count to int ([#82](https://www.github.com/google/slo-generator/issues/82)) ([8bbc552](https://www.github.com/google/slo-generator/commit/8bbc55282685bb570115bd3ec5275db33e83f4a9))
* strip URL to avoid bad API response [Dynatrace] ([#78](https://www.github.com/google/slo-generator/issues/78)) ([7320f8b](https://www.github.com/google/slo-generator/commit/7320f8b9ecf12831b29186d30d0e95e636dd24be))

## [1.2.0](https://www.github.com/google/slo-generator/compare/v1.1.1...v1.2.0) (2020-10-12)


### Features

* Add colored output ([#48](https://www.github.com/google/slo-generator/issues/48)) ([3e79325](https://www.github.com/google/slo-generator/commit/3e79325dc19f33f813186b2e9f77b088fcac85aa))
* Add Datadog integration ([#14](https://www.github.com/google/slo-generator/issues/14)) ([702ba18](https://www.github.com/google/slo-generator/commit/702ba182d4d5260017ec99153b94674f1058701b))
* add Dynatrace backend and exporter ([#62](https://www.github.com/google/slo-generator/issues/62)) ([412a0a9](https://www.github.com/google/slo-generator/commit/412a0a96dde09de34ed6565b25b06c7897cf8d85))
* Add exc_info to logging. ([#33](https://www.github.com/google/slo-generator/issues/33)) ([6e87d8d](https://www.github.com/google/slo-generator/commit/6e87d8da21d55ea6483fa2a754fd51434dd12b6e))
* Custom backend and exporter classes ([#34](https://www.github.com/google/slo-generator/issues/34)) ([2cf650b](https://www.github.com/google/slo-generator/commit/2cf650bec9bde5cd8e1a6691f25945f70ce47a24))
* Prometheus backend improvements ([#35](https://www.github.com/google/slo-generator/issues/35)) ([9231c9b](https://www.github.com/google/slo-generator/commit/9231c9bdf1974cbe91f8eb57a2d201c8ee7cd4f3))
* report template doc ([#16](https://www.github.com/google/slo-generator/issues/16)) ([20856fe](https://www.github.com/google/slo-generator/commit/20856fe83bf78053e814f774337cd1c749e486c5))


### Bug Fixes

* alerting_burn_rate_threshold should be float ([#63](https://www.github.com/google/slo-generator/issues/63)) ([8eacf7d](https://www.github.com/google/slo-generator/commit/8eacf7d5cb458c262e280b9f89b70612764eec9f))
* correct get_human_timestamp ([#43](https://www.github.com/google/slo-generator/issues/43)) ([cbf7ee9](https://www.github.com/google/slo-generator/commit/cbf7ee900dd2da7fd92a786aee48e0b2d18a1bfa))
* Datadog backend ratio as_count() ([#61](https://www.github.com/google/slo-generator/issues/61)) ([82cbd9f](https://www.github.com/google/slo-generator/commit/82cbd9fa76c5bd7f131d6ce514121f32f97c6c4f))
* isort observed on imports ([#36](https://www.github.com/google/slo-generator/issues/36)) ([3a63e6e](https://www.github.com/google/slo-generator/commit/3a63e6e9662a9ebd99ee57fc2085fe0d95545ca8))
* Optimize performance on creating schemas when exporting to Big Query ([#23](https://www.github.com/google/slo-generator/issues/23)) ([d125c70](https://www.github.com/google/slo-generator/commit/d125c7009835f5cd2eab545af1a6efc530650696))
* pin google dependencies (90b9810) ([#68](https://www.github.com/google/slo-generator/issues/68)) ([9eb887e](https://www.github.com/google/slo-generator/commit/9eb887e58b08e17050fa2c115784a8e96dd16c0a))
* resolve bug in SSM API for service autodetection ([#47](https://www.github.com/google/slo-generator/issues/47)) ([e050ac1](https://www.github.com/google/slo-generator/commit/e050ac17085f4f80a3356820eb87a125abca295c))
* restrict dep google-cloud-monitoring to 1.x.x ([#65](https://www.github.com/google/slo-generator/issues/65)) ([0e92ea3](https://www.github.com/google/slo-generator/commit/0e92ea3cd8b02b18b5db74afd2b5631c542b28ba))
* Set min_valid_events to 1 ([#66](https://www.github.com/google/slo-generator/issues/66)) ([cdc9cb1](https://www.github.com/google/slo-generator/commit/cdc9cb155e608bc5949cf8a20226041570062071))
* SLO Report validation ([#46](https://www.github.com/google/slo-generator/issues/46)) ([adb8a5c](https://www.github.com/google/slo-generator/commit/adb8a5ca6df525fb432f8c8c31aa7db7e12f728a))
* switch Dockerfile Python to 3.7 ([#72](https://www.github.com/google/slo-generator/issues/72)) ([96eeeff](https://www.github.com/google/slo-generator/commit/96eeeff0eee3d87d6c909d68c295f835dbf75a17))
* timestamp human in UTC format ([#70](https://www.github.com/google/slo-generator/issues/70)) ([f32369a](https://www.github.com/google/slo-generator/commit/f32369afb9c9f319cc3b8e6f5036b5680d6b08e3))


### Documentation

* Clarify Datadog docs for extra arguments ([#64](https://www.github.com/google/slo-generator/issues/64)) ([3d53e45](https://www.github.com/google/slo-generator/commit/3d53e450f023c0b9cc7722e77aeaf9cc96b0ffd0))
* Fix broken sample links ([#55](https://www.github.com/google/slo-generator/issues/55)) ([b72d936](https://www.github.com/google/slo-generator/commit/b72d93674e41139c05e60bbf5a8d5b5002d8410d))
* Improve docs ([#53](https://www.github.com/google/slo-generator/issues/53)) ([a8bdb0e](https://www.github.com/google/slo-generator/commit/a8bdb0e469703884cdb6154608437b2276a38cbe))
* remove window from Prometheus sample (automatically added) ([#57](https://www.github.com/google/slo-generator/issues/57)) ([4590908](https://www.github.com/google/slo-generator/commit/4590908e9f063cb634642e753f3de00b7dab157f))

### [1.1.1](https://www.github.com/google/slo-generator/compare/v1.1.0...v1.1.1) (2020-09-25)


### Bug Fixes

* Prometheus backend: allow complex expressions ([#11](https://www.github.com/google/slo-generator/issues/11)) ([17c3238](https://www.github.com/google/slo-generator/commit/17c3238aebf58d4b5602537398b31fb4228fa36a))
* unittests failing after 'fstr' style removed from pylint 2.5 ([dc4ca36](https://www.github.com/google/slo-generator/commit/dc4ca3622aca72c9c024edee8c310dfdc2047358))

## 1.1.0 (08-21-2020)

### Fixes
* Partition table for BigQuery database.

## 1.0.1 (07-20-2020)

### Fixes
* Frequent 500s in Stackdriver timeseries.write

## 1.0.0 (04-01-2020)

### Fixes
* Add unit tests for ElasticSearch
* Add unit tests for Prometheus
* Improve overall documentation
* Add unit tests for Stackdriver Service Monitoring

### Features
* Add Stackdriver Service Monitoring backend
* Reformat SLO reporting in a new dataclass
* Add working samples for each backend
* Reformat kwargs blocks in each backend to be less generic

## 0.2.1 (01-28-2020)

### Fixes
* Add Pylint tests and make them all pass
* Add test fixtures for Prometheus metrics backend

### Features
* Add support for Prometheus metrics backend
* Add support for ElasticSearch metrics backend
* Add feature to support SLO config folder instead of single file
* Add feature to support parsing environmental variables from YAML file
* Add support for filter_valid in Stackdriver backend
* Rewrite documentation

## 0.1.0 (08-30-2019)

### Features
* feat: Basic SLO monitoring with Stackdriver
