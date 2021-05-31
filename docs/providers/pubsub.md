# Pub/Sub

## Exporter

The `pubsub` exporter will export SLO reports to a Pub/Sub topic, in JSON format.

```yaml
exporters:
  pubsub:
    project_id: "${PUBSUB_PROJECT_ID}"
    topic_name: "${PUBSUB_TOPIC_NAME}"
```

This allows teams to consume SLO reports in real-time, and take appropriate
actions when they see a need.

**&rightarrow; [Full SLO config](../../samples/cloud_monitoring/slo_pubsub_subscription_throughput.yaml)**
