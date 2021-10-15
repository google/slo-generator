# How to Contribute

We'd love to accept your patches and contributions to this project. There are
just a few small guidelines you need to follow.

## Contributor License Agreement

Contributions to this project must be accompanied by a Contributor License
Agreement. You (or your employer) retain the copyright to your contribution;
this simply gives us permission to use and redistribute your contributions as
part of the project. Head over to <https://cla.developers.google.com/> to see
your current agreements on file or to sign a new one.

You generally only need to submit a CLA once, so if you've already submitted one
(even if it was for a different project), you probably don't need to do it
again.

## Code reviews

All submissions, including submissions by project members, require review. We
use GitHub pull requests for this purpose. Consult
[GitHub Help](https://help.github.com/articles/about-pull-requests/) for more
information on using pull requests.

## Community Guidelines

This project follows [Google's Open Source Community
Guidelines](https://opensource.google/conduct/).

## Contributing guidelines

### Development environment

To prepare for development, you need to fork this repository and work on your
own branch so that you can later submit your changes as a GitHub Pull Request.

Once you have forked the repo on GitHub, clone it locally and install the `slo-generator` in a Python virtual environment:
```
git clone github.com/google/slo-generator
cd slo-generator
python3 -m venv venv/
source venv/bin/activate
```

Install `slo-generator` locally in development mode, so that you can start making changes to it:
```
make develop
```

#### Protobuf

The exporter `prometheus_remote_write` uses Protocol Buffers, the `_pb2.py` stubs are already generated, but you can update or re-generate the files via the Makefile under [slo_generator/exporters/gen](slo_generator/exporters/gen) directory.
```
cd slo_generator/exporters/gen
make generate # dependencies will be automatically downloaded
```

Protobuf files (.proto) are copies of original files in [Prometheus](https://github.com/prometheus/prometheus) and [gogo/protobuf](https://github.com/gogo/protobuf) repositories.

### Testing environment
Unittests are located in the `tests/unit` folder.

To run all the tests, run `make` in the base directory.

You can also select which test to run, and do other things:
```
make unittests     # run unittests only
make flake8 pylint # run linting tests only
make docker_test   # build Docker image and run tests within Docker container
make docker_build  # build Docker image only
make info          # see current slo-generator version
```

### Adding support for a new backend or exporter

The `slo-generator` tool is designed to be modular as it moves forward.
Users, customers and Google folks should be able to easily add the metrics
backend or the exporter of their choosing.

**New backend**

To add a new backend, one must:

* Add a new file `slo-generator/backends/<backend>.py`

* Write a new Python class called `<Name>Backend` (CamlCase)

* Test it with a sample config

* Add some unit tests

* Make sure all tests pass

* Submit a PR

***Example with a fake Cat backend:***

* Add a new backend file:

  ```sh
  touch slo-generator/backends/cat.py
  ```

* Fill the content of `cat.py`:

  ```python
  from provider import CatClient

  class CatBackend:
    def __init__(self, **kwargs):
      # instantiate your client here, or do nothing if your backend
      # doesn't need it.
      url = kwargs['url']
      self.client = CatClient(url)

    def _fmt_query(query, **options):
      # format your query string as you need to
      return query

    def query(self, *args, **kwargs):
      # add code to query your backend here.
      return self.client.query(*args, **kwargs)

    @staticmethod
    def count(timeseries):
      # add code to count the number of events in the timeseries returned
      return 500

    def distribution_cut(self, timestamp, window, slo_config):
      # this should return a tuple `(good_event_count, bad_event_count)`
      valid_event_query = slo_config['measurement']['query_valid']
      valid_timeseries = self.query(valid_event_query, timestamp, window)
      # ...
      return (good_count, bad_count)

    def good_bad_ratio(self, timestamp, window, slo_config):
      # this should return a tuple `(good_event_count, bad_event_count)`
      good_event_query = kwargs['measurement']['query_good']
      bad_event_query = kwargs['measurement']['query_bad']
      good_timeseries = self.query(good_event_query, timestamp, window)
      bad_timeseries = self.query(bad_event_query, timestamp, window)
      good_count = Datadog.count(good_timeseries)
      bad_count = Datadog.count(bad_timeseries)
      return (good_count, bad_count)

    def query_sli(self, timestamp, window, slo_config):
      # this should return a float `SLI value`.
      my_sli_value = self.compute_random_stuff()
      return my_sli_value
  ```
* Write a sample SLO configs (`slo_cat_test_slo_ratio.yaml`):

  ```yaml
  service_name: cat
  feature_name: test
  slo_name: slo
  slo_description: Test Cat SLO
  backend:
    class: Cat
    method: good_bad_ratio # change to test another method
    url: cat.mycompany.com
    measurement:
      query_good: avg:system.disk.free{*}.rollup(avg, {window})
      query_valid: avg:system.disk.used{*}.rollup(avg, {window})
  ```

* Run a live test with the SLO generator:
  ```sh
  slo-generator -f slo_cat_test_slo_ratio.yaml -b samples/error_budget_target.yaml
  ```

* Create a directory `samples/<backend>` for your backend samples.

* Add some YAML samples to show how to write SLO configs for your backend. Samples should be named `slo_<service_name>_<feature_name>_<method>.yaml`.

* Add a unit test: in the `tests/unit/test_compute.py`, simply add a method called `test_compute_<backend>`. Take the other backends an example when
writing the test.

* Add documentation for your backend / exporter in a new file named `docs/providers/cat.md`.

* Make sure all tests pass

* Submit a PR

The steps above are similar for adding a new exporter, but the exporter code will go to the `exporters/` directory and the unit test will be named `test_export_<exporter>`.
