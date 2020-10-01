# Changelog

## [1.2.0](https://www.github.com/google/slo-generator/compare/v1.1.1...v1.2.0) (2020-10-01)


### Features

* Add exc_info to logging. ([#33](https://www.github.com/google/slo-generator/issues/33)) ([6e87d8d](https://www.github.com/google/slo-generator/commit/6e87d8da21d55ea6483fa2a754fd51434dd12b6e))
* Prometheus backend improvements ([#35](https://www.github.com/google/slo-generator/issues/35)) ([9231c9b](https://www.github.com/google/slo-generator/commit/9231c9bdf1974cbe91f8eb57a2d201c8ee7cd4f3))
* report template doc ([#16](https://www.github.com/google/slo-generator/issues/16)) ([20856fe](https://www.github.com/google/slo-generator/commit/20856fe83bf78053e814f774337cd1c749e486c5))


### Bug Fixes

* correct get_human_timestamp ([#43](https://www.github.com/google/slo-generator/issues/43)) ([cbf7ee9](https://www.github.com/google/slo-generator/commit/cbf7ee900dd2da7fd92a786aee48e0b2d18a1bfa))
* isort observed on imports ([#36](https://www.github.com/google/slo-generator/issues/36)) ([3a63e6e](https://www.github.com/google/slo-generator/commit/3a63e6e9662a9ebd99ee57fc2085fe0d95545ca8))
* Optimize performance on creating schemas when exporting to Big Query ([#23](https://www.github.com/google/slo-generator/issues/23)) ([d125c70](https://www.github.com/google/slo-generator/commit/d125c7009835f5cd2eab545af1a6efc530650696))

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
