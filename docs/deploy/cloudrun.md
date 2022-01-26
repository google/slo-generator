# Deploy SLO Generator as a Cloud Run service

`slo-generator` can also be deployed as a Cloud Run service by following the 
instructions below.

## Setup a Cloud Storage bucket

Create the GCS bucket that will hold our SLO configurations:

```
gsutil mb -p ${PROJECT_ID} gs://${BUCKET_NAME}
```

Upload the slo-generator configuration to the GCS bucket:

```
gsutil cp config.yaml gs://${BUCKET_NAME}/
```

See sample [config.yaml](../../samples/config.yaml)

## Deploy the CloudRun service

```
gcloud run deploy slo-generator \
   --image gcr.io/slo-generator-ci-a2b4/slo-generator:latest \
   --region=europe-west1 \
   --project=${PROJECT_ID} \
   --set-env-vars CONFIG_PATH=gs://${BUCKET_NAME}/config.yaml \
   --platform managed \
   --command="slo-generator" \
   --args=api \
   --args=--signature-type=http \
   --min-instances 1 \
   --allow-unauthenticated
```

Once the deployment is finished, get the service URL from the log output.

## [Optional] Test an SLO
```
curl -X POST -H "Content-Type: text/x-yaml" --data-binary @slo.yaml ${SERVICE_URL} # yaml
curl -X POST -H "Content-Type: application/json" -d @${SLO_PATH} ${SERVICE_URL}    # json
```

See sample [slo.yaml](../../samples/cloud_monitoring/slo_gae_app_availability.yaml)

## Schedule SLO reports every minute

Upload your SLO config to the GCS bucket:
```
gsutil cp slo.yaml gs://${BUCKET_NAME}/
```

Create a Cloud Scheduler job that will hit the service with the SLO config URL:
```
gcloud scheduler jobs create http slo --schedule=”* * * * */1” \
   --uri=${SERVICE_URL} \
   --message-body=”gs://${BUCKET_NAME}/slo.yaml”
   --project=${PROJECT_ID}
```

## Deploy an exporter-only Cloud Run instance

### Description


The `slo-generator` API can be deployed as an exporter-only instance.

The exporter-only Cloud Run instance is used in certain scenarios where it's 
worth decoupling the export functionality of the SLO generator to another 
service. For instance, a certain organisation of SRE can be to let the 
application / product teams have their own service.

Like the slo-generator standard API, it can have two modes of functioning:

* `--signature-type=http`: Rest API mode, where it can be accessed through HTTP. 
The `slo-generator` has an `HTTPExporter` that you can use to send SLO reports 
to the instance running in this mode.

```
gcloud run deploy slo-generator-export \
   --image gcr.io/slo-generator-ci-a2b4/slo-generator:latest \
   --region=europe-west1 \
   --project=${PROJECT_ID} \
   --set-env-vars CONFIG_PATH=gs://${BUCKET_NAME}/config.yaml \
   --platform managed \
   --command="slo-generator" \
   --args=api \
   --args=--signature-type=http \
   --min-instances 1 \
   --allow-unauthenticated
```

* `--signature-type=cloudevent`: CloudEvent mode, can receive CloudEvent 
messages such as those coming from Pub/Sub etc.

```
gcloud run deploy slo-generator-export \
   --image gcr.io/slo-generator-ci-a2b4/slo-generator:latest \
   --region=europe-west1 \
   --project=${PROJECT_ID} \
   --set-env-vars CONFIG_PATH=gs://${BUCKET_NAME}/config.yaml \
   --platform managed \
   --command="slo-generator" \
   --args=api \
   --args=--signature-type=cloudevent \
   --min-instances 1 \
   --allow-unauthenticated
```

It is recommended to run it in this mode if you already have a Pub/Sub exporter
set up on the `slo-generator` side.
