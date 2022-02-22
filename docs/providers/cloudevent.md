# Cloudevent

## Exporter

The Cloudevent exporter will make a POST request to a CloudEvent receiver 
service. 

This allows to send SLO Reports to another service that can process them, or 
export them to other destinations, such as an export-only slo-generator service.

**Config example:**

```yaml
exporters:
  cloudevent:
    service_url: <SERVICE_URL>
    # auth:
    #   token: <TOKEN_ID> # a token for the service
    # auth:
    #   google_service_account_auth: true # enable Google service account authentication
```

Optional fields:
* `auth` section allows to specify authentication tokens if needed.
Tokens are added as a header
  * `token` is used to pass an authentication token in the request headers.
  * `google_service_account_auth: true` is used to enable Google service account 
  authentication. Use this if the target service is hosted on GCP (Cloud Run, 
  Cloud Functions, Google Kubernetes Engine ...).
