# Splunk

## Backend

Using the `splunk` backend class, you can query any metrics available in Splunk Enterprise to create an SLO.

```yaml
backends:
  splunk:
    host: ${SPLUNK_HOST}
    port: ${SPLUNK_PORT}
    user: ${SPLUNK_USER}
    password: ${SPLUNK_PWD}
    token: $[SPLUNK_BEARER_TOKEN}
```
You need either a user/password pair or a token, not both.

The following methods are available to compute SLOs with the `splunk` backend:

* `search_query_good` & `search_query_bad`/`search_query_valid` for computing good / bad metrics ratios.
* `search_query` for computing SLIs directly with Splunk.

The `good_bad_ratio` method is used to compute the ratio between two metrics:

* **Good events**, i.e events we consider as 'good' from the user perspective.
* **Bad or valid events**, i.e events we consider either as 'bad' from the user perspective, or all events we consider as 'valid' for the computation of the SLO. Note : if both are specified, 'bad' configuration takes precedence over 'valid'.

This method is often used for availability SLOs, but can be used for other purposes as well (see examples).

**Config example:**

```yaml
backend: splunk
method:  good_bad_ratio
service_level_indicator:
    search_query_good: search index=access_logs host=web* status=200 | stats count(status) as good | table good
    search_query_bad: search index=access_logs host=web* status!=200 status!=403 | stats count(status) as bad | table bad
```

**&rightarrow; [Full SLO config](../../samples/splunk/slo_splunk_app_availability_ratio.yaml)**

### Query SLI

The `query_sli` method is used to directly query the needed SLI with Splunk using the search language arithmetics ciapabilities.

This method makes it more flexible to input any `splunk` SLI computation and eventually reduces the number of queries made to Splunk.

```yaml
backend: splunk
method: query_sli
service_level_indicator:
    search_query: search index=access_logs host=web* status!=200 status!=403 | stats count(status="200") as good count(status!="403") as valid | eval sli=round(good/valid,3)
```

**&rightarrow; [Full SLO config](../../samples/splunk/slo_splunk_app_availability_query_sli.yaml)**

### Examples

Complete SLO samples using `splunk` are available in [samples/splunk](../../samples/splunk). Check them out!

## Exporter

Not implemented as of yet.

## Splunk search performance

Note that running oneshot queries on splunk may not always be fast. depending on the resources of your splunk infrastructure, volume of data and SLO window, it can take up to minutes. It can even be so long that the "oneshot" method of the SDK we're using times out. In this case there are several alternatives :

1. Switch the code to the "normal" search mode instead, which asynchronously polls the splunk search head for results instead of waiting for the REST response.
2. Make use of pre-cooked "saved searches" and just trigger the jobs on demand. This would require the bakend code to be reworked to switch from oneshot searches to saved search
3. Alternatively it's also possible to have isaved searches already executed by splunk on a schedule and just query their results. Same here, this would require a rework/update of the code
