# Deploy SLO Generator in Cloud Functions [DEPRECATED]

`slo-generator` is frequently used as part of an SLO Reporting Pipeline made of:

* A **Cloud Scheduler** triggering an event every X minutes.
* A **PubSub topic**, triggered by the Cloud Scheduler event.
* A **Cloud Function**, triggered by the PubSub topic, running `slo-generator`.
* A **PubSub topic** to stream computation results.


Other components can be added to make results available to other destinations:
* A **Cloud Function** to export SLO reports (e.g: to BigQuery and Cloud Monitoring), running `slo-generator`.
* A **Cloud Monitoring Policy** to alert on high budget Burn Rates.

Below is a diagram of what this pipeline looks like:

![Architecture](https://raw.githubusercontent.com/terraform-google-modules/terraform-google-slo/master/diagram.png)

**Benefits:**

* **Frequent SLO / Error Budget / Burn rate reporting** (max 1 every minute) with Cloud Scheduler.

* **Historical analytics** by analyzing SLO data in Bigquery.

* **Real-time alerting** by setting up Cloud Monitoring alerts based on
wanted SLOs.

* **Real-time, daily, monthly, yearly dashboards** by streaming BigQuery SLO reports to DataStudio (see [here](datastudio_slo_report.md)) and building dashboards.

An example of pipeline automation with Terraform can be found in the corresponding  [Terraform module](https://github.com/terraform-google-modules/terraform-google-slo/tree/master/examples/slo-generator/simple_example).
