# Elasticsearch

## Backend

Using the `opensearch` backend class, you can query any metrics available in Opensearch to create an SLO.

```yaml
backends:
  opensearch:
    url: ${OPENSEARCH_URL}
```

Note that `url` can be either a single string (when connecting to a single node) or a list of strings (when connecting to multiple nodes):

```yaml
backends:
  opensearch:
    url: https://localhost:9200
```

```yaml
backends:
  opensearch:
    url:
      - https://localhost:9200
      - https://localhost:9201
```

The following method is available to compute SLOs with the `opensearch` backend:

* `good_bad_ratio` method is used to compute the ratio between two metrics:

* **Good events**, i.e events we consider as 'good' from the user perspective.
* **Bad or valid events**, i.e events we consider either as 'bad' from the user perspective, or all events we consider as 'valid' for the computation of the SLO.

This method is often used for availability SLOs, but can be used for other purposes as well (see examples).

**SLO example:**

```yaml
  backend: opensearch
  method: good_bad_ratio
  service_level_indicator:
    index: my-index
    date_field: '@timestamp'
    query_good:
      must:
        range:
          api-response-time:
            lt: 350
    query_bad:
      must:
        range:
          api-response-time:
            gte: 350
```

Additional info:

* `date_field`: Has to be a valid Opensearch `timestamp` type

**&rightarrow; [Full SLO config](../../samples/opensearch/slo_opensearch_latency_sli.yaml)**

You can also use the `filter_bad` field which identifies bad events instead of the `filter_valid` field which identifies all valid events.

The Lucene query entered in either the `query_good`, `query_bad` or `query_valid` fields will be combined (using the `bool` operator) into a larger query that filters results on the `window` specified in your Error Budget Policy steps.

The full `Opensearh` query body for the `query_bad` above will therefore look like:

```json
{
  "query": {
    "bool": {
      "must": {
        "range": {
          "api-response-time": {
            "gte": 350
          }
        }
      },
      "filter": {
        "range": {
          "@timestamp": {
            "gte": "now-3600s/s",
            "lt": "now/s"
          }
        }
      }
    }
  },
  "track_total_hits": true
}
```

### Examples

Complete SLO samples using the `opensearch` backend are available in [samples/elasticsearch](../../samples/opensearch). Check them out!
