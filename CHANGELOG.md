# Changelog

## [2.5.2](https://github.com/google/slo-generator/compare/v2.5.1...v2.5.2) (2023-11-10)


### Bug Fixes

* add `query_bad` option to Datadog backend ([#377](https://github.com/google/slo-generator/issues/377)) ([6ecc728](https://github.com/google/slo-generator/commit/6ecc72803a6bd7dbfe2035e978cc3c2b0a3349f3))

## [2.5.1](https://github.com/google/slo-generator/compare/v2.5.0...v2.5.1) (2023-10-13)


### Bug Fixes

* get_human_time() should not hard-code the human-readable timezone ([#350](https://github.com/google/slo-generator/issues/350)) ([1948694](https://github.com/google/slo-generator/commit/194869473887c22948b1029bcbfda3e5b535c160))

## [2.5.0](https://github.com/google/slo-generator/compare/v2.4.0...v2.5.0) (2023-10-11)


### Features

* add support for OpenSearch backend ([#348](https://github.com/google/slo-generator/issues/348)) ([f7bb0d9](https://github.com/google/slo-generator/commit/f7bb0d90850b7e56edd3d84091accda571c891e8))
* upgrade google-* packages ([#354](https://github.com/google/slo-generator/issues/354)) ([e18fe5d](https://github.com/google/slo-generator/commit/e18fe5d5d295be7b4332a1004c06a3f3f3cd74de))


### Bug Fixes

* avoid CVEs reported by `safety check` ([#353](https://github.com/google/slo-generator/issues/353)) ([fb35d87](https://github.com/google/slo-generator/commit/fb35d870f80a86d7dcc7aae05725e5cf713b11a8))

## [2.4.0](https://github.com/google/slo-generator/compare/v2.3.4...v2.4.0) (2023-06-21)


### Features

* add support for Splunk backend ([#335](https://github.com/google/slo-generator/issues/335)) ([5171318](https://github.com/google/slo-generator/commit/51713189f8bf473e7e384ed46653640f282c0dcb))


### Bug Fixes

* bump version of iSort to avoid non-deterministic error during pre-commit checks ([5542a06](https://github.com/google/slo-generator/commit/5542a065d5ca3d255b84ea20bebe42ff5d8c09aa))

## [2.3.4](https://github.com/google/slo-generator/compare/v2.3.3...v2.3.4) (2023-02-27)


### Bug Fixes

* convert timestamp to UTC in Cloud Monitoring MQL backend ([#331](https://github.com/google/slo-generator/issues/331)) ([0b7cbcc](https://github.com/google/slo-generator/commit/0b7cbcc6ef9bf36277cca316a5255993824a7f46))
* implicit Optional type hints are now forbidden (cf. PEP 484) ([#301](https://github.com/google/slo-generator/issues/301)) ([c1351e0](https://github.com/google/slo-generator/commit/c1351e065a3c0767ce8a50460c98f1ebb42326f6))
* **lint:** replace too generic exceptions (Exception) with more specific ones (ValueError) ([d2eadbf](https://github.com/google/slo-generator/commit/d2eadbf5a3f5ce7032c36c0446c914dcd1c55d0f))
* wrong environment variable name for `--target` option in `api` command ([#320](https://github.com/google/slo-generator/issues/320)) ([3303735](https://github.com/google/slo-generator/commit/3303735b28803bf92905554dc501e2772c707232))

## [2.3.3](https://github.com/google/slo-generator/compare/v2.3.2...v2.3.3) (2022-11-02)


### Bug Fixes

* compute the time horizon of MQL requests more accurately so they return the same results as MQF requests ([#290](https://github.com/google/slo-generator/issues/290)) ([41b814b](https://github.com/google/slo-generator/commit/41b814b6119f7a43b229317f8da0f4006c987656))

## [2.3.2](https://github.com/google/slo-generator/compare/v2.3.1...v2.3.2) (2022-10-29)


### Bug Fixes

* remove calls to list and create metric descriptors in Cloud Monitoring exporter to prevent Quota Exceeded errors ([#286](https://github.com/google/slo-generator/issues/286)) ([0a6a0fb](https://github.com/google/slo-generator/commit/0a6a0fb75d6c83deddbf81288c4d020e22bbd6d5))


### Documentation

* update docs and samples with all backends ([#283](https://github.com/google/slo-generator/issues/283)) ([61f2f32](https://github.com/google/slo-generator/commit/61f2f3291671fbfc1afc607255c1366f90c55b98))

## [2.3.1](https://github.com/google/slo-generator/compare/v2.3.0...v2.3.1) (2022-10-27)


### Bug Fixes

* migrate `cloud_service_monitoring` backend to `google-cloud-monitoring` v2 (with breaking changes) ([#280](https://github.com/google/slo-generator/issues/280)) ([affd157](https://github.com/google/slo-generator/commit/affd157fc5b1e253a3e6f02baa22a100b4da244d))


### Documentation

* document Cloud Monitoring MQL backend ([#277](https://github.com/google/slo-generator/issues/277)) ([8c931cd](https://github.com/google/slo-generator/commit/8c931cd69c8a1be5c59e8b431271da210ea986d7))
* refine development workflow instructions ([#275](https://github.com/google/slo-generator/issues/275)) ([2a35754](https://github.com/google/slo-generator/commit/2a357546d0e6019110a76c7238349a92677cabd1))

## [2.3.0](https://github.com/google/slo-generator/compare/v2.2.0...v2.3.0) (2022-10-24)


### Features

* add Cloud Monitoring MQL backend ([#245](https://github.com/google/slo-generator/issues/245)) ([159f4d5](https://github.com/google/slo-generator/commit/159f4d5f93fd389f991fd1df3981ab28a2a80572))
* add Prometheus Self exporter for API mode ([#209](https://github.com/google/slo-generator/issues/209)) ([53c0fdf](https://github.com/google/slo-generator/commit/53c0fdfb1030b84ca7ec11e2c54ab2d22cb046f4))
* add pytype linting ([#249](https://github.com/google/slo-generator/issues/249)) ([b622d09](https://github.com/google/slo-generator/commit/b622d098a1f489988c8f4b2e92f52e87cad703bc))


### Bug Fixes

* add timeFrame to retrieve_slo dynatrace ([#212](https://github.com/google/slo-generator/issues/212)) ([2db0140](https://github.com/google/slo-generator/commit/2db01404e1b9e9d216a26f987fbc5531092312ea))
* make unit tests pass again with elasticsearch 8.x client ([#223](https://github.com/google/slo-generator/issues/223)) ([39dd26c](https://github.com/google/slo-generator/commit/39dd26cb7197fdae0c4cb6f4fbc6808053615a37))
* prevent gcloud crash with python 3.10 during release workflow ([39a257e](https://github.com/google/slo-generator/commit/39a257e7244c53990063fb63f0edf88cfbb30681))
* remove useless and unknown Pylint options ([#247](https://github.com/google/slo-generator/issues/247)) ([5053251](https://github.com/google/slo-generator/commit/50532511b4de13becabd5b78d92eb32d59fefde7))
* support custom exporters ([#235](https://github.com/google/slo-generator/issues/235)) ([b72b8f4](https://github.com/google/slo-generator/commit/b72b8f46d33b42ceb805c45eccdd7275c5495dd9))
* update "Development Status" classifier ([c82eea3](https://github.com/google/slo-generator/commit/c82eea3a843dadf8720e8c828b2eaed0064eee4e))


### Documentation

* add missing 'method' field in readme ([#213](https://github.com/google/slo-generator/issues/213)) ([5d2a9a0](https://github.com/google/slo-generator/commit/5d2a9a00ba3cb45b2fe1d5144e4aee735abaf655))
* add Python 3.9 classifier ([#226](https://github.com/google/slo-generator/issues/226)) ([83c36b9](https://github.com/google/slo-generator/commit/83c36b93693d4d6cb231ba38c5ea3ea0c8e01c2a))
* document how to write and configure filters in Cloud Monitoring provider ([#266](https://github.com/google/slo-generator/issues/266)) ([29ab2e1](https://github.com/google/slo-generator/commit/29ab2e1dc043bbaa5203c2b5219e474d292fe7f9))

## [2.2.0](https://www.github.com/google/slo-generator/compare/v2.1.0...v2.2.0) (2022-02-02)


### Features

* add batch mode, better error reporting, cloud run docs ([#204](https://www.github.com/google/slo-generator/issues/204)) ([d305a63](https://www.github.com/google/slo-generator/commit/d305a63d2b3566815b6be6a04605a4d2beddf197))


### Bug Fixes

* alerting burn rate threshold null in BQ ([#201](https://www.github.com/google/slo-generator/issues/201)) ([d25f0f3](https://www.github.com/google/slo-generator/commit/d25f0f397fbe79f6fd265a5905952743f9a7a9ff))
* custom backend path for integration tests ([#203](https://www.github.com/google/slo-generator/issues/203)) ([7268dc1](https://www.github.com/google/slo-generator/commit/7268dc1d843d3cf8bf3388f42590e6e6fba4ed86))
* dynatrace slo import ([#198](https://www.github.com/google/slo-generator/issues/198)) ([df86234](https://www.github.com/google/slo-generator/commit/df86234db3dc14e91c7ebc31c29974e9d312834d))
* remove row_ids to solve de-duplication issues ([#200](https://www.github.com/google/slo-generator/issues/200)) ([56d9b9b](https://www.github.com/google/slo-generator/commit/56d9b9bc551e1e37f6070ed1fe61cbaab1620f39))


### Documentation

* clarify API export-only docs ([#206](https://www.github.com/google/slo-generator/issues/206)) ([7c449c3](https://www.github.com/google/slo-generator/commit/7c449c32321f0fff3690c6177e3a85340afff2c8))

## [2.1.0](https://www.github.com/google/slo-generator/compare/v2.0.1...v2.1.0) (2022-01-19)


### Features

* search SLO configs in subdirectories ([#181](https://www.github.com/google/slo-generator/issues/181)) ([575f2f7](https://www.github.com/google/slo-generator/commit/575f2f701d43e8dfbb9505b98a81ab76dde79d50))


### Bug Fixes

* better exception handling and error logging ([#187](https://www.github.com/google/slo-generator/issues/187)) ([0826f11](https://www.github.com/google/slo-generator/commit/0826f11533f04395b353829ea877999d390ffddf))
* bigquery exporter lint ([#183](https://www.github.com/google/slo-generator/issues/183)) ([9710b06](https://www.github.com/google/slo-generator/commit/9710b068ea8bc419c571b90ef11ec2469c3c511a))
* dependency issue with google-cloud-monitoring for the bazillionth time ([#191](https://www.github.com/google/slo-generator/issues/191)) ([1a613f3](https://www.github.com/google/slo-generator/commit/1a613f3112e1e243679f4c6ec2e5f62b232c3331))
* Set Python version to 3.9 ([#179](https://www.github.com/google/slo-generator/issues/179)) ([c433fb9](https://www.github.com/google/slo-generator/commit/c433fb9588660cc4f6b1b724b0b896988a96b9c6))


### Reverts

* Revert "feat: search SLO configs in subdirectories (#181)" (#189) ([08b13e7](https://www.github.com/google/slo-generator/commit/08b13e712a6b385972f5c641ee32ad3173e73865)), closes [#181](https://www.github.com/google/slo-generator/issues/181) [#189](https://www.github.com/google/slo-generator/issues/189)


### Documentation

* correct bigquery.md ([#182](https://www.github.com/google/slo-generator/issues/182)) ([3ba32a1](https://www.github.com/google/slo-generator/commit/3ba32a15923660e0f0f82e341cea782d8e300d59))
* How to define a latency SLI-SLO from an exponential distribution metric in Cloud Monitoring ([#56](https://www.github.com/google/slo-generator/issues/56)) ([8346c47](https://www.github.com/google/slo-generator/commit/8346c479471ab57f0630255876eb7ba656544ab6))
* improve datastudio md ([#54](https://www.github.com/google/slo-generator/issues/54)) ([4c8e8a2](https://www.github.com/google/slo-generator/commit/4c8e8a21d7e5d261a37b747b95ee7ce13032a722))

### [2.0.1](https://www.github.com/google/slo-generator/compare/v2.0.0...v2.0.1) (2021-09-29)


### Bug Fixes

* yaml loader security issue ([#173](https://www.github.com/google/slo-generator/issues/173)) ([36318be](https://www.github.com/google/slo-generator/commit/36318beab1b85d14bb860e45bea186b184690d5d))


### Documentation

* add cURL example ([4d6c215](https://www.github.com/google/slo-generator/commit/4d6c215c88a968d61f472c296b281495748a0f84))
* update badges ([b63fac8](https://www.github.com/google/slo-generator/commit/b63fac866dff0e6fd85c4b961330b9201e57ea18))
* update readme ([50ce1bf](https://www.github.com/google/slo-generator/commit/50ce1bf81d7c6a97da52cf167b1d3ee8100ddd90))

## [2.0.0](https://www.github.com/google/slo-generator/compare/v1.5.1...v2.0.0) (2021-09-28)


### ⚠ BREAKING CHANGES

* Upgrade slo-generator CLI to Click library (#131)
* Support slo-generator config v2 format (core changes) (#126)
* Split dependencies by backend (#129)

### Features

* add Dynatrace method to query SLO ([#116](https://www.github.com/google/slo-generator/issues/116)) ([0148e99](https://www.github.com/google/slo-generator/commit/0148e99c5830081e59db6321767bef3c84bddad4))
* Add migrator for v1 to v2 migration ([#127](https://www.github.com/google/slo-generator/issues/127)) ([796442e](https://www.github.com/google/slo-generator/commit/796442e92e35d2ceeecd12635a6e1a057791427b))
* Add slo-generator Functions Framework API ([#130](https://www.github.com/google/slo-generator/issues/130)) ([ab1d57c](https://www.github.com/google/slo-generator/commit/ab1d57c8a1b4ad1c7183e03f1cd98db136306ef2))
* add slo-generator JSON schemas ([#169](https://www.github.com/google/slo-generator/issues/169)) ([33e461b](https://www.github.com/google/slo-generator/commit/33e461b7aa34ce533f1e50b1f2c8ff1048f613f2))
* Split dependencies by backend ([#129](https://www.github.com/google/slo-generator/issues/129)) ([c640a1d](https://www.github.com/google/slo-generator/commit/c640a1d9235c9cf24243beabc5609efecbcc9d62))
* Support slo-generator config v2 format (core changes) ([#126](https://www.github.com/google/slo-generator/issues/126)) ([bf5e6b4](https://www.github.com/google/slo-generator/commit/bf5e6b4167a7081f03ca373c11e06be70da66fd5))
* Upgrade slo-generator CLI to Click library ([#131](https://www.github.com/google/slo-generator/issues/131)) ([5b2635b](https://www.github.com/google/slo-generator/commit/5b2635b05e6d7434f54eb95fb4d3445d88ce29f0))


### Bug Fixes

* Migrate sample configurations to v2 ([#128](https://www.github.com/google/slo-generator/issues/128)) ([bafaf51](https://www.github.com/google/slo-generator/commit/bafaf5178b827ece5da7d204e8dc982916a1ad5f))
* Migrator and dependency issues fixes ([#160](https://www.github.com/google/slo-generator/issues/160)) ([51b956b](https://www.github.com/google/slo-generator/commit/51b956b85e7769725c46be3579cc51c4b02bd333))
* migrator glob catch .yml, .yaml and .json ext ([0d44dc6](https://www.github.com/google/slo-generator/commit/0d44dc6f64dba2e6e263699c658ff88864e367a3))
* migrator not listing all files ([#167](https://www.github.com/google/slo-generator/issues/167)) ([c34ba68](https://www.github.com/google/slo-generator/commit/c34ba6881b38e713a3d0eb6ade7026a0ea0bd193))
* migrator target path locations ([#171](https://www.github.com/google/slo-generator/issues/171)) ([2f7a07d](https://www.github.com/google/slo-generator/commit/2f7a07d49f40c46a6b63f82195914245aba73a6f))
* Minor v2 fixes ([#142](https://www.github.com/google/slo-generator/issues/142)) ([2d48d61](https://www.github.com/google/slo-generator/commit/2d48d617e124f58e307d9ec64da44e67df9bb611))
* Support JSON or text data in API ([#147](https://www.github.com/google/slo-generator/issues/147)) ([93a8c9f](https://www.github.com/google/slo-generator/commit/93a8c9f90626460dbe96567f3c3cd6920dbefd78))
* update migrator to fail softly when invalid YAMLs are found ([#154](https://www.github.com/google/slo-generator/issues/154)) ([507302e](https://www.github.com/google/slo-generator/commit/507302e69f7065c5e114c9d9a72fa22f648cf83b))
* v2 deployment fixes ([#143](https://www.github.com/google/slo-generator/issues/143)) ([1f03ee2](https://www.github.com/google/slo-generator/commit/1f03ee226de29249bccb854ae097708be5aed709))


### Documentation

* Add Cloudrun docs ([#165](https://www.github.com/google/slo-generator/issues/165)) ([223830b](https://www.github.com/google/slo-generator/commit/223830bb2395076f455fcd17ce1f9a9ebd1b6579))
* add pointers to v1 docs and v1 to v2 migration ([e96c625](https://www.github.com/google/slo-generator/commit/e96c62516dad50786766db484eb3f2da9eee7dc2))
* Update documentation for v2 ([#133](https://www.github.com/google/slo-generator/issues/133)) ([0a9cd38](https://www.github.com/google/slo-generator/commit/0a9cd38a507c9559ecb97b6d55eca3b8bc9d20bc))

### [1.5.1](https://www.github.com/google/slo-generator/compare/v1.5.0...v1.5.1) (2021-02-12)


### Bug Fixes

* broken setuptools ([#117](https://www.github.com/google/slo-generator/issues/117)) ([f1fa346](https://www.github.com/google/slo-generator/commit/f1fa346d2b8ae618b85a44d3683aa04377bba85f))

## [1.5.0](https://www.github.com/google/slo-generator/compare/v1.4.1...v1.5.0) (2021-01-12)


### Features

* support Datadog monitor-based SLOs ([#112](https://www.github.com/google/slo-generator/issues/112)) ([43a7896](https://www.github.com/google/slo-generator/commit/43a7896e022b0c8314d8be4150f6113859a169fa))

### [1.4.1](https://www.github.com/google/slo-generator/compare/v1.4.0...v1.4.1) (2020-11-30)


### Bug Fixes

* replace PUT by POST for prometheus exporter (push-gateway) ([#109](https://www.github.com/google/slo-generator/issues/109)) ([0002456](https://www.github.com/google/slo-generator/commit/00024565ba9b5c713c2e122930a78ee22eb5122a))


### Documentation

* update readme with metadata info ([#107](https://www.github.com/google/slo-generator/issues/107)) ([6e078f8](https://www.github.com/google/slo-generator/commit/6e078f849c1de8cb908d7a065cb0f66449e95e57))

## [1.4.0](https://www.github.com/google/slo-generator/compare/v1.3.2...v1.4.0) (2020-11-12)


### Features

* Add custom metadata to SLO configs ([#103](https://www.github.com/google/slo-generator/issues/103)) ([e53bdda](https://www.github.com/google/slo-generator/commit/e53bddaee1f7811ebedd93ff2b8b5fcf4ab875fb))


### Bug Fixes

* Add `threshold` method to Dynatrace backend ([#87](https://www.github.com/google/slo-generator/issues/87)) ([a36c6eb](https://www.github.com/google/slo-generator/commit/a36c6eb930ddf64791ca02ab3404b35e6c24b59a))
* add post validation of SLI value ([#95](https://www.github.com/google/slo-generator/issues/95)) ([3c75da4](https://www.github.com/google/slo-generator/commit/3c75da465d0d5077fb1fe67aee866c82f760c2f0))
* default metrics ([#97](https://www.github.com/google/slo-generator/issues/97)) ([34bc2b7](https://www.github.com/google/slo-generator/commit/34bc2b78ccbae742cbaf03a1e2d359374d3a1c21))
* Duplicated project_id in Stackdriver exporter metric ([#100](https://www.github.com/google/slo-generator/issues/100)) ([b1c274d](https://www.github.com/google/slo-generator/commit/b1c274d26f5f8d92ac3fa7a0b3555c8721865fab))
* metrics bug with multiple exporters ([#105](https://www.github.com/google/slo-generator/issues/105)) ([0ee5e05](https://www.github.com/google/slo-generator/commit/0ee5e05bf9b4a25acbfd5eb2fe4a1a176c935eba))
* metrics exporters bugfixes ([#106](https://www.github.com/google/slo-generator/issues/106)) ([bccb407](https://www.github.com/google/slo-generator/commit/bccb407d740247cb6de744a3a28350c7bf870e09))

### [1.3.2](https://www.github.com/google/slo-generator/compare/v1.3.1...v1.3.2) (2020-10-23)


### Bug Fixes

* Datadog backend for direct SLI calculations ([#93](https://www.github.com/google/slo-generator/issues/93)) ([00fca80](https://www.github.com/google/slo-generator/commit/00fca80adb958e5200beca096b964e88d83c8d44))

### [1.3.1](https://www.github.com/google/slo-generator/compare/v1.3.0...v1.3.1) (2020-10-23)


### Bug Fixes

* Datadog count ([#88](https://www.github.com/google/slo-generator/issues/88)) ([65b9312](https://www.github.com/google/slo-generator/commit/65b9312fbd6faf3b35c8d98360d1d792c81a2df9))
* Dynatrace fixes ([#89](https://www.github.com/google/slo-generator/issues/89)) ([ca6c7b2](https://www.github.com/google/slo-generator/commit/ca6c7b2e44267fd74280b7ce428121c2d409c4dc))


### Documentation

* Add better custom samples ([#90](https://www.github.com/google/slo-generator/issues/90)) ([c0fcfe5](https://www.github.com/google/slo-generator/commit/c0fcfe50f9c8f0407b6b44e82e15e288401e92d3))
* fix metrics blob in exporters docs ([#91](https://www.github.com/google/slo-generator/issues/91)) ([f75663d](https://www.github.com/google/slo-generator/commit/f75663db3fe5d9f6c8736b58e4e423f8cdb9fd35))

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
