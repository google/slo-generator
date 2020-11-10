# Troubleshooting

## `StackdriverExporter`: Labels limit (10) reached.
```
The new labels would cause the metric custom.googleapis.com/slo_target to have over 10 labels.: timeSeries[0]"
    debug_error_string = "{"created":"@1605001943.853828000","description":"Error received from peer ipv6:[2a00:1450:4007:817::200a]:443","file":"src/core/lib/surface/call.cc","file_line":1062,"grpc_message":"One or more TimeSeries could not be written: The new labels would cause the metric custom.googleapis.com/slo_target to have over 10 labels.: timeSeries[0]","grpc_status":3}"
```

### Solutions

**Solution 1:**
Delete the metric descriptor, and re-run the SLO Generator. 
You can do so using `gmon` (`pip install gmon`) and run: 
`gmon metrics delete custom.googleapis.com/slo_target`.
**Warning:** this will destroy all historical metric data (6 weeks). 
If you are using the metric in Cloud Monitoring dashboards, be wary.

**Solution 2:**
Limit the number of user labels sent with the metric.
The default metrics are exported with 7 labels maximum, which means you have up 
to 3 additional user labels (`metadata` labels in SLO config, or 
`additional_labels` in the `metrics` config).
