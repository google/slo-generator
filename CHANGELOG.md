# Changelog

### [1.1.1](https://www.github.com/google/slo-generator/compare/v1.1.0...v1.1.1) (2020-09-25)


### Bug Fixes

* Prometheus backend: allow complex expressions ([#11](https://www.github.com/google/slo-generator/issues/11)) ([17c3238](https://www.github.com/google/slo-generator/commit/17c3238aebf58d4b5602537398b31fb4228fa36a))
* release-please ([cca0f73](https://www.github.com/google/slo-generator/commit/cca0f7384099f6ce0b5fa6ff1a99453194b93442))
* release-please config to use GitHub app instead of robots ([#20](https://www.github.com/google/slo-generator/issues/20)) ([55a39af](https://www.github.com/google/slo-generator/commit/55a39afbabb4d18eba6c4278d0338be60a3d7e69))
* release-please existing changelog.md ([#8](https://www.github.com/google/slo-generator/issues/8)) ([81e2489](https://www.github.com/google/slo-generator/commit/81e2489b31d1bd381be07459f60fb21adfd25df3))
* release-please GitHub action ([#6](https://www.github.com/google/slo-generator/issues/6)) ([38096d0](https://www.github.com/google/slo-generator/commit/38096d0e756f7d37859a14530bc1a337fcb3ee16))
* setup.py for release-please ([aa58061](https://www.github.com/google/slo-generator/commit/aa58061ef57608a520de97308180470dc4f41393))
* unittests failing after 'fstr' style removed from pylint 2.5 ([dc4ca36](https://www.github.com/google/slo-generator/commit/dc4ca3622aca72c9c024edee8c310dfdc2047358))


### Reverts

* Revert "build: Add correct author to release-please (#18)" (#19) ([da5c200](https://www.github.com/google/slo-generator/commit/da5c200065bde228aa8993e48ddd7fa120dab017)), closes [#18](https://www.github.com/google/slo-generator/issues/18) [#19](https://www.github.com/google/slo-generator/issues/19)

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
